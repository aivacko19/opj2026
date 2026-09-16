#!/usr/bin/env python3
"""
run_baselines.py — ugnežđena unakrsna validacija za sve konfiguracije iz features.py.

DVE SHEME SLOJEVA, obe se pokreću i obe se prijavljuju:

  plain    StratifiedKFold — ono što propozicije doslovno traže: 10 slojeva,
           stratifikovano po oznaci.

  grouped  StratifiedGroupKFold po article_id — sve rečenice jednog članka
           ostaju u istom sloju.

Zašto obe. Prozor je 8 uzastopnih rečenica iz istog članka, pa kod obične podele
7 od 8 rečenica završi u trening skupu dok 1 ide u test. Model tada delimično
prepoznaje članak umesto da procenjuje subjektivnost, i rezultat je naduvan.
RAZLIKA IZMEĐU DVE SHEME JE SAMA PO SEBI REZULTAT: meri koliko je prividne
uspešnosti došlo od preklapanja članaka.

UGNEŽĐENA VALIDACIJA: unutar svakog od 10 spoljnih trening skupova radi se još
jedna petostruka validacija kojom se bira hiperparametar (C za logističku
regresiju, alpha za Bajesa). Biranje na spoljnom test sloju značilo bi
prijavljivanje rezultata na podacima koji su učestvovali u odlukama.

METRIKA: makro F1 kao glavna. Pri odnosu klasa oko 80:20 tačnost je beskorisna —
model koji uvek predviđa OBJ ima 80% tačnosti a ne prepoznaje ništa. Makro F1
računa F1 za svaku klasu pa ih usrednjava sa jednakom težinom.

IZLAZ: results.tsv u DUGOM formatu (jedan red po sloju), da bi se kasnije mogle
dopisivati nove konfiguracije bez ponovnog pokretanja postojećih, i da bi se
mogao raditi upareni test značajnosti po slojevima.

Pokretanje:
    python3 run_baselines.py --data ../corpus_labeled.tsv
    python3 run_baselines.py --leak-test        # provera ispravnosti harnessa
    python3 run_baselines.py --data ... --configs w1-tfidf-lower w13-tfidf-lower-stem
"""

import csv, io, sys, time, random, argparse, pathlib, collections
import numpy as np
from sklearn.model_selection import (StratifiedKFold, StratifiedGroupKFold,
                                     GridSearchCV)
from sklearn.metrics import f1_score, accuracy_score

import features as F

OUT = "results.tsv"
COLS = ["config", "model", "scheme", "fold", "macro_f1", "f1_obj", "f1_subj",
        "accuracy", "n_test", "best_param", "n_features"]


def load(path, label_col="label"):
    # čitanje bez escape-ovanja, simetrično sa common.write_tsv
    rows = list(csv.DictReader(io.open(path, encoding="utf-8", newline=""),
                               delimiter="\t", quotechar=None,
                               quoting=csv.QUOTE_NONE))
    rows = [r for r in rows if r.get(label_col, "").strip() in ("OBJ", "SUBJ")]
    if not rows:
        raise SystemExit(f"nema označenih redova u {path} (kolona '{label_col}')")
    X = [r.get("text_marked") or r["text"] for r in rows]
    y = np.array([1 if r[label_col] == "SUBJ" else 0 for r in rows])
    g = np.array([f'{r["source"]}-{r["article_id"]}' for r in rows])
    return X, y, g, rows


def synthetic_leak(n_articles=150, per_article=8, seed=0):
    """Sintetički skup: oznaka je slučajna PO ČLANKU, tekst ne nosi signal.

    Obična podela treba da bude znatno iznad slučajnosti (model prepoznaje
    članak), grupisana treba da bude na ~0.5. Ako nije tako, harness je
    pogrešan i to treba znati pre nego što stignu prave oznake.
    """
    rng = random.Random(seed)
    vocab = [f"rec{i}" for i in range(300)]
    X, y, g = [], [], []
    for a in range(n_articles):
        label = rng.randint(0, 1)
        marker = rng.sample(vocab, 12)          # rečnik svojstven članku
        for _ in range(per_article):
            X.append(" ".join(rng.sample(marker, 8) + rng.sample(vocab, 4)))
            y.append(label); g.append(f"art-{a}")
    return X, np.array(y), np.array(g)


def evaluate(X, y, groups, config, model, scheme, n_outer=10, n_inner=5, seed=0):
    pipe, grid = F.build(config, model)
    if scheme == "grouped":
        outer = StratifiedGroupKFold(n_splits=n_outer, shuffle=True, random_state=seed)
        splits = outer.split(X, y, groups)
    else:
        outer = StratifiedKFold(n_splits=n_outer, shuffle=True, random_state=seed)
        splits = outer.split(X, y)

    rows = []
    for k, (tr, te) in enumerate(splits):
        Xtr = [X[i] for i in tr]; Xte = [X[i] for i in te]
        inner = StratifiedKFold(n_splits=n_inner, shuffle=True, random_state=seed)
        gs = GridSearchCV(pipe, grid, scoring="f1_macro", cv=inner, n_jobs=-1)
        gs.fit(Xtr, y[tr])
        pred = gs.predict(Xte)
        f1s = f1_score(y[te], pred, average=None, labels=[0, 1], zero_division=0)
        rows.append(dict(
            config=config, model=model, scheme=scheme, fold=k,
            macro_f1=round(f1_score(y[te], pred, average="macro", zero_division=0), 4),
            f1_obj=round(f1s[0], 4), f1_subj=round(f1s[1], 4),
            accuracy=round(accuracy_score(y[te], pred), 4),
            n_test=len(te),
            best_param=list(gs.best_params_.values())[0],
            n_features=len(gs.best_estimator_.named_steps["vec"].vocabulary_)))
    return rows


def append(rows, path=OUT):
    new = not pathlib.Path(path).exists()
    with io.open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        if new:
            w.writerow(COLS)
        for r in rows:
            w.writerow([r[c] for c in COLS])


def done_already(path=OUT):
    if not pathlib.Path(path).exists():
        return set()
    return {(r["config"], r["model"], r["scheme"])
            for r in csv.DictReader(io.open(path, encoding="utf-8"), delimiter="\t")}


def summarize(rows):
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["config"], r["model"], r["scheme"])].append(r["macro_f1"])
    for k in sorted(by):
        v = np.array(by[k])
        print(f"    {k[0]:24s} {k[1]:7s} {k[2]:8s} "
              f"macro-F1 {v.mean():.3f} ± {v.std():.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--configs", nargs="*", default=None)
    ap.add_argument("--models", nargs="*", default=list(F.MODELS))
    ap.add_argument("--leak-test", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

    if a.leak_test:
        print("PROVERA CURENJA — oznaka je slučajna po članku, tekst ne nosi signal")
        print("  očekivano: plain znatno iznad 0.5, grouped oko 0.5\n")
        X, y, g = synthetic_leak()
        print(f"  {len(X)} rečenica, {len(set(g))} članaka, "
              f"{y.mean():.0%} SUBJ\n")
        for scheme in ("plain", "grouped"):
            rows = evaluate(X, y, g, F.REFERENCE, "logreg", scheme)
            v = np.array([r["macro_f1"] for r in rows])
            print(f"  {scheme:8s} macro-F1 {v.mean():.3f} ± {v.std():.3f}")
        print("\n  Ako je grouped oko 0.5 a plain osetno veći, harness je ispravan\n"
              "  i razlika meri upravo curenje kroz članke.")
        return

    if not a.data:
        ap.error("zadaj --data ili --leak-test")

    X, y, g, rows = load(a.data, a.label_col)
    print(f"{len(X)} rečenica, {len(set(g))} članaka, "
          f"{y.mean():.1%} SUBJ, {len(y)-y.sum()} OBJ / {y.sum()} SUBJ\n")
    if y.sum() < 30:
        print("  UPOZORENJE: premalo SUBJ primera za smislene rezultate.\n"
              "  Ovo je provera da pipeline radi, ne merenje.\n")

    configs = a.configs or list(F.CONFIGS)
    skip = done_already(a.out)
    todo = [(c, m, s) for c in configs for m in a.models
            for s in ("plain", "grouped") if (c, m, s) not in skip]
    print(f"{len(todo)} kombinacija za pokretanje "
          f"({len(skip)} već u {a.out})\n")

    t0 = time.time()
    for i, (c, m, s) in enumerate(todo, 1):
        t = time.time()
        res = evaluate(X, y, g, c, m, s)
        append(res, a.out)
        v = np.array([r["macro_f1"] for r in res])
        print(f"  [{i:2d}/{len(todo)}] {c:24s} {m:7s} {s:8s} "
              f"macro-F1 {v.mean():.3f} ± {v.std():.3f}   ({time.time()-t:.0f}s)")
    print(f"\nukupno {time.time()-t0:.0f}s  ->  {a.out}")


if __name__ == "__main__":
    main()
