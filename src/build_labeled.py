import argparse, collections, pathlib, glob
import common as C

LABELS = ("OBJ", "SUBJ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus.tsv")
    ap.add_argument("--gold", default="gold_calibration.tsv")
    ap.add_argument("--main", nargs="+", required=True)
    ap.add_argument("--tasks", default="zadatak-*-ids.txt")
    ap.add_argument("--out", default="corpus_labeled.tsv")
    a = ap.parse_args()

    rows = C.read_tsv(a.corpus)
    by_id = {r["sentence_id"]: r for r in rows}
    print(f"korpus: {len(rows)} rečenica\n")

    label, source = {}, {}
    gold = C.read_tsv(a.gold)
    for r in gold:
        label[r["sentence_id"]] = r["label"]
        source[r["sentence_id"]] = r.get("izvor_oznake", "kalibracija")
    print(f"kalibracija: {len(gold)} rečenica "
          f"({sum(1 for r in gold if r.get('izvor_oznake')=='saglasnost')} saglasnost, "
          f"{sum(1 for r in gold if r.get('izvor_oznake')=='usaglaseno')} usaglašeno)")


    assigned = {}
    for f in glob.glob(a.tasks):
        who = pathlib.Path(f).stem.replace("zadatak-", "").replace("-ids", "")
        assigned[who] = set(pathlib.Path(f).read_text(encoding="utf-8").split())

    dupes, bad = collections.Counter(), []
    print()
    for f in a.main:
        rr = C.read_tsv(f)
        who = rr[0].get("annotator") or pathlib.Path(f).stem
        n_ok = 0
        for r in rr:
            sid, lab = r["sentence_id"], r["label"].strip().upper()
            if lab not in LABELS:
                bad.append((who, sid, r["label"])); continue
            if sid in label:
                dupes[sid] += 1
                if source[sid] in ("saglasnost", "usaglaseno"):
                    continue                      
            label[sid] = lab; source[sid] = who; n_ok += 1

        key = next((k for k in assigned if k.split()[0] in who or who.split()[0] in k),
                   None)
        extra = short = "?"
        if key:
            got = {r["sentence_id"] for r in rr}
            extra = len(got - assigned[key])
            short = len(assigned[key] - got)
        print(f"  {who}: {len(rr)} redova, {n_ok} upisano"
              + (f", višak {extra}, manjak {short}" if key else
                 "  (nema zadatak-*-ids.txt za proveru)"))

    if bad:
        print(f"\n  NEISPRAVNE OZNAKE: {len(bad)}")
        for w, s, l in bad[:8]:
            print(f"    {w}  {s}  {l!r}")
    if dupes:
        print(f"\n  rečenica sa više od jedne oznake: {len(dupes)} "
              f"(kalibracija ima prednost)")
        for s, n in list(dupes.items())[:5]:
            print(f"    {s}  x{n+1}")

    out, missing = [], []
    for r in rows:
        sid = r["sentence_id"]
        if sid not in label:
            missing.append(sid); continue
        out.append(dict(r, label=label[sid], izvor_oznake=source[sid]))

    print(f"\n{len(out)}/{len(rows)} rečenica ima oznaku")
    if missing:
        print(f"  BEZ OZNAKE: {len(missing)}  npr. {missing[:5]}")

    cols = list(rows[0].keys()) + ["label", "izvor_oznake"]
    C.write_tsv(a.out, out, cols)

    lab = collections.Counter(r["label"] for r in out)
    print(f"\n  SUBJ {lab['SUBJ']} ({lab['SUBJ']/len(out):.1%})   "
          f"OBJ {lab['OBJ']} ({lab['OBJ']/len(out):.1%})")

    print("\n  udeo SUBJ po izvoru i žanru:")
    cell = collections.defaultdict(lambda: [0, 0])
    for r in out:
        c = cell[(r["source"], r["genre"])]
        c[0] += r["label"] == "SUBJ"; c[1] += 1
    srcs = sorted({r["source"] for r in out})
    print("             " + "".join(f"{g:>12s}" for g in ("kolumna", "vest")))
    for s in srcs:
        line = f"    {s:9s}"
        for g in ("kolumna", "vest"):
            n_s, n = cell[(s, g)]
            line += f"{(f'{n_s/n:.0%} ({n})' if n else '—'):>12s}"
        print(line)

    print("\n  udeo SUBJ po temi:")
    for t in sorted({r["topic"] for r in out}):
        sub = [r for r in out if r["topic"] == t]
        n_s = sum(1 for r in sub if r["label"] == "SUBJ")
        print(f"    {t:12s} {n_s/len(sub):5.1%}  ({len(sub)})")

    print("\n  udeo SUBJ po poreklu oznake:")
    for src in sorted({r["izvor_oznake"] for r in out}):
        sub = [r for r in out if r["izvor_oznake"] == src]
        n_s = sum(1 for r in sub if r["label"] == "SUBJ")
        print(f"    {src:14s} {n_s/len(sub):5.1%}  ({len(sub)})")

    q = [r for r in out if r.get("in_quote") == "Y"]
    if q:
        n_s = sum(1 for r in q if r["label"] == "SUBJ")
        print(f"\n  unutar navoda: {len(q)} rečenica, SUBJ {n_s/len(q):.1%} "
              f"(očekuje se nisko — P6)")

    print(f"\n-> {a.out}")
    print("\nSledeće: python3 ../model/run_baselines.py --data ../corpus_labeled.tsv")


if __name__ == "__main__":
    main()
