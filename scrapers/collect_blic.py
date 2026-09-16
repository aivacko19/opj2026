"""
Pokretanje:
    python3 collect_blic.py --fetch --since 2025-06     
    python3 collect_blic.py                            
"""

import re, glob, gzip, argparse, collections, datetime
import common as C

BASE = "https://www.blic.rs"
SNAP = C.DATA / "snapshots" / "blic"

CATS = {
    "vesti/politika":         ("vest", "pol-drustvo"),
    "vesti/drustvo":          ("vest", "pol-drustvo"),
    "vesti/beograd":          ("vest", "pol-drustvo"),
    "vesti/hronika":          ("vest", "hronika"),
    "vesti/svet":             ("vest", "svet"),
    "vesti/republika-srpska": ("vest", "svet"),
    "biznis/vesti":           ("vest", "ekonomija"),
    "biznis/privreda":        ("vest", "ekonomija"),
    "kultura":                ("vest", "kultura"),
}

OPED = re.compile(r"^[a-z]+-[a-z]+-(pise-za-blic|kolumna)-")
URL_RE = re.compile(r"^%s/(.+)/([0-9a-z]{7})$" % re.escape(BASE))

def classify(url):
    """(rubrika, slug, id) ili None ako URL nije članak iz posmatranih rubrika."""
    m = URL_RE.match(url)
    if not m:
        return None
    segs, sid = m.group(1).split("/"), m.group(2)
    for k in (2, 1):                                   
        cat = "/".join(segs[:k])
        if cat in CATS and len(segs) == k + 1:
            return cat, segs[-1], sid
    return None

def parse(xml_text):
    return re.findall(r"<url><loc>(.*?)</loc><lastmod>(.*?)</lastmod>", xml_text)

def read_xml(path):
    """Mapa sajta, čuva se gzip-ovana (data/snapshots/*/*.xml.gz)."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return f.read()

def rows_from(files):
    out, skipped = {}, collections.Counter()
    for f in files:
        for url, mod in parse(read_xml(f)):
            c = classify(url)
            if not c:
                skipped[url.replace(BASE + "/", "").split("/")[0]] += 1; continue
            cat, slug, sid = c
            genre, topic = CATS[cat]
            if cat == "vesti/politika" and OPED.match(slug):
                genre, topic = "kolumna", None
            category = "biznis" if cat == "biznis/vesti" else cat.split("/")[-1]
            out[sid] = dict(source="blic", article_id=str(int(sid, 36)), url=url,
                            genre=genre, topic=topic, category=category,
                            date=mod[:10], title=slug.replace("-", " ").capitalize())
    return list(out.values()), skipped

def fetch_snapshots(since):
    """Preuzima mesečne mape od `since` (GGGG-MM) do tekućeg meseca u SNAP."""
    import requests, time
    SNAP.mkdir(parents=True, exist_ok=True)
    y, m = map(int, since.split("-"))
    today = datetime.date.today()
    while (y, m) <= (today.year, today.month):
        name = f"sitemap-stories-by-month-{y}-{m}.xml"
        f = SNAP / (name + ".gz")
        if not f.exists():
            r = requests.get(f"{BASE}/{name}.gz", headers=C.UA, timeout=90)
            time.sleep(C.DELAY)
            if r.status_code != 200:
                print(f"    {name}: HTTP {r.status_code}")
            else:
                raw = r.content                    
                text = (gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8")
                with gzip.open(f, "wt", encoding="utf-8") as out:
                    out.write(text)
                print(f"    {name}: {text.count('<url>')} url")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="preuzmi mesečne mape u data/snapshots/blic/")
    ap.add_argument("--since", default="2025-06", help="prvi mesec (GGGG-MM) za --fetch")
    a = ap.parse_args()

    if a.fetch:
        fetch_snapshots(a.since)
    files = sorted(glob.glob(str(SNAP / "*.xml*")))
    if not files:
        raise SystemExit(f"nema mapa u {SNAP} — pokreni sa --fetch")
    new, skipped = rows_from(files)
    print(f"  {len(files)} mapa, {len(new)} članaka iz posmatranih rubrika")
    for k, v in skipped.most_common(12):
        print(f"    preskočeno {v:6d}  {k}")

    path = C.DATA / "inventory.jsonl"
    merged = {(r["source"], r["article_id"]): r for r in C.read_jsonl(path)}
    added = sum(1 for r in new
                if merged.setdefault((r["source"], r["article_id"]), r) is r)
    C.write_jsonl(path, list(merged.values()))

    print(f"\n  novih: {added}   ukupno u inventaru: {len(merged)}")
    bli = [r for r in merged.values() if r["source"] == "blic"]
    for k, v in sorted(collections.Counter(
            (r["genre"], r["topic"], r["category"]) for r in bli).items(),
            key=lambda kv: tuple(map(str, kv[0]))):
        print(f"    {v:5d}  {k}")

if __name__ == "__main__":
    main()
