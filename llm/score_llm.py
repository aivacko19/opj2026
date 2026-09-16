import csv, io, glob, argparse, collections, pathlib, itertools, sys
sys.path.insert(0, "../src")
import common as C

TSV = dict(delimiter="\t", quotechar=None, quoting=csv.QUOTE_NONE)
LAB = ("OBJ", "SUBJ")


def mcnemar(gold, pa, pb):
    """Da li su dve konfiguracije stvarno različite.

    Poređenje je upareno — iste rečenice, dva sistema — pa se gleda samo gde se
    sistemi razlikuju: koliko puta je A tačan a B nije (b01) i obrnuto (b10).
    Ako je razlika slučajna, ta dva broja treba da budu slična.

    Za mali broj neslaganja koristi se tačan binomni test, inače hi-kvadrat sa
    korekcijom neprekidnosti.
    """
    b01 = sum(1 for g, x, y in zip(gold, pa, pb) if x == g and y != g)
    b10 = sum(1 for g, x, y in zip(gold, pa, pb) if x != g and y == g)
    nd = b01 + b10
    if nd == 0:
        return b01, b10, 1.0
    if nd < 25:
        from math import comb
        k = min(b01, b10)
        p = 2 * sum(comb(nd, i) for i in range(k + 1)) / (2 ** nd)
        return b01, b10, min(1.0, p)
    chi = (abs(b01 - b10) - 1) ** 2 / nd
    try:
        from scipy.stats import chi2
        return b01, b10, float(chi2.sf(chi, 1))
    except ImportError:
        from math import erfc, sqrt
        return b01, b10, erfc(sqrt(chi / 2))     


def prf(gold, pred, positive):
    tp = sum(1 for g, p in zip(gold, pred) if g == p == positive)
    fp = sum(1 for g, p in zip(gold, pred) if p == positive and g != positive)
    fn = sum(1 for g, p in zip(gold, pred) if g == positive and p != positive)
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return pr, rc, f1


def score(gold, pred):
    acc = sum(1 for g, p in zip(gold, pred) if g == p) / len(gold)
    f = {l: prf(gold, pred, l) for l in LAB}
    macro = sum(f[l][2] for l in LAB) / 2
    return dict(n=len(gold), acc=acc, macro=macro,
                f_obj=f["OBJ"][2], f_subj=f["SUBJ"][2],
                p_subj=f["SUBJ"][0], r_subj=f["SUBJ"][1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="../src/corpus_labeled.tsv")
    ap.add_argument("--preds", default="llm_preds")
    ap.add_argument("--human-kappa", type=float, default=0.666)
    ap.add_argument("--out", default="llm_results.tsv")
    a = ap.parse_args()

    gold_rows = C.read_tsv(a.gold)
    gold = {r["sentence_id"]: r for r in gold_rows}
    print(f"zlatne oznake: {len(gold)} rečenica, "
          f"SUBJ {sum(1 for r in gold_rows if r['label']=='SUBJ')/len(gold):.1%}\n")

    results, preds = [], {}
    for f in sorted(glob.glob(f"{a.preds}/*.tsv")):
        name = pathlib.Path(f).stem
        rows = list(csv.DictReader(io.open(f, encoding="utf-8", newline=""), **TSV))
        model = rows[0]["model"]
        pairs = [(gold[r["sentence_id"]], r["pred"]) for r in rows
                 if r["sentence_id"] in gold]
        fail = sum(1 for _, p in pairs if p == "PARSE_FAIL")
        usable = [(g, p) for g, p in pairs if p in LAB]
        if not usable:
            print(f"{name}: nema upotrebljivih predikcija"); continue
        s = score([g["label"] for g, _ in usable], [p for _, p in usable])
        s.update(config=name, model=model, fail=fail,
                 fail_rate=fail / len(pairs) if pairs else 0,
                 pred_subj=sum(1 for _, p in usable if p == "SUBJ") / len(usable))
        results.append(s)
        preds[name] = {r["sentence_id"]: r["pred"] for r in rows}

    print("=" * 96)
    print(f"{'konfiguracija':22s} {'model':20s} {'n':>5s} {'makro F1':>9s} "
          f"{'F1 OBJ':>7s} {'F1 SUBJ':>8s} {'tačnost':>8s} {'% SUBJ':>7s} {'fail':>6s}")
    print("=" * 96)
    for s in sorted(results, key=lambda x: -x["macro"]):
        print(f"{s['config']:22s} {s['model'][:20]:20s} {s['n']:5d} "
              f"{s['macro']:9.3f} {s['f_obj']:7.3f} {s['f_subj']:8.3f} "
              f"{s['acc']:8.3f} {s['pred_subj']:7.1%} {s['fail_rate']:6.1%}")

    best = max(results, key=lambda x: x["macro"])
    print(f"\n  najbolja: {best['config']}  makro F1 {best['macro']:.3f}")
    print(f"  ljudska granica: saglasnost anotatora kapa = {a.human_kappa:.3f}")
    print(f"  udeo SUBJ u zlatnim oznakama: "
          f"{sum(1 for r in gold_rows if r['label']=='SUBJ')/len(gold_rows):.1%}")

    print("\n" + "=" * 96)
    print("POREĐENJA PO DIMENZIJI (razlika u makro F1)")
    print("=" * 96)
    by = {s["config"]: s for s in results}

    def cmp(a_, b_, label):
        if a_ not in by or b_ not in by:
            return
        d = by[a_]["macro"] - by[b_]["macro"]
        shared = [i for i in preds[a_]
                  if i in gold and i in preds[b_]
                  and preds[a_][i] in LAB and preds[b_][i] in LAB]
        gl = [gold[i]["label"] for i in shared]
        b01, b10, pv = mcnemar(gl, [preds[a_][i] for i in shared],
                               [preds[b_][i] for i in shared])
        sig = "značajno" if pv < 0.05 else "nije značajno"
        print(f"  {label:30s} {by[a_]['macro']:.3f} : {by[b_]['macro']:.3f}"
              f"   razlika {d:+.3f}   McNemar p={pv:.3f}  {sig}")
        print(f"     {'':30s} ({a_} bolji u {b01}, {b_} u {b10} rečenica)")

    models = sorted({s["model"] for s in results})
    for m in sorted({c.split("-")[0] for c in by}):
        cmp(f"{m}-sr-zero", f"{m}-en-zero", "jezik upita (zero-shot)")
        cmp(f"{m}-sr-few", f"{m}-en-few", "jezik upita (few-shot)")
        cmp(f"{m}-sr-few", f"{m}-sr-zero", "primeri u upitu (srpski)")
        cmp(f"{m}-en-few", f"{m}-en-zero", "primeri u upitu (engleski)")
    if len({c.split("-")[0] for c in by}) > 1:
        for lang, shots in itertools.product(("sr", "en"), ("zero", "few")):
            ms = sorted(c for c in by if c.endswith(f"{lang}-{shots}"))
            if len(ms) == 2:
                cmp(ms[0], ms[1], f"model ({lang}-{shots})")

    print("\n" + "=" * 96)
    print(f"PODSKUPOVI — makro F1 najbolje konfiguracije ({best['config']})")
    print("=" * 96)
    p = preds[best["config"]]

    def sub(pred_fn, label):
        u = [(gold[i], p[i]) for i in p
             if i in gold and p[i] in LAB and pred_fn(gold[i])]
        if len(u) < 30:
            print(f"  {label:30s} n={len(u):4d}  premalo za meru"); return
        s = score([g["label"] for g, _ in u], [q for _, q in u])
        print(f"  {label:30s} n={s['n']:4d}  makro F1 {s['macro']:.3f}   "
              f"F1 SUBJ {s['f_subj']:.3f}")

    for g in ("kolumna", "vest"):
        sub(lambda r, g=g: r["genre"] == g, f"žanr = {g}")
    for t in sorted({r["topic"] for r in gold_rows}):
        sub(lambda r, t=t: r["topic"] == t, f"tema = {t}")
    for s_ in sorted({r["source"] for r in gold_rows}):
        sub(lambda r, s_=s_: r["source"] == s_, f"izvor = {s_}")
    sub(lambda r: r.get("in_quote") == "Y", "unutar navoda (P6, P13)")
    sub(lambda r: r["text"].rstrip().endswith("?"), "pitanja (P9)")

    print("\n  prema saglasnosti anotatora:")
    sub(lambda r: r.get("izvor_oznake") == "saglasnost", "  puna saglasnost")
    sub(lambda r: r.get("izvor_oznake") == "usaglaseno", "  bilo sporno")

    cols = ["config", "model", "n", "macro", "f_obj", "f_subj", "p_subj",
            "r_subj", "acc", "pred_subj", "fail", "fail_rate"]
    with io.open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar=None,
                       quoting=csv.QUOTE_NONE, lineterminator="\n")
        w.writerow(cols)
        for s in results:
            w.writerow([f"{s[c]:.4f}" if isinstance(s[c], float) else s[c]
                        for c in cols])
    print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
