import re, time, argparse, collections, requests
import common as C

API = "https://vreme.com/wp-json/wp/v2"

CATS = {
    "komentar":  ("kolumna", None),
    "vesti":     ("vest",    None),
    "svet":      ("vest",    "svet"),
    "drustvo":   ("vest",    "pol-drustvo"),
    "ekonomija": ("vest",    "ekonomija"),
    "sport":     ("vest",    "sport"),
    "kultura":   ("?",       "kultura"),
    "mozaik":    ("?",       None),
}

def fetch(after, max_pages=10):
    cats = {c["id"]: c["slug"] for c in requests.get(
        f"{API}/categories", params={"per_page": 100, "_fields": "id,slug"},
        headers=C.UA, timeout=30).json()}
    out = {}
    for cid, slug in cats.items():
        if slug not in CATS:
            continue
        got = 0
        for page in range(1, max_pages + 1):
            r = requests.get(f"{API}/posts", headers=C.UA, timeout=30, params={
                "categories": cid, "per_page": 100, "page": page, "after": after,
                "_fields": "id,link,date,title,categories"})
            time.sleep(1)
            if r.status_code != 200 or not r.json():
                break
            for p in r.json():
                slugs = [cats.get(c, str(c)) for c in p["categories"]]
                main = next((s for s in slugs if s in CATS), slug)
                g, t = CATS[main]
                out[str(p["id"])] = dict(
                    source="vreme", article_id=str(p["id"]), url=p["link"],
                    genre=g, topic=t, category=main, date=p["date"],
                    title=re.sub("<[^>]+>", "", p["title"]["rendered"]))
                got += 1
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                break
        print(f"  {slug}: {got}")
    return list(out.values())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--after", default="2025-06-01T00:00:00")
    a = ap.parse_args()

    new = fetch(a.after)
    path = C.DATA / "inventory.jsonl"
    merged = {(r["source"], r["article_id"]): r for r in C.read_jsonl(path)}
    added = sum(1 for r in new
                if merged.setdefault((r["source"], r["article_id"]), r) is r)
    C.write_jsonl(path, list(merged.values()))

    print(f"\n  novih: {added}   ukupno u inventaru: {len(merged)}")
    vre = [r for r in merged.values() if r["source"] == "vreme"]
    for k, v in sorted(collections.Counter(
            (r["genre"], r["topic"]) for r in vre).items(),
            key=lambda kv: tuple(map(str, kv[0]))):
        print(f"    {v:5d}  {k}")

if __name__ == "__main__":
    main()
