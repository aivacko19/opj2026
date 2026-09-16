import random, argparse, collections, pathlib, io
import common as C

SEED = 20260902


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus.tsv")
    ap.add_argument("--exclude", nargs="*", default=["discovery_ids.txt"])
    ap.add_argument("--n", type=int, default=350)
    ap.add_argument("--out", default="calibration_ids.txt")
    a = ap.parse_args()

    rows = C.read_tsv(a.corpus)
    seen = set()
    for f in a.exclude:
        p = pathlib.Path(f)
        if p.exists():
            ids = set(p.read_text(encoding="utf-8").split())
            seen |= ids
            print(f"  isključeno iz {f}: {len(ids)}")
        else:
            print(f"  UPOZORENJE: {f} ne postoji")

    pool = [r for r in rows if r["sentence_id"] not in seen]
    print(f"\n{len(rows)} rečenica, {len(seen)} već viđenih, "
          f"{len(pool)} na raspolaganju")

    cells = collections.Counter((r["source"], r["genre"]) for r in pool)
    tot = sum(cells.values())
    raw = {k: v / tot * a.n for k, v in cells.items()}
    quota = {k: int(v) for k, v in raw.items()}
    for k, _ in sorted(raw.items(), key=lambda kv: -(kv[1] - int(kv[1])))[
            :a.n - sum(quota.values())]:
        quota[k] += 1

    rng = random.Random(SEED)
    by_cell = collections.defaultdict(list)
    for r in pool:
        by_cell[(r["source"], r["genre"])].append(r)

    picked, used_art = [], set()
    for cell, need in quota.items():
        cand = by_cell[cell][:]
        rng.shuffle(cand)
        got = 0
        for r in cand:
            if got >= need:
                break
            art = (r["source"], r["article_id"])
            if art in used_art:            
                continue
            picked.append(r); used_art.add(art); got += 1
        if got < need:
            print(f"  NEDOVOLJNO {cell}: {got}/{need} "
                  f"(premalo različitih članaka)")

    rng.shuffle(picked)                    
    io.open(a.out, "w", encoding="utf-8").write(
        "\n".join(r["sentence_id"] for r in picked) + "\n")

    print(f"\n{len(picked)} rečenica iz {len(used_art)} članaka -> {a.out}")
    print(f"seed {SEED}\n")
    for f in ("source", "genre", "topic"):
        print(f"  {f}:")
        c = collections.Counter(r[f] for r in picked)
        cp = collections.Counter(r[f] for r in pool)
        for k, v in c.most_common():
            print(f"    {v:4d} ({v/len(picked):5.1%})   korpus {cp[k]/len(pool):5.1%}   {k}")
    nq = sum(1 for r in picked if r["in_quote"] == "Y")
    qm = sum(1 for r in picked if r["text"].rstrip().endswith("?"))
    print(f"\n  unutar navoda: {nq} ({nq/len(picked):.1%})")
    print(f"  pitanja: {qm} ({qm/len(picked):.1%})")
    print("\nSva tri člana učitavaju corpus.tsv, context.json i ovaj fajl "
          "u polje za izbor u alatu za anotaciju.")


if __name__ == "__main__":
    main()
