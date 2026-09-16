import csv
import io
import collections
import statistics
import sys

from scipy.stats import wilcoxon

sys.stdout.reconfigure(encoding="utf-8")

REFERENCE = "w1-tfidf-lower"
CONFIGS = ["w1-tfidf-lower", "w12-tfidf-lower", "w13-tfidf-lower",
           "w12-tf-lower", "w13-tf-lower"]
MODELS = ["logreg", "nb"]
SCHEMES = ["plain", "grouped"]


def load(path="results.tsv"):
    return list(csv.DictReader(io.open(path, encoding="utf-8", newline=""),
                                delimiter="\t", quotechar=None,
                                quoting=csv.QUOTE_NONE))

def group(rows, keys):
    by = collections.defaultdict(list)
    for r in rows:
        by[tuple(r[k] for k in keys)].append(r)
    return by


def main():
    rows = load()
    by_cms = group(rows, ["config", "model", "scheme"])

    print("=" * 70)
    print("BROJ ODLIKA (prosek preko slojeva, po konfiguraciji)")
    print("=" * 70)
    by_config = collections.defaultdict(list)
    for r in rows:
        by_config[r["config"]].append(int(r["n_features"]))
    n_feat = {}
    for k in CONFIGS:
        n_feat[k] = statistics.mean(by_config[k])
        print(f"  {k:20s} {n_feat[k]:8.0f} odlika")

    print("\n" + "=" * 70)
    print("MAKRO F1 -- prosek ± std, obe šeme jedna pored druge")
    print("=" * 70)
    print(f"{'config':20s} {'model':7s} {'plain (mean±std)':20s} "
          f"{'grouped (mean±std)':20s} {'razlika (plain-grouped)':>24s}")
    scheme_stats = {}
    for cfg in CONFIGS:
        for m in MODELS:
            vals = {}
            for sch in SCHEMES:
                f1s = [float(r["macro_f1"]) for r in by_cms[(cfg, m, sch)]]
                vals[sch] = (statistics.mean(f1s), statistics.stdev(f1s), f1s)
            scheme_stats[(cfg, m)] = vals
            diff = vals["plain"][0] - vals["grouped"][0]
            print(f"{cfg:20s} {m:7s} "
                  f"{vals['plain'][0]:.3f}±{vals['plain'][1]:.3f}          "
                  f"{vals['grouped'][0]:.3f}±{vals['grouped'][1]:.3f}          "
                  f"{diff:+.3f}")

    print("\n" + "=" * 70)
    print(f"UPARENI VILKOKSONOV TEST naspram reference ({REFERENCE}), po sloju")
    print("=" * 70)
    for m in MODELS:
        for sch in SCHEMES:
            ref_f1 = scheme_stats[(REFERENCE, m)][sch][2]
            print(f"\n[{m} / {sch}]  referenca {REFERENCE} = "
                  f"{statistics.mean(ref_f1):.3f}")
            for cfg in CONFIGS:
                if cfg == REFERENCE:
                    continue
                other_f1 = scheme_stats[(cfg, m)][sch][2]
                try:
                    stat, p = wilcoxon(other_f1, ref_f1)
                except ValueError as e:
                    stat, p = float("nan"), float("nan")
                d = statistics.mean(other_f1) - statistics.mean(ref_f1)
                sig = "  <- ZNAČAJNO (p<0.05)" if p < 0.05 else ""
                print(f"  {cfg:20s} {statistics.mean(other_f1):.3f}  "
                      f"(razlika {d:+.3f}, p={p:.4f}){sig}")

    out = "analysis_summary.tsv"
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar=None,
                        quoting=csv.QUOTE_NONE, lineterminator="\n")
        w.writerow(["config", "model", "scheme", "macro_f1_mean", "macro_f1_std",
                    "n_features_mean", "diff_plain_minus_grouped",
                    "wilcoxon_p_vs_ref"])
        for cfg in CONFIGS:
            for m in MODELS:
                for sch in SCHEMES:
                    mean_f1, std_f1, f1s = scheme_stats[(cfg, m)][sch]
                    diff = (scheme_stats[(cfg, m)]["plain"][0]
                            - scheme_stats[(cfg, m)]["grouped"][0])
                    if cfg == REFERENCE:
                        p = ""
                    else:
                        ref_f1 = scheme_stats[(REFERENCE, m)][sch][2]
                        try:
                            _, p = wilcoxon(f1s, ref_f1)
                            p = f"{p:.4f}"
                        except ValueError:
                            p = "nan"
                    w.writerow([cfg, m, sch, f"{mean_f1:.4f}", f"{std_f1:.4f}",
                                f"{n_feat[cfg]:.0f}", f"{diff:+.4f}", p])
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
