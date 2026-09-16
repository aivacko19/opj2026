#!/usr/bin/env python3
"""
stemmer.py — stemer Ljubešića i Pandžića ("Simple stemmer for Croatian v0.1"),
u obliku upotrebljivom kao scikit-learn `preprocessor`.

Pravila su ugrađena u `lp_rules.py`, izvučena iz referentne Java implementacije
(SCStemmers, Vuk Batanović, GPL v3), pa se ništa ne preuzima ručno.

Stemer je razvijen za hrvatski, ali se koristi i za srpski — u radovima o analizi
sentimenta na srpskom davao je bolje rezultate od lematizacije, a prednost mu je
rasla sa n-gramima višeg reda. To je i razlog zašto ga koristimo uz n-gramske
odlike, kako je predloženo na konsultacijama.

ALGORITAM (verno prema referentnoj implementaciji):

    stem(reč):
        1. ako je reč u STOPSET (mala slova) -> vrati je nepromenjenu
        2. primeni prvu odgovarajuću sufiksnu transformaciju
        3. probaj pravila redom; prvo koje se poklopi deli reč na osnovu i nastavak
        4. osnova se prihvata ako ima više od jednog znaka i sadrži samozvučnik
        5. ako nijedno pravilo ne prođe, vrati transformisanu reč

    Samozvučnik je [aeiouR], gde se slogotvorno r prethodno kapitalizuje
    obrascem (^|[^aeiou])r($|[^aeiou]), pa reči poput 'prst' ili 'krv' prolaze.

ODSTUPANJE OD REFERENCE: u Javi su transformacije HashMap, pa je redosled
provere nedeterministički. Dva ključa se preklapaju kao sufiksi ('anjac'/'njac'
i 'teticima'/'ticima'), pa kod njih redosled menja rezultat. Ovde se ide od
najdužeg ključa ka najkraćem, što bira specifičniju transformaciju.

VAŽNO ZA scikit-learn: prosleđen `preprocessor` ZAMENJUJE ugrađeno spuštanje na
mala slova, pa `lowercase=True` na vektorizatoru nema efekta. Zato ovaj omotač
sam radi lowercasing, kontrolisano parametrom `lowercase`.

Provera ispravnosti:
    python3 stemmer.py
"""

import re, sys, functools
from lp_rules import STOPSET, TRANSFORMATIONS, RULES

WORD = re.compile(r"\w+", re.UNICODE)
VOWEL = re.compile(r"[aeiouR]")
SYLLABIC_R = re.compile(r"(^|[^aeiou])r($|[^aeiou])")

# duži ključ prvi — vidi napomenu o odstupanju iznad
_TRANS = sorted(TRANSFORMATIONS, key=lambda kv: -len(kv[0]))
_RULES = [re.compile(f"^({a})({b})$") for a, b in RULES]


def _has_vowel(w):
    return bool(VOWEL.search(SYLLABIC_R.sub(r"\1R\2", w)))


@functools.lru_cache(maxsize=300_000)
def stem_word(word):
    """Koren jedne reči. Keširano — poziva se milionima puta kroz mrežu odlika."""
    if word.lower() in STOPSET:
        return word
    w = word
    for find, repl in _TRANS:
        if w.endswith(find):
            w = w[:len(w) - len(find)] + repl
            break
    for rule in _RULES:
        m = rule.match(w)
        if m and len(m.group(1)) > 1 and _has_vowel(m.group(1)):
            return m.group(1)
    return w


class Stemmer:
    """Pozivljiv objekat za `TfidfVectorizer(preprocessor=Stemmer())`."""

    def __init__(self, lowercase=True):
        self.lowercase = lowercase

    def __call__(self, text):
        """Stemuje reči, a interpunkciju ostavlja na mestu.

        Interpunkcija se čuva jer navodnici nose informaciju (kolona in_quote),
        pa bi spajanje samo korena razmacima izgubilo taj signal.
        """
        if self.lowercase:
            text = text.lower()
        return WORD.sub(lambda m: stem_word(m.group(0)), text)


# ---------------------------------------------------------------------- provera

FAMILIES = [
    ("sramotan", "sramotna", "sramotni", "sramotno", "sramotnog"),
    ("zavidan", "zavidna", "zavidni", "zavidnom"),
    ("kolumna", "kolumne", "kolumnu", "kolumni", "kolumnama"),
    ("subjektivan", "subjektivna", "subjektivnost", "subjektivnosti"),
    ("novinar", "novinara", "novinaru", "novinarima", "novinarski"),
    ("izbor", "izbora", "izbore", "izborima", "izborni"),
]
DISTINCT = [("rad", "rat"), ("vlada", "vladar"), ("pisac", "pismo")]


def selftest():
    st = Stemmer()
    print(f"pravila {len(_RULES)} | transformacija {len(_TRANS)} | "
          f"stop-reči {len(STOPSET)}\n")

    forms = distinct = 0
    print("saživanje oblika iste reči")
    for fam in FAMILIES:
        stems = [stem_word(w) for w in fam]
        forms += len(fam); distinct += len(set(stems))
        print(f"  {len(fam)} -> {len(set(stems))}   {' '.join(fam)}")
        print(f"            {' '.join(stems)}")
    ratio = forms / distinct
    print(f"\n  kompresija: {forms} oblika -> {distinct} korena ({ratio:.2f}x)")

    ok = ratio >= 1.3
    if not ok:
        print("  GREŠKA: gotovo nikakvo saživanje — pravila se ne primenjuju")

    print("\nrazličite reči ne smeju da se spoje")
    for a, b in DISTINCT:
        sa, sb = stem_word(a), stem_word(b)
        print(f"  {'OK  ' if sa != sb else 'PAŽNJA'} {a} -> {sa} | {b} -> {sb}")

    print("\nstop-reči ostaju nepromenjene")
    for w in ("biti", "mogu", "treba", "želimo"):
        s = stem_word(w)
        print(f"  {'OK  ' if s == w else 'GREŠKA'} {w} -> {s}")
        ok &= s == w

    print("\nslogotvorno r prolazi kao samozvučnik")
    for w in ("prst", "krv", "crn"):
        print(f"  {w}: has_vowel={_has_vowel(w)}")
        ok &= _has_vowel(w)

    print("\nočuvanje interpunkcije i navodnika")
    t = '„Ovaj zakon je sramotan i štetan.“'
    out = st(t)
    print(f"  {t}\n  -> {out}")
    ok &= "„" in out and "“" in out

    print("\n" + ("Stemer radi." if ok else "Stemer NE radi — vidi greške iznad."))
    return ok


if __name__ == "__main__":
    sys.exit(0 if selftest() else 1)
