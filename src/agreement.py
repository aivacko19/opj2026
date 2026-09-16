import argparse, collections, itertools, io, re
import common as C

LABELS = ("OBJ", "SUBJ")
P8 = re.compile(r"\b(naravno|dakle|uostalom|naime|zapravo|inače)\b", re.I)


def cohen(x, y):
    n = len(x)
    po = sum(a == b for a, b in zip(x, y)) / n
    pe = sum((x.count(c) / n) * (y.count(c) / n) for c in LABELS)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


def fleiss(cols):
    n_rat, N = len(cols), len(cols[0])
    counts = [[sum(c[i] == lab for c in cols) for lab in LABELS] for i in range(N)]
    P = [(sum(x * x for x in row) - n_rat) / (n_rat * (n_rat - 1)) for row in counts]
    pj = [sum(row[j] for row in counts) / (N * n_rat) for j in range(len(LABELS))]
    Pe = sum(p * p for p in pj)
    Pbar = sum(P) / N
    return (Pbar - Pe) / (1 - Pe) if Pe < 1 else 1.0


def krippendorff(cols):
    n_rat, N = len(cols), len(cols[0])
    o = collections.Counter()
    for i in range(N):
        vals = [c[i] for c in cols]
        for a, b in itertools.permutations(vals, 2):
            o[(a, b)] += 1 / (n_rat - 1)
    nc = {c: sum(o[(c, k)] for k in LABELS) for c in LABELS}
    n = sum(nc.values())
    Do = sum(o[(c, k)] for c in LABELS for k in LABELS if c != k)
    De = sum(nc[c] * nc[k] for c in LABELS for k in LABELS if c != k) / (n - 1)
    return 1 - Do / De if De else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--corpus", default="corpus.tsv")
    ap.add_argument("--out", default="neslaganja.tsv")
    a = ap.parse_args()

    meta = {r["sentence_id"]: r for r in C.read_tsv(a.corpus)}
    anns = {}
    for f in a.files:
        rows = C.read_tsv(f)
        name = rows[0].get("annotator") or f
        bad = [r["sentence_id"] for r in rows if r["label"] not in LABELS]
        if bad:
            print(f"  UPOZORENJE {name}: {len(bad)} redova bez ispravne oznake, "
                  f"npr. {bad[:3]}")
        anns[name] = {r["sentence_id"]: r for r in rows if r["label"] in LABELS}
        print(f"  {name}: {len(anns[name])} označenih rečenica")

    names = sorted(anns)
    ids = set.intersection(*(set(d) for d in anns.values()))
    allids = set.union(*(set(d) for d in anns.values()))
    if len(ids) != len(allids):
        print(f"\n  UPOZORENJE: {len(allids)-len(ids)} rečenica nema oznaku "
              f"od svih anotatora; računa se na preseku od {len(ids)}")
    ids = sorted(ids)
    cols = [[anns[n][i]["label"] for i in ids] for n in names]

    print(f"\n{'='*64}\nSAGLASNOST — {len(ids)} rečenica, {len(names)} anotatora\n{'='*64}")
    ks = []
    for (i, n1), (j, n2) in itertools.combinations(list(enumerate(names)), 2):
        po, k = cohen(cols[i], cols[j])
        ks.append(k)
        print(f"  {n1} — {n2}:  slaganje {po:5.1%}   Koenova kapa {k:.3f}")
    print(f"\n  prosek parnih kapa:   {sum(ks)/len(ks):.3f}")
    print(f"  Fajsova kapa:         {fleiss(cols):.3f}")
    print(f"  Kripendorfova alfa:   {krippendorff(cols):.3f}")
    print("    (izvorni rad: 0.51 pre razgovora, 0.83 posle)")

    print("\n  raspodela oznaka po anotatoru — razlika u pragu se vidi ovde")
    for n, col in zip(names, cols):
        c = collections.Counter(col)
        print(f"    {n:22s} SUBJ {c['SUBJ']:4d} ({c['SUBJ']/len(col):5.1%})   "
              f"OBJ {c['OBJ']:4d}")

    print("\n  matrice konfuzije (red = prvi anotator, kolona = drugi)")
    for (i, n1), (j, n2) in itertools.combinations(list(enumerate(names)), 2):
        t = collections.Counter(zip(cols[i], cols[j]))
        print(f"    {n1} / {n2}      OBJ   SUBJ")
        for lab in LABELS:
            print(f"      {lab:6s} {t[(lab,'OBJ')]:6d} {t[(lab,'SUBJ')]:6d}")

    def subset_kappa(pred, label):
        sel = [n for n, i in enumerate(ids) if i in meta and pred(meta[i])]
        if len(sel) < 20:
            print(f"    {label:28s} {len(sel):4d} rečenica — premalo za meru")
            return
        sub = [[c[n] for n in sel] for c in cols]
        kk = [cohen(sub[i], sub[j])[1]
              for i, j in itertools.combinations(range(len(names)), 2)]
        print(f"    {label:28s} {len(sel):4d} rečenica   prosek kapa {sum(kk)/len(kk):.3f}")

    print("\n  saglasnost po podskupovima")
    subset_kappa(lambda r: True, "ceo kalibracioni skup")
    subset_kappa(lambda r: r.get("in_quote") == "Y", "unutar navoda (P6, P13)")
    subset_kappa(lambda r: r["text"].rstrip().endswith("?"), "pitanja (P9)")
    subset_kappa(lambda r: bool(P8.search(r["text"])), "diskursni konektori (P8)")
    for g in ("kolumna", "vest"):
        subset_kappa(lambda r, g=g: r["genre"] == g, f"žanr = {g}")
    for s in sorted({r["source"] for r in meta.values()}):
        subset_kappa(lambda r, s=s: r["source"] == s, f"izvor = {s}")

    dis = [i for n, i in enumerate(ids) if len({c[n] for c in cols}) > 1]
    out = []
    for i in dis:
        r = meta.get(i, {})
        row = {"sentence_id": i, "article_id": r.get("article_id", ""),
               "genre": r.get("genre", ""), "topic": r.get("topic", ""),
               "source": r.get("source", ""), "in_quote": r.get("in_quote", ""),
               "text": r.get("text_marked") or r.get("text", "")}
        for n in names:
            row[f"label_{n.split()[0]}"] = anns[n][i]["label"]
            row[f"nap_{n.split()[0]}"] = anns[n][i].get("napomena", "")
        row["dogovoreno"] = ""
        row["pravilo"] = ""
        out.append(row)
    if out:
        C.write_tsv(a.out, out)
    print(f"\n  neslaganja: {len(dis)}/{len(ids)} ({len(dis)/len(ids):.1%}) -> {a.out}")

    flagged = [i for i in ids if any(anns[n][i].get("nedoumica") == "Y" for n in names)]
    print(f"  označeno kao nedoumica: {len(flagged)}")
    notes = [anns[n][i].get("napomena", "").strip()
             for i in ids for n in names if anns[n][i].get("napomena", "").strip()]
    if notes:
        print(f"\n  napomene ({len(notes)}) — grupisati po RAZLOGU, ne po oznaci:")
        for t in notes[:12]:
            print(f"    {t[:90]}")

    print("\nSledeći korak: proći kroz neslaganja.tsv zajedno, upisati dogovorenu\n"
          "oznaku i pravilo koje je odlučuje, pa ponovo pokrenuti ovaj skript nad\n"
          "usaglašenim oznakama za drugu vrednost saglasnosti.")


if __name__ == "__main__":
    main()
