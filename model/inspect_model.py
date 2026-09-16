#!/usr/bin/env python3
"""
inspect_model.py — šta je najbolji osnovni model zapravo naučio.

Tri stvari, i sve tri idu u izveštaj:

  1. NAJJAČE ODLIKE PO KLASI. Ovo je provera konfaunda koju smo obećali posle
     napomene sa konsultacija. Ako među odlikama koje vuku ka SUBJ dominiraju
     tematske imenice (utakmica, policija, festival), model delom prepoznaje
     temu umesto subjektivnosti — bez obzira na to što je na nivou korpusa
     tema x oznaka bila zanemarljiva. Ako dominiraju ocenjivačke reči, naučio
     je ono što treba.

     Kod logističke regresije to su koeficijenti. Kod Bajesa nema koeficijenata
     u istom smislu, pa se koristi razlika logaritama verovatnoća između klasa,
     što odlike rangira na isti način.

  2. PREDIKCIJE IZVAN SLOJA (out-of-fold). Svaka rečenica se predviđa modelom
     koji je nije video. Bez toga bi analiza grešaka bila nad podacima na kojima
     je model učio, pa bi izgledao bolji nego što jeste.

  3. PODSKUPOVI, u istom obliku u kojem ih daje score_llm.py — po žanru, temi,
     izvoru, unutar navoda, pitanja, i prema tome da li su se anotatori složili.
     Tek tako se track A i track B mogu uporediti red po red.

Pokretanje:
    python3 inspect_model.py --data ../corpus_labeled.tsv \\
        --config w13-tf-lower-stem --model nb
"""

import csv, io, re, argparse, collections, sys
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold, GridSearchCV, StratifiedKFold

import features as F

sys.path.insert(0, "../src")
import common as C

LAB = ("OBJ", "SUBJ")
P8 = re.compile(r"\b(naravno|dakle|uostalom|naime|zapravo|inače)\b", re.I)


def load(path):
    rows = [r for r in C.read_tsv(path) if r.get("label") in LAB]
    X = [r.get("text_marked") or r["text"] for r in rows]
    y = np.array([1 if r["label"] == "SUBJ" else 0 for r in rows])
    g = np.array([f'{r["source"]}-{r["article_id"]}' for r in rows])
    return rows, X, y, g


def ranking(pipe):
    """Odlike poređane od najjačeg dokaza za OBJ do najjačeg za SUBJ."""
    vec = pipe.named_steps["vec"]
    clf = pipe.named_steps["clf"]
    names = np.array(vec.get_feature_names_out())
    if hasattr(clf, "coef_"):
        w = clf.coef_[0]
    else:                                   # Bajes: razlika log-verovatnoća
        w = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
    return names, w


def prf(gold, pred, pos):
    tp = sum(1 for g, p in zip(gold, pred) if g == p == pos)
    fp = sum(1 for g, p in zip(gold, pred) if p == pos and g != pos)
    fn = sum(1 for g, p in zip(gold, pred) if g == pos and p != pos)
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return 2 * pr * rc / (pr + rc) if pr + rc else 0.0


def macro(gold, pred):
    return sum(prf(gold, pred, l) for l in (0, 1)) / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../corpus_labeled.tsv")
    ap.add_argument("--config", default="w13-tf-lower-stem")
    ap.add_argument("--model", default="nb")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--out", default="oof_predictions.tsv")
    a = ap.parse_args()

    rows, X, y, g = load(a.data)
    print(f"{len(rows)} rečenica, {len(set(g))} članaka, SUBJ {y.mean():.1%}")
    print(f"konfiguracija: {a.config} + {a.model}\n")

    # ---------------------------------------------------- 1. najjače odlike
    pipe, grid = F.build(a.config, a.model)
    gs = GridSearchCV(pipe, grid, scoring="f1_macro",
                      cv=StratifiedKFold(5, shuffle=True, random_state=0), n_jobs=-1)
    gs.fit(X, y)
    fitted = gs.best_estimator_
    names, w = ranking(fitted)
    order = np.argsort(w)
    print("=" * 74)
    print(f"NAJJAČE ODLIKE  ({len(names)} ukupno, hiperparametar {gs.best_params_})")
    print("=" * 74)
    print(f"{'ka OBJ':38s}  {'ka SUBJ':38s}")
    for i in range(a.top):
        lo, hi = order[i], order[-(i + 1)]
        print(f"  {names[lo][:28]:28s} {w[lo]:7.3f}    "
              f"{names[hi][:28]:28s} {w[hi]:7.3f}")
    print("\n  Pitanje za izveštaj: da li su na SUBJ strani ocenjivačke reči\n"
          "  ili tematske imenice? Drugo bi značilo da model delom prepoznaje\n"
          "  temu, uprkos tome što je tema x oznaka na nivou korpusa V=0.116.")

    # --------------------------------------------- 2. predikcije izvan sloja
    print("\n" + "=" * 74)
    print("PREDIKCIJE IZVAN SLOJA (grupisani slojevi po članku)")
    print("=" * 74)
    oof = np.empty(len(y), dtype=object)
    outer = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=0)
    for k, (tr, te) in enumerate(outer.split(X, y, g)):
        p2, grid2 = F.build(a.config, a.model)
        gs2 = GridSearchCV(p2, grid2, scoring="f1_macro",
                           cv=StratifiedKFold(5, shuffle=True, random_state=0),
                           n_jobs=-1)
        gs2.fit([X[i] for i in tr], y[tr])
        pred = gs2.predict([X[i] for i in te])
        for idx, p in zip(te, pred):
            oof[idx] = LAB[p]
        print(f"  sloj {k}: {len(te)} rečenica", end="\r", flush=True)
    print(" " * 40, end="\r")

    gold = [LAB[v] for v in y]
    pred = list(oof)
    print(f"  makro F1 izvan sloja: {macro(y, [LAB.index(p) for p in pred]):.3f}")
    conf = collections.Counter(zip(gold, pred))
    print(f"\n  matrica konfuzije (red = zlatno, kolona = predviđeno)")
    print(f"    {'':6s} {'OBJ':>7s} {'SUBJ':>7s}")
    for l in LAB:
        print(f"    {l:6s} {conf[(l,'OBJ')]:7d} {conf[(l,'SUBJ')]:7d}")

    for r, p in zip(rows, pred):
        r["pred"] = p
    C.write_tsv(a.out, rows, list(rows[0].keys()))
    print(f"\n  -> {a.out}")

    # ------------------------------------------------------- 3. podskupovi
    print("\n" + "=" * 74)
    print("PODSKUPOVI  (isti oblik kao u score_llm.py, radi poređenja)")
    print("=" * 74)

    def sub(fn, label):
        idx = [i for i, r in enumerate(rows) if fn(r)]
        if len(idx) < 30:
            print(f"  {label:30s} n={len(idx):4d}  premalo za meru"); return
        gg = [y[i] for i in idx]
        pp = [LAB.index(pred[i]) for i in idx]
        print(f"  {label:30s} n={len(idx):4d}  makro F1 {macro(gg,pp):.3f}   "
              f"F1 SUBJ {prf(gg,pp,1):.3f}")

    for gn in ("kolumna", "vest"):
        sub(lambda r, gn=gn: r["genre"] == gn, f"žanr = {gn}")
    for t in sorted({r["topic"] for r in rows}):
        sub(lambda r, t=t: r["topic"] == t, f"tema = {t}")
    for s in sorted({r["source"] for r in rows}):
        sub(lambda r, s=s: r["source"] == s, f"izvor = {s}")
    sub(lambda r: r.get("in_quote") == "Y", "unutar navoda (P6, P13)")
    sub(lambda r: r["text"].rstrip().endswith("?"), "pitanja (P9)")
    sub(lambda r: bool(P8.search(r["text"])), "diskursni konektori (P8)")
    print("\n  prema saglasnosti anotatora:")
    sub(lambda r: r.get("izvor_oznake") == "saglasnost", "  puna saglasnost")
    sub(lambda r: r.get("izvor_oznake") == "usaglaseno", "  bilo sporno")

    # ----------------------------------------------------- najgore greške
    print("\n" + "=" * 74)
    print("PRIMERI GREŠAKA (za ručnu analizu)")
    print("=" * 74)
    for want, got in (("SUBJ", "OBJ"), ("OBJ", "SUBJ")):
        bad = [r for r in rows if r["label"] == want and r["pred"] == got]
        print(f"\n  zlatno {want}, predviđeno {got}  ({len(bad)} rečenica)")
        for r in bad[:8]:
            print(f"    [{r['genre'][:3]}/{r['source'][:4]}] "
                  f"{(r.get('text_marked') or r['text'])[:84]}")


if __name__ == "__main__":
    main()
