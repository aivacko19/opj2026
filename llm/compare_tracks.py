"""
Pokretanje:
    python3 compare_tracks.py --gold ../src/corpus_labeled.tsv \\
        --baseline ../model/oof_predictions.tsv \\
        --llm ../llm/llm_preds/gemini-sr-few.tsv ../llm/llm_preds/chatgpt-en-zero.tsv
"""

import csv, io, re, argparse, collections, itertools, pathlib, sys
sys.path.insert(0, "../src")
import common as C

LAB = ("OBJ", "SUBJ")
TSV = dict(delimiter="\t", quotechar=None, quoting=csv.QUOTE_NONE)
P8 = re.compile(r"\b(naravno|dakle|uostalom|naime|zapravo|inače)\b", re.I)


def read(p):
    return list(csv.DictReader(io.open(p, encoding="utf-8", newline=""), **TSV))


def f1(gold, pred, pos):
    tp = sum(1 for g, p in zip(gold, pred) if g == p == pos)
    fp = sum(1 for g, p in zip(gold, pred) if p == pos and g != pos)
    fn = sum(1 for g, p in zip(gold, pred) if g == pos and p != pos)
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return 2 * pr * rc / (pr + rc) if pr + rc else 0.0


def macro(gold, pred):
    return sum(f1(gold, pred, l) for l in LAB) / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="../src/corpus_labeled.tsv")
    ap.add_argument("--baseline", default="../model/oof_predictions.tsv")
    ap.add_argument("--llm", nargs="+", required=True)
    ap.add_argument("--out", default="poredjenje.tsv")
    a = ap.parse_args()

    gold = {r["sentence_id"]: r for r in C.read_tsv(a.gold) if r.get("label") in LAB}
    sysp = {}

    b = read(a.baseline)
    sysp["osnovni model"] = {r["sentence_id"]: r["pred"] for r in b
                             if r.get("pred") in LAB}
    for f in a.llm:
        rows = read(f)
        sysp[pathlib.Path(f).stem] = {r["sentence_id"]: r["pred"] for r in rows
                                      if r["pred"] in LAB}

    names = list(sysp)
    ids = sorted(set(gold) & set.intersection(*(set(d) for d in sysp.values())))
    print(f"{len(ids)} rečenica sa zlatnom oznakom i predikcijom svih "
          f"{len(names)} sistema\n")
    g = [gold[i]["label"] for i in ids]


    print("=" * 86)
    print(f"{'sistem':26s} {'makro F1':>9s} {'F1 OBJ':>8s} {'F1 SUBJ':>9s} "
          f"{'tačnost':>9s} {'% SUBJ':>8s}")
    print("=" * 86)
    for n in names:
        p = [sysp[n][i] for i in ids]
        acc = sum(1 for x, y in zip(g, p) if x == y) / len(g)
        print(f"{n:26s} {macro(g,p):9.3f} {f1(g,p,'OBJ'):8.3f} "
              f"{f1(g,p,'SUBJ'):9.3f} {acc:9.3f} "
              f"{sum(1 for x in p if x=='SUBJ')/len(p):8.1%}")
    print(f"{'zlatne oznake':26s} {'':9s} {'':8s} {'':9s} {'':9s} "
          f"{sum(1 for x in g if x=='SUBJ')/len(g):8.1%}")

    print("\n" + "=" * 86)
    print("MAKRO F1 PO PODSKUPOVIMA   (u zagradi F1 za klasu SUBJ)")
    print("=" * 86)
    print(f"{'podskup':26s} {'n':>5s}  " + "".join(f"{n[:17]:>19s}" for n in names))
    print("-" * 86)

    rows_out = []

    def line(fn, label):
        idx = [k for k, i in enumerate(ids) if fn(gold[i])]
        if len(idx) < 30:
            print(f"{label:26s} {len(idx):5d}   premalo za meru"); return
        gg = [g[k] for k in idx]
        cells, rec = [], {"podskup": label, "n": len(idx)}
        for n in names:
            pp = [sysp[n][ids[k]] for k in idx]
            m, s = macro(gg, pp), f1(gg, pp, "SUBJ")
            cells.append(f"{m:.3f} ({s:.3f})".rjust(19))
            rec[n] = round(m, 4); rec[n + " SUBJ"] = round(s, 4)
        rows_out.append(rec)
        print(f"{label:26s} {len(idx):5d}  " + "".join(cells))

    line(lambda r: True, "ceo korpus")
    for gn in ("kolumna", "vest"):
        line(lambda r, gn=gn: r["genre"] == gn, f"žanr = {gn}")
    for t in sorted({r["topic"] for r in gold.values()}):
        line(lambda r, t=t: r["topic"] == t, f"tema = {t}")
    for s in sorted({r["source"] for r in gold.values()}):
        line(lambda r, s=s: r["source"] == s, f"izvor = {s}")
    line(lambda r: r.get("in_quote") == "Y", "unutar navoda (P6, P13)")
    line(lambda r: r["text"].rstrip().endswith("?"), "pitanja (P9)")
    line(lambda r: bool(P8.search(r["text"])), "konektori (P8)")
    line(lambda r: r.get("izvor_oznake") == "saglasnost", "anotatori se složili")
    line(lambda r: r.get("izvor_oznake") == "usaglaseno", "anotatori se nisu složili")

    if rows_out:
        C.write_tsv(a.out, rows_out)
        print(f"\n-> {a.out}")


    print("\n" + "=" * 86)
    print("SLAGANJE IZMEĐU SISTEMA")
    print("=" * 86)
    for n1, n2 in itertools.combinations(names, 2):
        same = sum(1 for i in ids if sysp[n1][i] == sysp[n2][i])
        print(f"  {n1:26s} — {n2:26s} {same/len(ids):6.1%}")

    print("\n" + "=" * 86)
    print("KO POGAĐA ŠTA (na rečenicama gde se sistemi razlikuju)")
    print("=" * 86)
    right = {n: {i for i in ids if sysp[n][i] == gold[i]["label"]} for n in names}
    allr = set.intersection(*right.values())
    alln = set(ids) - set.union(*right.values())
    print(f"  svi tačni:      {len(allr):5d} ({len(allr)/len(ids):5.1%})")
    print(f"  svi netačni:    {len(alln):5d} ({len(alln)/len(ids):5.1%})")
    for n in names:
        only = right[n] - set.union(*(right[m] for m in names if m != n))
        print(f"  jedino {n:22s} {len(only):5d} ({len(only)/len(ids):5.1%})")

    print("\n" + "=" * 86)
    print("TVRDO JEZGRO — rečenice koje nijedan sistem ne pogađa")
    print("=" * 86)
    hard = sorted(alln, key=lambda i: gold[i]["label"])
    by = collections.Counter((gold[i]["label"], gold[i]["genre"]) for i in hard)
    print("  po zlatnoj oznaci i žanru:", dict(by))
    nq = sum(1 for i in hard if gold[i].get("in_quote") == "Y")
    print(f"  unutar navoda: {nq} ({nq/max(1,len(hard)):.1%}, "
          f"u korpusu {sum(1 for i in ids if gold[i].get('in_quote')=='Y')/len(ids):.1%})")
    for lab in LAB:
        sel = [i for i in hard if gold[i]["label"] == lab][:6]
        print(f"\n  zlatno {lab}, svi predviđaju {LAB[1-LAB.index(lab)]}:")
        for i in sel:
            r = gold[i]
            print(f"    [{r['genre'][:3]}/{r['source'][:4]}] "
                  f"{(r.get('text_marked') or r['text'])[:80]}")


if __name__ == "__main__":
    main()
