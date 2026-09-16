
import random, argparse, collections, pathlib
import common as C


OPINION = [("politika", "pogledi",  40),
           ("vreme",    "komentar", 28),
           ("vreme",    "kultura",  24),
           ("vreme",    "mozaik",   16)]
MIXED = {("vreme", "kultura"), ("vreme", "mozaik")} 

def load_inventory():
    rows = C.read_jsonl(C.DATA / "inventory.jsonl")
    if not rows:
        raise SystemExit("data/inventory.jsonl je prazan — pokreni collect_* skripte")
    return rows

def spread(rows, n, rng):
    """Ravnomerno kroz vreme: podeli na 4 intervala i iz svakog uzmi jednako.

    Sprečava da korpus bude uzorak jednog kratkog perioda i jednog vesti-ciklusa.
    """
    key = lambda r: (r.get("date") or "") if r["source"] == "vreme" else int(r["article_id"])
    rows, out = sorted(rows, key=key), []
    for i in range(4):
        chunk = rows[i*len(rows)//4:(i+1)*len(rows)//4]
        take = n // 4 + (1 if i < n % 4 else 0)
        out += rng.sample(chunk, min(len(chunk), take))
    return out

def norm_rows(rows):
    """Popravlja redove kojima je pri ručnoj izmeni nestao tabulator."""
    for r in rows:
        g = r["genre"].strip()
        if " " in g:
            r["genre"], r["topic"] = g.split()[0], g.split()[1]
        r["genre"] = r["genre"].strip()
        r["topic"] = r["topic"].strip()
    return rows

def stage_candidates():
    inv, rng = load_inventory(), random.Random(C.SEED)
    out = []
    for src, cat, n in OPINION:
        pool = [r for r in inv if r["source"] == src and r["category"] == cat]
        if not pool:
            print(f"  UPOZORENJE: nema članaka za {src}/{cat}")
            continue
        out += spread(pool, n, rng)
    C.write_tsv("opinion_candidates.tsv", out,
                ["source", "article_id", "category", "genre", "topic", "title", "url"])
    print(f"\n{len(out)} kandidata -> opinion_candidates.tsv")
    print("RUČNO: dopuni prazne genre i topic, pa pokreni:  python3 sample.py news")


def stage_news(n_news):
    inv, rng = load_inventory(), random.Random(C.SEED)
    op = [r for r in norm_rows(C.read_tsv("opinion_candidates.tsv"))
          if r["genre"] == "kolumna"]
    if not op:
        raise SystemExit("opinion_candidates.tsv nije dopunjen")

    mix = collections.Counter(r["topic"] for r in op)
    tot = sum(mix.values())
    quota = {t: max(1, round(v / tot * n_news)) for t, v in mix.items()}
    print(f"\n  {len(op)} kolumni, raspodela tema koju vesti treba da preslikaju:")
    for t, v in mix.most_common():
        print(f"    {t:12s} {v:3d} ({v/tot:5.1%})  ->  {quota[t]:2d} vesti")

    used = {(r["source"], r["article_id"]) for r in C.read_tsv("opinion_candidates.tsv")}
    picked, check = [], set()
    for topic, need in quota.items():
        per = {"politika": need // 2 + need % 2, "vreme": need // 2}
        for src, k in per.items():
            if not k:
                continue
            if (src, topic) == ("vreme", "kultura"): 
                pool = [r for r in inv if r["source"] == "vreme"
                        and r["category"] in ("kultura", "mozaik")
                        and (r["source"], r["article_id"]) not in used]
                got = spread(pool, k * 3, rng)
                check |= {(g["source"], g["article_id"]) for g in got}
            else:
                pool = [r for r in inv if r["source"] == src and r["genre"] == "vest"
                        and r["topic"] == topic
                        and (r["source"], r["article_id"]) not in used]
                got = spread(pool, k, rng)
            if len(got) < k:
                print(f"    NEDOVOLJNO {src}/{topic}: {len(got)}/{k}")
            picked += [dict(g, topic=topic, genre="vest") for g in got]

    for r in picked:
        r["check"] = "Y" if (r["source"], r["article_id"]) in check else ""
    C.write_tsv("news_candidates.tsv", picked,
                ["source", "article_id", "category", "genre", "topic",
                 "title", "url", "check"])
    print(f"\n{len(picked)} vesti -> news_candidates.tsv  ({len(check)} za ručnu proveru)")
    print("RUČNO: kod redova sa check=Y obriši one koji nisu izveštajni tekst.")
    print("Zatim:  python3 build.py")


def stage_discovery(n):
    rows = C.read_tsv("to_annotate.tsv")
    rng = random.Random(C.SEED_DP)
    cells = collections.Counter((r["genre"], r["topic"]) for r in rows)
    tot = sum(cells.values())
    raw = {k: v / tot * n for k, v in cells.items()}
    quota = {k: int(v) for k, v in raw.items()}
    for k, _ in sorted(raw.items(), key=lambda kv: -(kv[1] - int(kv[1])))[
            :n - sum(quota.values())]:
        quota[k] += 1

    pool = rows[:]; rng.shuffle(pool)
    left, per_art, picked = dict(quota), collections.Counter(), []
    for r in pool:
        k = (r["genre"], r["topic"])
        if left.get(k, 0) <= 0 or per_art[r["article_id"]] >= 2:
            continue
        picked.append(r); per_art[r["article_id"]] += 1; left[k] -= 1

    idx = {(r["article_id"], int(r["sent_idx"])): r["text"] for r in rows}
    nb = lambda r, o: idx.get((r["article_id"], int(r["sent_idx"]) + o), "")
    C.write_tsv("discovery_pass.tsv", [
        dict(sentence_id=r["sentence_id"], genre=r["genre"], topic=r["topic"],
             is_question="Y" if r["text"].rstrip().endswith("?") else "",
             prev=nb(r, -1), text=r["text"], next=nb(r, +1),
             label="", hard="", note="") for r in picked])
    pathlib.Path("discovery_ids.txt").write_text(
        "\n".join(r["sentence_id"] for r in picked) + "\n", encoding="utf-8")
    print(f"\n{len(picked)} rečenica iz {len(per_art)} članaka -> discovery_pass.tsv")
    print("Označi label, pa 'hard' gde si oklevao i 'note' ZAŠTO je bilo teško.")
    print("discovery_ids.txt čuvaj — te rečenice se izuzimaju iz kalibracije.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["candidates", "news", "discovery"])
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    if   a.stage == "candidates": stage_candidates()
    elif a.stage == "news":       stage_news(a.n or 54)
    else:                         stage_discovery(a.n or 70)
