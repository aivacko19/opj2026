
import csv, json, io, os, re, time, pathlib, unicodedata, collections


SEED    = 20260827         
SEED_DP = 20260828          
WINDOW  = 8               
MIN_WIN = 4                 
DELAY   = 2.0              

UA = {"User-Agent": "ETF-NLP-projekat/1.0 (studentski projekat; kontakt: ime@primer.rs)"}

CACHE = pathlib.Path("cache"); CACHE.mkdir(exist_ok=True)
DATA  = pathlib.Path("data");  DATA.mkdir(exist_ok=True)

GENRES = ("kolumna", "vest")
TOPICS = ("pol-drustvo", "svet", "ekonomija", "kultura", "sport", "hronika")

COLS = ["sentence_id", "source", "article_id", "genre", "topic",
        "category", "sent_idx", "n_clean", "url", "text"]


def http_get(url, cache_key=None):
    """GET uz keširanje na disk i pauzu između zahteva.

    Keširanje znači da ponovno pokretanje pipeline-a ne pravi nove zahteve
    prema sajtovima. Obriši cache/ samo ako namerno hoćeš sveže podatke.
    """
    import requests
    key = cache_key or re.sub(r"[^\w.-]", "_", url)[:150]
    f = CACHE / (key + ".html")
    if f.exists():
        return f.read_text(encoding="utf-8")
    r = requests.get(url, headers=UA, timeout=30)
    time.sleep(DELAY)
    r.raise_for_status()
    f.write_text(r.text, encoding="utf-8")
    return r.text


def read_jsonl(path):
    p = pathlib.Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]

def write_jsonl(path, rows):
    with io.open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


TSV = dict(delimiter="\t", quotechar=None, quoting=csv.QUOTE_NONE)

def open_tsv(path):
    """DictReader nad čistim TSV-om. Koristiti umesto csv.DictReader direktno."""
    return csv.DictReader(io.open(path, encoding="utf-8", newline=""), **TSV)

def read_tsv(path):
    return list(open_tsv(path))

def write_tsv(path, rows, cols=None):
    """Čist TSV bez ikakvog escape-ovanja.

    Polja se čiste od tabova i preloma reda, pa navodnici ne moraju da se
    escape-uju. Bez ovoga csv.writer oko polja sa navodnicima dodaje jos jedan
    sloj navodnika, sto je ispravno po CSV standardu ali zbunjuje pri citanju
    fajla i lomi naivne parsere (npr. alat za anotaciju).
    """
    cols = cols or list(rows[0].keys())
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n", **TSV)
        w.writerow(cols)
        for r in rows:
            w.writerow([str(r.get(c, "")).replace("\t", " ").replace("\n", " ")
                        for c in cols])

_nlp = None
def sentences(text):
    """Podela na rečenice alatom CLASSLA (Stanza za južnoslovenske jezike).

    Bira se zbog srpskih specifičnosti: tačka iza rednog broja u datumu
    ('15. januara') i iza skraćenica ('dr.', 'prof.') ne završava rečenicu.
    """
    global _nlp
    if _nlp is None:
        import classla
        _nlp = classla.Pipeline("sr", processors="tokenize", verbose=False)
    return [s.text.strip() for s in _nlp(text).sentences if s.text.strip()]


OPEN, CLOSE, NEUTRAL = "„«", "“”ˮ»", '"'
MARK_L, MARK_R = "„", "“"

def _depths(text):
    """Dubina navoda pre svake pozicije u tekstu.

    Srpski veb tekstovi mešaju znake navoda: „ “ ” ali i običan " i dva
    apostrofa ''. U istoj rečenici se javlja i ''ovako" — otvoreno apostrofima,
    zatvoreno navodnikom. Zato se i '' i " tretiraju kao neutralni znak koji
    prebacuje stanje, umesto da se apostrofi ignorišu.

    Dubina se nulira na kraju pasusa. Navod skoro nikad ne prelazi granicu
    pasusa, a bez toga jedan nezatvoren znak navoda pokvari ceo ostatak članka:
    sve naredne rečenice dobiju in_quote='Y'.
    """
    out = [0] * (len(text) + 1)
    d = i = 0
    while i < len(text):
        out[i] = d
        ch = text[i]
        if ch == "\n":
            d = 0
        elif ch in OPEN:
            d += 1
        elif ch in CLOSE:
            d = max(0, d - 1)
        elif ch == NEUTRAL:
            d = 0 if d else 1
        elif ch == "'" and text[i+1:i+2] == "'":
            d = 0 if d else 1
            i += 1
            out[i] = d
        i += 1
    out[len(text)] = d
    return out


def mark_quotes(rows, context, key=lambda r: r["article_id"]):
    """Označava rečenice koje počinju unutar otvorenog navoda i vraća im navodnike.

    Podela na rečenice uklanja navodnike sa svih rečenica višerečeničnog navoda
    osim prve i poslednje, pa rečenica iz sredine izgleda kao autorov iskaz.
    Bez ovoga bi oznaka zavisila od podatka koji model ne vidi.

    Dodaje kolone: in_quote ('Y' / '' / '?'), text_marked.
    """
    cache, cursor, missing = {}, collections.Counter(), []
    for r in rows:
        k = key(r)
        art = context.get(k)
        if art is None:
            r["in_quote"] = "?"; missing.append(r["sentence_id"]); continue
        if k not in cache:
            cache[k] = _depths(art)
        frag = r["text"][:40]
        pos = art.find(frag, cursor[k])
        if pos < 0:
            pos = art.find(frag)
        if pos < 0:
            r["in_quote"] = "?"; missing.append(r["sentence_id"]); continue
        cursor[k] = pos + 1
        r["in_quote"] = "Y" if cache[k][pos] > 0 else ""

    for r in rows:
        t = r["text"].rstrip()
        if r.get("in_quote") == "Y" and t[0] not in OPEN:
            if t[-1] not in CLOSE and t[-1] != NEUTRAL:
                t += MARK_R
            r["text_marked"] = MARK_L + t
        else:
            r["text_marked"] = r["text"]
    return missing


def cramers_v(pairs):
    """Hi-kvadrat test nezavisnosti i Cramerovo V za listu parova (red, kolona).

    Hi-kvadrat kaže DA LI su dve kategorijske promenljive povezane; raste sa
    veličinom uzorka. Cramerovo V kaže KOLIKO su povezane, na skali 0-1, i
    uporedivo je između skupova različite veličine. Ispod 0.1 je zanemarljivo.
    """
    rs = sorted({a for a, _ in pairs}); cs = sorted({b for _, b in pairs})
    tab = [[sum(1 for p in pairs if p == (r, c)) for c in cs] for r in rs]
    n = sum(map(sum, tab))
    if n == 0 or len(rs) < 2 or len(cs) < 2:
        return 0.0, 0, 0.0, (rs, cs, tab)
    rt = [sum(row) for row in tab]; ct = [sum(col) for col in zip(*tab)]
    chi2 = sum((tab[i][j] - rt[i]*ct[j]/n) ** 2 / (rt[i]*ct[j]/n)
               for i in range(len(rs)) for j in range(len(cs)) if rt[i]*ct[j])
    dof = (len(rs) - 1) * (len(cs) - 1)
    v = (chi2 / (n * min(len(rs) - 1, len(cs) - 1))) ** 0.5
    return chi2, dof, v, (rs, cs, tab)

def balance(rows, label=""):
    """Provera da li tema ili izvor predviđaju žanr. Radi se na nivou članka."""
    arts = {(r["source"], r["article_id"]): r for r in rows}.values()
    print(f"\n  {label}{len(rows)} rečenica iz {len(arts)} članaka")
    for name, prs in [("tema x žanr",  [(r["topic"],  r["genre"]) for r in arts]),
                      ("izvor x žanr", [(r["source"], r["genre"]) for r in arts])]:
        chi2, dof, v, _ = cramers_v(prs)
        flag = "" if v < 0.15 else "   <-- PROVERITI"
        print(f"    {name:14s} chi2({dof})={chi2:6.2f}  V={v:.3f}{flag}")

def counts(rows, *fields):
    for f in fields:
        print(f"\n  {f}:")
        for k, v in sorted(collections.Counter(r[f] for r in rows).items(),
                           key=lambda kv: -kv[1]):
            print(f"    {v:6d}  {k or '(prazno)'}")

def norm(s):
    """Normalizacija za deduplikaciju: mala slova, bez dijakritike i interpunkcije."""
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", "", re.sub(r"\s+", " ", s)).strip()
