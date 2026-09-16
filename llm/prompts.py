
FEWSHOT = [
    ("vre-4977044-018",
     "Nekada simbol industrijskog napretka i građanskog ponosa, Vajfertova pivara sada je skoro razrušena: ciglene zgrade su urušene, a krovove, takođe urušene, probijaju trava i korov.",
     "OBJ",  "P2 — približnost nije ocena"),
    ("pol-782395-003",
     "„Niko u njemu ne vidi Petera Mađara, osim tebe, izgubljeni dragi Danasu”, "
     "napisala je ona, uz emotikon.",
     "OBJ",  "P6 — preneti tuđi iskaz"),
    ("pol-759883-066",
     "Tako je bilo i sada.",
     "OBJ",  "P7 — nema sopstvenog stava"),
    ("vre-4970392-008",
     "Štede na svemu – hrani, obući, odjeći, sredstvima za higijenu.",
     "OBJ",  "P3 — književan stil nije ocena"),
    ("vre-4929355-016",
     "Sudska presuda maksimalno je izolirala predsjednika RS.",
     "SUBJ", "P1 — evaluativni epitet"),
    ("vre-4965741-005",
     "Pisci biraju radnju koja je tinejdžerima bliska, a oni imaju dovoljno i čitalačkog i životnog iskustva pa im je ilustrovanje onoga o čemu čitaju nepotrebno.",
     "SUBJ", "P4 — mišljenje u tvrdnoj formi"),
    ("vre-4936342-006",
     "Njegov govor tijela odaje duboko frustriranog čovjeka koji uživa u patnji drugih – žena, djece, mladih i starih osoba.",
     "SUBJ", "P5 — pripisano unutrašnje stanje"),
    ("n1i-413598-013",
     "Ili, ukratko: „Mi napadamo Nepalce, Filipince i Indijce jer su se naselili "
     "ovdje i uzimaju nam posao.“",
     "SUBJ", "P13 — izmišljen navod"),
]
FEWSHOT_IDS = {sid for sid, _, _, _ in FEWSHOT}

TASK = {
"sr": """Klasifikuješ rečenice iz srpskih novinskih tekstova.

Za svaku rečenicu odluči da li je SUBJEKTIVNA ili OBJEKTIVNA:

SUBJ — rečenica iznosi stav, ocenu, doživljaj ili pretpostavku AUTORA teksta.
OBJ  — rečenica iznosi tvrdnju o stvarnosti, prenosi tuđi iskaz, ili ne sadrži
       autorov stav.

Oznaka se odnosi na glas autora teksta, ne na sadržaj rečenice. Rečenica može
biti puna oštrih ocena i svejedno biti OBJ, ako te ocene pripadaju nekome koga
autor citira.

Ne uzimaj u obzir temu rečenice, da li je tvrdnja tačna, niti da li se slažeš
sa autorom.""",

"en": """You are classifying sentences from Serbian news articles.

For each sentence decide whether it is SUBJECTIVE or OBJECTIVE:

SUBJ — the sentence conveys the opinion, evaluation, personal experience or
       speculation of the ARTICLE'S AUTHOR.
OBJ  — the sentence states a fact, reports someone else's statement, or carries
       no stance of the author's own.

The label concerns the author's voice, not the sentence's content. A sentence
full of harsh judgements is still OBJ if those judgements belong to someone the
author is quoting.

Disregard the sentence's topic, whether the claim is true, and whether you
agree with the author.""",
}

FORMAT = {
"sr": """Odgovori isključivo JSON objektom, bez ikakvog dodatnog teksta i bez
markdown oznaka. Ključ je redni broj rečenice kao niska, vrednost je "OBJ" ili
"SUBJ". Za svaku rečenicu iz ulaza mora postojati tačno jedan ključ.

Primer odgovora: {"1": "OBJ", "2": "SUBJ", "3": "OBJ"}""",

"en": """Reply with a JSON object only, with no surrounding text and no markdown
fences. Each key is a sentence number as a string, each value is "OBJ" or
"SUBJ". Every input sentence must have exactly one key.

Example reply: {"1": "OBJ", "2": "SUBJ", "3": "OBJ"}""",
}

EX_HEAD = {"sr": "Primeri:", "en": "Examples:"}
IN_HEAD = {"sr": "Rečenice za klasifikaciju:", "en": "Sentences to classify:"}


def system_prompt(lang="sr", shots="zero"):
    parts = [TASK[lang]]
    if shots == "few":
        ex = "\n".join(f'{i}. "{t}" -> {lab}'
                       for i, (_, t, lab, _) in enumerate(FEWSHOT, 1))
        parts.append(f"{EX_HEAD[lang]}\n{ex}")
    parts.append(FORMAT[lang])
    return "\n\n".join(parts)


def user_prompt(sentences, lang="sr"):
    body = "\n".join(f"{i}. {s}" for i, s in enumerate(sentences, 1))
    return f"{IN_HEAD[lang]}\n{body}"


def config_name(model, lang, shots):
    return f"{model}-{lang}-{shots}"


CONFIGS = [(lang, shots) for lang in ("sr", "en") for shots in ("zero", "few")]
REFERENCE = ("sr", "zero")


if __name__ == "__main__":
    import sys
    lang = sys.argv[1] if len(sys.argv) > 1 else "sr"
    shots = sys.argv[2] if len(sys.argv) > 2 else "zero"
    demo = ["Sednica je počela u 18 časova, saopštila je služba za informisanje.",
            "To je najsramnija odluka koju je ova vlada donela do sada.",
            "Ministar je rekao da će zakon biti povučen iz procedure."]
    print("=" * 70); print(f"SYSTEM  ({lang}, {shots})"); print("=" * 70)
    print(system_prompt(lang, shots))
    print("\n" + "=" * 70); print("USER"); print("=" * 70)
    print(user_prompt(demo, lang))
    print("\n" + "=" * 70)
    print(f"few-shot primeri isključeni iz rezultata: {len(FEWSHOT_IDS)}")
    for sid, _, lab, rule in FEWSHOT:
        print(f"  {lab:4s}  {rule:34s}  {sid}")
