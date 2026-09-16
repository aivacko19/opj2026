#!/usr/bin/env python3
"""
build.py — od izabranih članaka do skupa rečenica za anotaciju.

Redom:
  1. preuzimanje izabranih članaka (keširano, uz pauzu iz common.DELAY)
  2. izdvajanje teksta (trafilatura, favor_precision) i podela na rečenice (CLASSLA)
  3. uklanjanje sadržaja koji nije deo članka
  4. izrez prozora od 8 uzastopnih rečenica sa slučajnim početkom
  5. vraćanje navodnika u rečenicama iz sredine višerečeničnog navoda
  6. izlazi: to_annotate.tsv, context.json, clanci/*.txt, clanci_metapodaci.tsv

O koraku 3. Ni uz favor_precision ekstrakcija ne uklanja sve. Dve vrste smeća:

  - okvir sajta (poziv na donaciju, pretplata, ograda redakcije, potpis autora)
  - najave DRUGIH tekstova iz sajdbara

Druga vrsta je opasnija: to su normalne novinarske rečenice, često izrazito
subjektivne, koje se pojavljuju u 10 do 23 različita članka. Da ostanu, iste
rečenice bi se našle u više slojeva unakrsne validacije i podigle sve rezultate.

Otkrivaju se učestalošću: rečenica u 3+ članka je gotovo sigurno smeće. Za
sajdbar koji se javlja u samo jednom članku učestalost ne pomaže, pa se dodatno
odseca sve od prve takve rečenice u DRUGOJ POLOVINI članka nadalje — sajdbar u
HTML-u dolazi posle teksta. Prag 'druga polovina' sprečava da okvir na vrhu
strane odseče ceo članak. Minimalna dužina od 30 znakova štiti kratke rečenice
koje se legitimno ponavljaju ('Naprotiv.').

O koraku 4. Prozor od 8 daje svakom članku istu težinu (kolumne imaju medijalno
49 rečenica, vesti 23) i smanjuje curenje između slojeva validacije. Slučajan
početak je bitan jer kolumne počinju činjeničnim uvodom a stav dolazi kasnije;
uzimanje prvih 8 sistematski bi favorizovalo objektivne delove.

Pokretanje:
    python3 build.py
    python3 build.py --show-boilerplate    # pregled liste pre primene
"""

import re, io, json, random, argparse, collections, pathlib
import trafilatura
import common as C

# ugrađeni vidžeti i preneti sadržaj koji ekstrakcija ostavi u tekstu
EMBED = re.compile(r"(A post shared by|View this post|Pogledajte ovu objavu"
                   r"|Sledeći video|Prati nas na|Podeli ovu vest)", re.I)

# otvarajući navodnici — legitimni počeci rečenice
OPENERS = "„«\"'“”"

# crta + malo slovo: atribucija dijaloga ("- pitao je onaj čiča."), nikada
# početak rečenice. Delilac je odvaja od upravnog govora jer se taj završava
# upitnikom ili uzvičnikom, pa je ovde treba vratiti nazad.
ATTRIB = re.compile(r"^\s*[-–—]\s*(\w)", re.UNICODE)


def rejoin_dialogue(sents):
    """Vraća atribuciju dijaloga na prethodnu rečenicu.

    '-Kako ... viša sila?' + '- pitao je onaj čiča.'
        -> '-Kako ... viša sila? - pitao je onaj čiča.'
    """
    out = []
    for s in sents:
        m = ATTRIB.match(s)
        if out and m and m.group(1).islower():
            out[-1] = out[-1].rstrip() + " " + s.lstrip()
        else:
            out.append(s)
    return out

def fragment(s):
    """Ostatak pogrešne podele na rečenice, a ne prava rečenica.

    Tri obrasca: počinje malim slovom (nastavak prethodne rečenice, npr.
    'godine legalizovao abortus...' posle podele na '1973.'), počinje
    zagradom ili zarezom, ili je pretežno cifre i interpunkcija.
    """
    t = s.lstrip()
    if not t:
        return True
    if t[0] in "(),;:":
        return True
    # posle rejoin_dialogue ovde ostaju samo atribucije bez svoje rečenice
    # (npr. kada je upravni govor otpao kao boilerplate) — one su ostatak
    core = t.lstrip(OPENERS + "-–— ")
    if core and core[0].isalpha() and core[0].islower():
        return True
    letters = sum(c.isalpha() for c in t)
    return letters < len(t) * 0.5


CHROME = re.compile(r"(Vidi sve|Podržite nas|Pravo novinarstvo košta|odaberite pretplatu"
                    r"|njuzleter|Međuvreme stiže|pretplat|popust na|digitalno izdanje"
                    r"|Arhiva nedeljnika|PDF format|odražavaju stavove autora"
                    r"|^Izvor:|^\*|^Foto|^FOTO)", re.I)

def selected():
    """Kolumne iz opinion_candidates.tsv + vesti iz news_candidates.tsv."""
    op = [r for r in C.read_tsv("opinion_candidates.tsv")]
    for r in op:                                   # popravi ručne izmene
        g = r["genre"].strip()
        if " " in g:
            r["genre"], r["topic"] = g.split()[0], g.split()[1]
        r["genre"], r["topic"] = r["genre"].strip(), r["topic"].strip()
    op = [r for r in op if r["genre"] == "kolumna"]
    nw = C.read_tsv("news_candidates.tsv")
    bad = [r for r in op + nw
           if r["genre"] not in C.GENRES or r["topic"] not in C.TOPICS]
    if bad:
        raise SystemExit("neispravan genre/topic u %d redova, npr. %s"
                         % (len(bad), bad[0]))
    return op + nw

def fetch_all(arts):
    docs, fails = [], []
    for i, a in enumerate(arts, 1):
        try:
            html = C.http_get(a["url"], f"{a['source']}_{a['article_id']}")
        except Exception as e:
            fails.append((a["url"], repr(e)[:60])); continue
        text = trafilatura.extract(html, favor_precision=True,
                                   include_comments=False, include_tables=False)
        if not text or len(text) < 300:
            fails.append((a["url"], f"ekstrakcija={len(text or '')}")); continue
        docs.append(dict(a, text=text, sents=rejoin_dialogue(C.sentences(text))))
        if i % 25 == 0:
            print(f"    {i}/{len(arts)}")
    return docs, fails

def docs_from_context(tsv_path, ctx_path):
    """Rekonstruiše članke iz tuđeg to_annotate fajla i njegovog context.json.

    Koristi se kada je član tima koristio drugi delilac rečenica, pa se ceo
    korak podele i čišćenja radi ponovo, istim kodom kao kod ostalih. Tekst
    članaka je u context.json, pa nema novih zahteva prema sajtu — ponovo se
    radi samo obrada, ne prikupljanje.
    """
    ctx = json.load(io.open(ctx_path, encoding="utf-8"))
    meta = {}
    for r in C.read_tsv(tsv_path):
        meta.setdefault(r["article_id"], r)          # prvi red nosi metapodatke
    docs, missing = [], []
    for aid, r in meta.items():
        text = ctx.get(aid)
        if not text:
            missing.append(aid); continue
        docs.append(dict(source=r["source"], article_id=aid, url=r["url"],
                         genre=r["genre"], topic=r["topic"],
                         category=r["category"], title=r.get("title", ""),
                         text=text, sents=rejoin_dialogue(C.sentences(text))))
    if missing:
        print(f"  UPOZORENJE: {len(missing)} članaka bez teksta u context.json: "
              f"{missing[:5]}")
    return docs, []


def blocklist(docs):
    freq = collections.Counter(s for d in docs for s in set(d["sents"]))
    return {s for s, n in freq.items() if n >= 3 and len(s) >= 30}, freq

def clean(sents, block):
    """Uklanja sadržaj koji nije deo članka i vraća upotrebljive rečenice.

    Dve vrste smeća se tretiraju različito:

      okvir sajta (lista po učestalosti + CHROME) dolazi POSLE teksta, pa prva
      takva rečenica u drugoj polovini članka označava kraj tela i sve od nje
      nadalje se odbacuje;

      ugrađeni vidžeti (EMBED) i ostaci pogrešne podele (fragment) javljaju se
      i USRED teksta, pa se uklanjaju pojedinačno. Da i oni prekidaju članak,
      jedan Instagram umetak bi odsekao ostatak teksta.
    """
    furniture = lambda s: s in block or CHROME.search(s)
    half = len(sents) // 2
    cut = next((i for i, s in enumerate(sents) if i >= half and furniture(s)),
               len(sents))
    out = []
    for s in sents[:cut]:
        if s.lstrip()[:2] in ("„ ", "“ ", '" '):      # siroči navodnik na početku
            s = s.lstrip("„“”\"' ").rstrip()
        if furniture(s) or EMBED.search(s) or fragment(s):
            continue
        if 5 <= len(s.split()) <= 50 and s[-1] in '.?!"”’)':
            out.append(s)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show-boilerplate", action="store_true")
    ap.add_argument("--from-context", nargs=2, metavar=("TSV", "CONTEXT"),
                    help="ponovna obrada tuđeg fajla iz njegovog context.json")
    ap.add_argument("--out", default="to_annotate.tsv")
    a = ap.parse_args()

    if a.from_context:
        print(f"ponovna obrada: {a.from_context[0]}")
        docs, fails = docs_from_context(*a.from_context)
    else:
        arts = selected()
        print(f"{len(arts)} izabranih članaka")
        docs, fails = fetch_all(arts)
    print(f"  članaka {len(docs)}, neuspešno {len(fails)}")
    for u, e in fails[:10]:
        print(f"    GREŠKA {e}  {u}")

    block, freq = blocklist(docs)
    print(f"\n  lista za uklanjanje: {len(block)} rečenica u 3+ članaka")
    if a.show_boilerplate:
        for s, n in freq.most_common(80):
            if n > 2:
                print(f"    {n:4d} | {s[:95]}")
        return

    rng = random.Random(C.SEED)
    seen, rows, short = set(), [], []
    for d in docs:
        c = [s for s in clean(d["sents"], block) if s not in seen]
        seen.update(c)
        if len(c) < C.MIN_WIN:
            short.append((len(c), d["url"])); continue
        n = min(C.WINDOW, len(c))
        start = rng.randrange(0, len(c) - n + 1)
        for j in range(start, start + n):
            rows.append({"sentence_id": f"{d['source'][:3]}-{d['article_id']}-{j:03d}",
                         "source": d["source"], "article_id": d["article_id"],
                         "genre": d["genre"], "topic": d["topic"],
                         "category": d["category"], "sent_idx": j,
                         "n_clean": len(c), "url": d["url"], "text": c[j]})

    context = {d["article_id"]: d["text"] for d in docs}
    missing = C.mark_quotes(rows, context)
    nq = sum(1 for r in rows if r["in_quote"] == "Y")

    C.write_tsv(a.out, rows, C.COLS + ["in_quote", "text_marked"])
    ctx_out = a.out.replace("to_annotate", "context").replace(".tsv", ".json")
    json.dump(context, io.open(ctx_out, "w", encoding="utf-8"), ensure_ascii=False)

    if a.from_context:                       # izlazi faze 1 već postoje kod autora
        print(f"\n-> {a.out}, {ctx_out}")
        return
    out = pathlib.Path("clanci"); out.mkdir(exist_ok=True)   # obavezan izlaz faze 1
    meta = []
    for d in docs:
        name = f"{d['source'][:3]}-{d['article_id']}.txt"
        (out / name).write_text(d["text"], encoding="utf-8")
        meta.append(dict(file=name, source=d["source"], article_id=d["article_id"],
                         genre=d["genre"], topic=d["topic"], category=d["category"],
                         url=d["url"], title=d["title"], n_sents=len(d["sents"])))
    C.write_tsv("clanci_metapodaci.tsv", meta)

    print(f"\n{len(rows)} rečenica iz {len({r['article_id'] for r in rows})} članaka")
    if short:
        print(f"  odbačeno kao prekratko: {short}")
    print(f"  unutar navoda: {nq} ({nq/len(rows):.1%})" +
          (f"   nespojeno: {len(missing)}" if missing else ""))
    C.counts(rows, "source", "genre", "topic")
    C.balance(rows)
    tok = sorted(len(r["text"].split()) for r in rows)
    print(f"\n  dužina rečenice: min {tok[0]}  medijana {tok[len(tok)//2]}  max {tok[-1]}")
    print("\n-> to_annotate.tsv, context.json, clanci/, clanci_metapodaci.tsv")

if __name__ == "__main__":
    main()
