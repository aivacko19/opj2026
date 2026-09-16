import re, glob, gzip, hashlib, argparse, collections, pathlib
import common as C

BASE = "https://www.danas.rs"
SNAP = C.DATA / "snapshots" / "danas"
FIRST_POST_SITEMAP = 698        

CATS = {
    "vesti/politika":              ("vest",    "pol-drustvo"),
    "vesti/politika/izbori26":     ("vest",    "pol-drustvo"),
    "vesti/drustvo":               ("vest",    "pol-drustvo"),
    "vesti/drustvo/suocavanje":    ("vest",    "pol-drustvo"),
    "vesti/drustvo/vladavina-prava": ("vest",  "pol-drustvo"),
    "vesti/drustvo/druga-strana-kosova": ("vest", "pol-drustvo"),
    "vesti/beograd":               ("vest",    "pol-drustvo"),
    "vesti/klimatske-promene":     ("vest",    "pol-drustvo"),
    "vesti/ekonomija":             ("vest",    "ekonomija"),
    "svet":                        ("vest",    "svet"),
    "svet/region":                 ("vest",    "svet"),
    "sport":                       ("vest",    "sport"),
    "sport/eurobasket-2025":       ("vest",    "sport"),
    "kultura":                     ("?",       "kultura"),   
    "kultura/scena":               ("?",       "kultura"),
    "kolumna":                     ("kolumna", None),       
    "dijalog":                     ("kolumna", None),        
    "dijalog/licni-stavovi":       ("kolumna", None),
    "dijalog/redakcijski-komentar": ("kolumna", None),
}

SKIP_TOP = ("zivot", "podkast")                       
SKIP = ("vesti", "dijalog/pisma-citalaca", "dijalog/feljton", "dijalog/reakcije",
        "vesti/drustvo/doniraj-danas")

def article_id(path):
    """Deterministički numerički ID iz putanje (WordPress ID nije u URL-u)."""
    return str(int(hashlib.sha1(path.encode("utf-8")).hexdigest()[:10], 16))

def classify(url):
    """(putanja rubrike, slug) ili None ako URL nije članak iz posmatranih rubrika."""
    path = url.replace(BASE, "").strip("/")
    segs = path.split("/")
    if len(segs) < 2:
        return None
    if segs[0] in SKIP_TOP:
        return segs[0], segs[-1]
    if segs[0] == "kolumna":                          
        return ("kolumna", segs[-1]) if len(segs) == 3 else None
    for k in range(len(segs) - 1, 0, -1):            
        cat = "/".join(segs[:k])
        if cat in CATS or cat in SKIP:
            return (cat, segs[-1]) if k == len(segs) - 1 else None
    return None

def parse(xml_text):
    """Redovi (url, lastmod) iz jedne mape; tip mape se ne razlikuje."""
    return re.findall(r"<url>\s*<loc>(.*?)</loc>(?:\s*<lastmod>(.*?)</lastmod>)?", xml_text)

def read_xml(path):
    """Mapa sajta, čuva se gzip-ovana (data/snapshots/*/*.xml.gz)."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return f.read()

def rows_from(files, since):
    out, skipped = {}, collections.Counter()
    for f in files:
        for url, mod in parse(read_xml(f)):
            c = classify(url)
            if not c:
                skipped["nepoznata rubrika"] += 1; continue
            cat, slug = c
            if cat in SKIP or cat in SKIP_TOP:
                skipped[cat] += 1; continue
            date = mod[:10]
            if date < since:
                skipped["pre " + since] += 1; continue
            genre, topic = CATS[cat]
            path = url.replace(BASE, "")
            out[path] = dict(source="danas", article_id=article_id(path), url=url,
                             genre=genre, topic=topic, category=cat.split("/")[-1],
                             date=date, title=slug.replace("-", " ").capitalize())
    return list(out.values()), skipped

def fetch_snapshots():
    """Preuzima kolumna-sitemap*.xml i post-sitemap<N>.xml (N >= 698) u SNAP."""
    import requests, time
    SNAP.mkdir(parents=True, exist_ok=True)
    r = requests.get(f"{BASE}/sitemap.xml", headers=C.UA, timeout=30); r.raise_for_status()
    names = re.findall(r"<loc>%s/((?:kolumna|post)-sitemap\d*\.xml)</loc>" % re.escape(BASE), r.text)
    want = []
    for n in names:
        m = re.match(r"post-sitemap(\d*)\.xml", n)
        if m and int(m.group(1) or 0) < FIRST_POST_SITEMAP:
            continue
        want.append(n)
    print(f"  mapa u indeksu: {len(want)} (kolumna-* i post-* od {FIRST_POST_SITEMAP})")
    for n in sorted(want):
        f = SNAP / (n + ".gz")
        if f.exists():
            continue
        r = requests.get(f"{BASE}/{n}", headers=C.UA, timeout=60)
        time.sleep(C.DELAY)
        if r.status_code != 200:
            print(f"    {n}: HTTP {r.status_code}"); continue
        if "<url>" not in r.text:                 
            print(f"    {n}: prazna, preskačem"); continue
        with gzip.open(f, "wt", encoding="utf-8") as out:
            out.write(r.text)
        print(f"    {n}: {r.text.count('<url>')} url")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="preuzmi mape sajta u data/snapshots/danas/")
    ap.add_argument("--since", default="2025-06-01", help="najstariji datum (lastmod) koji se uzima")
    a = ap.parse_args()

    if a.fetch:
        fetch_snapshots()
    files = sorted(glob.glob(str(SNAP / "*.xml*")))
    if not files:
        raise SystemExit(f"nema mapa u {SNAP} — pokreni sa --fetch")
    new, skipped = rows_from(files, a.since)
    print(f"  {len(files)} mapa, {len(new)} članaka od {a.since}")
    for k, v in skipped.most_common():
        print(f"    preskočeno {v:6d}  {k}")

    ids = collections.Counter(r["article_id"] for r in new)
    dup = [k for k, v in ids.items() if v > 1]
    if dup:
        raise SystemExit(f"KOLIZIJA article_id: {dup[:5]} — povećaj broj cifara heša")

    path = C.DATA / "inventory.jsonl"
    merged = {(r["source"], r["article_id"]): r for r in C.read_jsonl(path)}
    added = sum(1 for r in new
                if merged.setdefault((r["source"], r["article_id"]), r) is r)
    C.write_jsonl(path, list(merged.values()))

    print(f"\n  novih: {added}   ukupno u inventaru: {len(merged)}")
    dan = [r for r in merged.values() if r["source"] == "danas"]
    for k, v in sorted(collections.Counter(
            (r["genre"], r["topic"], r["category"]) for r in dan).items(),
            key=lambda kv: tuple(map(str, kv[0]))):
        print(f"    {v:5d}  {k}")

if __name__ == "__main__":
    main()
