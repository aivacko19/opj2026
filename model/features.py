#!/usr/bin/env python3
"""
features.py — mreža odlika, kao lista imenovanih konfiguracija.

Zašto imenovane konfiguracije umesto ugnežđenih petlji: svaki red u tabeli
ablacije ima ime koje se može citirati u izveštaju, i svaka konfiguracija menja
TAČNO JEDNU stvar u odnosu na referentnu. Ukrštanje svega dalo bi tabelu u kojoj
se razlike ne mogu pripisati pojedinačnom faktoru.

Referentna konfiguracija (`w1-tfidf-lower`) je namerno najjednostavnija:
unigrami, TF-IDF, mala slova, bez stemovanja. Sve ostalo se poredi sa njom.

Faktori u prvoj verziji su oni koje traži predlog projekta i napomena sa
konsultacija:
    - spuštanje na mala slova (lowercasing)
    - TF naspram TF-IDF
    - n-gramski opseg reči: (1,1), (1,2), (1,3)
    - stemovanje (Ljubešić–Pandžić)

Kasnije se dodaju, ako bude vremena: karakterski n-grami 3-5, binarno
ponderisanje, uklanjanje stop-reči. Dodavanje je dopisivanje reda u CONFIGS —
ostatak koda se ne menja, a `results.tsv` je u dugom formatu pa se novi redovi
samo dopisuju.

VAŽNO: vektorizator je UVEK unutar Pipeline-a. Ako se nauči nad celim skupom pa
tek onda podeli na slojeve, statistika dokumentne frekvencije (IDF) je videla
test sloj i rezultati su naduvani. Pipeline ga uči iznova na svakom sloju.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

from stemmer import Stemmer

MIN_DF = 2          # odlika mora da se javi u bar dva primera; kroti retke trigrame


def vectorizer(ngram=(1, 1), idf=True, lower=True, stem=False):
    """TF-IDF ili TF vektorizator sa opcionim stemovanjem.

    Stemer se prosleđuje kao `preprocessor`, čime ZAMENJUJE ugrađeno spuštanje
    na mala slova, pa ga sam radi (parametar `lowercase` na Stemmer-u).
    """
    if stem:
        pre, low = Stemmer(lowercase=lower), False
    else:
        pre, low = None, lower
    return TfidfVectorizer(ngram_range=ngram, use_idf=idf, min_df=MIN_DF,
                           preprocessor=pre, lowercase=low,
                           sublinear_tf=False, token_pattern=r"(?u)\b\w+\b")


# ime -> (opis za tabelu, kwargs za vectorizer)
CONFIGS = {
    # ---- referentna ----
    "w1-tfidf-lower":        ("unigrami, TF-IDF, mala slova",      dict()),

    # ---- n-gramski opseg ----
    "w12-tfidf-lower":       ("+ bigrami",                         dict(ngram=(1, 2))),
    "w13-tfidf-lower":       ("+ trigrami",                        dict(ngram=(1, 3))),

    # ---- ponderisanje ----
    "w1-tf-lower":           ("TF umesto TF-IDF",                  dict(idf=False)),
    "w12-tf-lower":          ("TF, bigrami",                       dict(ngram=(1, 2), idf=False)),
    "w13-tf-lower":          ("TF, trigrami",                      dict(ngram=(1, 3), idf=False)),

    # ---- mala slova ----
    "w1-tfidf-nolower":      ("bez spuštanja na mala slova",       dict(lower=False)),
    "w13-tfidf-nolower":     ("bez malih slova, trigrami",         dict(ngram=(1, 3), lower=False)),

    # ---- stemovanje ----
    "w1-tfidf-lower-stem":   ("+ stemovanje",                      dict(stem=True)),
    "w12-tfidf-lower-stem":  ("stemovanje, bigrami",               dict(ngram=(1, 2), stem=True)),
    "w13-tfidf-lower-stem":  ("stemovanje, trigrami",              dict(ngram=(1, 3), stem=True)),
    "w13-tf-lower-stem":     ("stemovanje, trigrami, TF",          dict(ngram=(1, 3), idf=False, stem=True)),
}

REFERENCE = "w1-tfidf-lower"

# hiperparametar koji se traži ugnežđenom validacijom, po modelu
MODELS = {
    "logreg": (lambda: LogisticRegression(max_iter=2000, solver="liblinear"),
               {"clf__C": [0.01, 0.1, 1, 10, 100]}),
    "nb":     (lambda: MultinomialNB(),
               {"clf__alpha": [0.01, 0.1, 0.5, 1.0, 2.0]}),
}


def build(config_name, model_name):
    """Vraća (Pipeline, mreža_hiperparametara) za zadatu kombinaciju."""
    _, kw = CONFIGS[config_name]
    make_clf, grid = MODELS[model_name]
    return Pipeline([("vec", vectorizer(**kw)), ("clf", make_clf())]), grid


if __name__ == "__main__":
    print(f"{len(CONFIGS)} konfiguracija x {len(MODELS)} modela = "
          f"{len(CONFIGS)*len(MODELS)} kombinacija\n")
    for name, (desc, kw) in CONFIGS.items():
        ref = "  <- referentna" if name == REFERENCE else ""
        print(f"  {name:24s} {desc}{ref}")
    print("\nprovera da se svaka konfiguracija gradi (broj odlika)")
    import csv, pathlib, sys
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "../to_annotate.tsv")
    if src.exists():
        demo = [r["text"] for r in
                csv.DictReader(io.open(src, encoding="utf-8"), delimiter="\t")]
        print(f"  ulaz: {src} ({len(demo)} rečenica)\n")
    else:
        demo = [f"Rečenica broj {i} iznosi tvrdnju o događaju i sadrži dovoljno "
                f"reči da se iz nje izgrade odlike raznih vrsta." for i in range(40)]
        demo += [f"Ova {i}. rečenica je subjektivna jer je sramotna, zavidna i "
                 f"zaista štetna po svakoga ko je pročita." for i in range(40)]
        print(f"  ulaz: sintetički ({len(demo)} rečenica) — "
              f"zadaj putanju do to_annotate.tsv za pravi broj\n")
    base = None
    for name in CONFIGS:
        pipe, _ = build(name, "logreg")
        n = pipe.named_steps["vec"].fit_transform(demo).shape[1]
        if base is None:
            base = n
        print(f"  {name:24s} {n:6d} odlika   ({n/base:5.2f}x referentne)")
