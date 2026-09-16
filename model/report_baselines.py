#!/usr/bin/env python3
"""
report_baselines.py — analiza rezultata iz results.tsv.

Ulaz je dugi format: jedan red po sloju unakrsne validacije. Zato se testovi
značajnosti rade upareno, po slojevima, a ne nad prosecima.

ŠTA SE RAČUNA:

  1. Tabela ablacije — prosek i standardna devijacija makro F1 po konfiguraciji,
     za obe sheme slojeva jedna pored druge.

  2. Razlika između shema (obična minus grupisana). To je MERA CURENJA kroz
     članke: koliko je prividne uspešnosti došlo od toga što sedam od osam
     rečenica jednog članka završi u trening skupu. Sama razlika je rezultat i
     ide u izveštaj.

  3. Vilkoksonov upareni test u odnosu na referentnu konfiguraciju. Koristi se
     umesto t-testa jer slojevi unakrsne validacije nisu nezavisni, pa je t-test
     na njima poznato preoptimističan.

  4. Broj odlika po konfiguraciji. Bez toga se ne vidi razlika između „nije
     pomoglo" i „nije imalo od čega da uči".

  5. Izabrani hiperparametar po sloju. Ako se stalno bira ivica mreže, mrežu
     treba proširiti.

Pokretanje:
    python3 report_baselines.py --results results.tsv
    python3 report_baselines.py --results results.tsv --model logreg
"""

import csv, io, argparse, collections, statistics, sys
import features as F


def load(path):
    rows = list(csv.DictReader(io.open(path, encoding="utf-8", newline=""),
                               delimiter="\t"))
    if not rows:
        sys.exit(f"{path} je prazan")
    for r in rows:
        for k in ("macro_f1", "f1_obj", "f1_subj", "accuracy"):
            r[k] = float(r[k])
        r["n_features"] = int(r["n_features"])
        r["fold"] = int(r["fold"])
    return rows


def wilcoxon(a, b):
    """Upareni Vilkoksonov test. Vraća (statistika, p) ili (None, None)."""
    try:
        from scipy.stats import wilcoxon as w
        if all(x == y for x, y in zip(a, b)):
            return 0.0, 1.0
        s, p = w(a, b)
        return float(s), float(p)
    except ImportError:
        return None, None
    except ValueError:
        return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results.tsv")
    ap.add_argument("--model", help="ograniči na jedan model (logreg / nb)")
    ap.add_argument("--metric", default="macro_f1")
    a = ap.parse_args()

    rows = load(a.results)
    if a.model:
        rows = [r for r in rows if r["model"] == a.model]

    folds = collections.defaultdict(dict)      # (config, model, scheme) -> {fold: red}
    for r in rows:
        folds[(r["config"], r["model"], r["scheme"])][r["fold"]] = r

    configs = sorted({k[0] for k in folds},
                     key=lambda c: list(F.CONFIGS).index(c) if c in F.CONFIGS else 99)
    models = sorted({k[1] for k in folds})
    print(f"{len(rows)} redova | {len(configs)} konfiguracija | modeli: {models}\n")

    def series(cfg, mdl, sch, field="macro_f1"):
        d = folds.get((cfg, mdl, sch), {})
        return [d[f][field] for f in sorted(d)]

    # ------------------------------------------------- 1. tabela ablacije
    for mdl in models:
        print("=" * 100)
        print(f"MODEL: {mdl}")
        print("=" * 100)
        print(f"{'konfiguracija':24s} {'obična podela':>16s} {'grupisana':>16s} "
              f"{'razlika':>9s} {'F1 SUBJ':>9s} {'odlika':>9s} {'p vs ref':>10s}")
        print("-" * 100)
        ref_g = series(F.REFERENCE, mdl, "grouped")
        for cfg in configs:
            pl, gr = series(cfg, mdl, "plain"), series(cfg, mdl, "grouped")
            if not gr:
                continue
            sub = series(cfg, mdl, "grouped", "f1_subj")
            nf = statistics.mean(v["n_features"]
                                 for v in folds[(cfg, mdl, "grouped")].values())
            gap = (statistics.mean(pl) - statistics.mean(gr)) if pl else float("nan")
            if cfg == F.REFERENCE or not ref_g or len(gr) != len(ref_g):
                pstr = "referentna" if cfg == F.REFERENCE else "—"
            else:
                _, p = wilcoxon(gr, ref_g)
                pstr = "—" if p is None else f"{p:.3f}{'*' if p < 0.05 else ''}"
            plstr = (f"{statistics.mean(pl):.3f}±{statistics.pstdev(pl):.3f}"
                     if pl else "—")
            print(f"{cfg:24s} {plstr:>16s} "
                  f"{statistics.mean(gr):.3f}±{statistics.pstdev(gr):.3f}   "
                  f"{gap:+9.3f} {statistics.mean(sub):9.3f} {nf:9.0f} {pstr:>10s}")
        print()

    # ------------------------------------------------- 2. mera curenja
    print("=" * 100)
    print("CURENJE KROZ ČLANKE (obična minus grupisana)")
    print("=" * 100)
    gaps = []
    for mdl in models:
        for cfg in configs:
            pl, gr = series(cfg, mdl, "plain"), series(cfg, mdl, "grouped")
            if pl and gr:
                gaps.append(statistics.mean(pl) - statistics.mean(gr))
    if gaps:
        print(f"  prosečna razlika: {statistics.mean(gaps):+.3f}   "
              f"raspon {min(gaps):+.3f} do {max(gaps):+.3f}   (n={len(gaps)})")
        print("  Toliko bi rezultat bio naduvan da smo koristili samo običnu\n"
              "  stratifikovanu podelu, bez grupisanja po članku.")

    # ------------------------------------------------- 3. izbor hiperparametra
    print("\n" + "=" * 100)
    print("IZABRANI HIPERPARAMETAR (ugnežđena validacija, grupisani slojevi)")
    print("=" * 100)
    for mdl in models:
        grid = F.MODELS[mdl][1]
        vals = sorted({v for g in grid.values() for v in g},
                      key=lambda x: float(x))
        print(f"\n  {mdl}  (mreža: {vals})")
        for cfg in configs:
            d = folds.get((cfg, mdl, "grouped"), {})
            if not d:
                continue
            c = collections.Counter(r["best_param"] for r in d.values())
            edge = ""
            if c and str(vals[0]) in c or str(vals[-1]) in c:
                n_edge = c.get(str(vals[0]), 0) + c.get(str(vals[-1]), 0)
                if n_edge >= len(d) / 2:
                    edge = "   <-- često bira ivicu mreže"
            print(f"    {cfg:24s} {dict(c.most_common())}{edge}")

    # ------------------------------------------------- 4. najbolje
    print("\n" + "=" * 100)
    best = max(((cfg, mdl, statistics.mean(series(cfg, mdl, "grouped")))
                for cfg in configs for mdl in models
                if series(cfg, mdl, "grouped")), key=lambda x: x[2])
    print(f"NAJBOLJA (grupisani slojevi): {best[0]} + {best[1]}  "
          f"makro F1 {best[2]:.3f}")
    print("=" * 100)
    print("\n  * uz p znači značajno na nivou 0.05, Vilkoksonov upareni test\n"
          "    nad vrednostima po slojevima, u odnosu na referentnu konfiguraciju")


if __name__ == "__main__":
    main()
