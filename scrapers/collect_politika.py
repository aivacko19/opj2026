import re, sys, argparse, collections
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import common as C

BASE = "https://www.politika.rs"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9",
      "n": "http://www.google.com/schemas/sitemap-news/0.9"}


ARCHIVES = {1: "svet", 2: "politika", 3: "drustvo", 4: "pogledi", 5: "hronika",
            6: "ekonomija", 7: "kultura", 8: "sport", 9: "srbija", 10: "beograd"}


TOPIC = {"svet": "svet", "region": "svet", "politika": "pol-drustvo",
         "drustvo": "pol-drustvo", "srbija": "pol-drustvo", "beograd": "pol-drustvo",
         "zdravlje": "pol-drustvo", "ekonomija": "ekonomija", "kultura": "kultura",
         "spektar": "kultura", "fudbal": "sport", "kosarka": "sport",
         "tenis": "sport", "odbojka": "sport", "rukomet": "sport",
         "ostali sportovi": "sport", "hronika": "hronika", "pogledi": None}

def latin(url):
    return url.replace("/scc/", "/sr/", 1)

def article_id(url):
    m = re.search(r"/clanak/(\d+)/", url)
    return m.group(1) if m else None

def from_sitemap(xml_text):
    """Vesti iz Google News mape sajta."""
    out = []
    for u in ET.fromstring(xml_text.encode("utf-8")).findall("s:url", NS):
        url = latin(u.findtext("s:loc", namespaces=NS) or "")
        aid = article_id(url)
        if not aid:
            continue
        rub = ((u.findtext(".//n:keywords", namespaces=NS) or "").split(",")[0]).strip()
        out.append(dict(source="politika", article_id=aid, url=url,
                        genre="vest", category=rub.lower(),
                        topic=TOPIC.get(rub.lower()),
                        date=u.findtext(".//n:publication_date", namespaces=NS),
                        title=u.findtext(".//n:title", namespaces=NS)))
    return out

def from_archive(n, max_pages=15):
    """Članci iz arhive rubrike N. Veze su oblika /sr/clanak/<id>/<slug>."""
    rub, out = ARCHIVES[n], {}
    for page in range(1, max_pages + 1):
        url = (f"{BASE}/sr/columns/archive/{n}" if page == 1
               else f"{BASE}/sr/columns/archive/{n}/page:{page}?url=")
        soup = BeautifulSoup(C.http_get(url, f"pol_arch{n}_p{page}"), "html.parser")
        found = {}
        for a in soup.find_all("a", href=True):
            href = a["href"].split("#")[0]
            aid = article_id(href)
            if not aid or not href.startswith("/sr/clanak/"):
                continue
            t = a.get_text(" ", strip=True)
            if len(t) > len(found.get(aid, ("",))[0]):
                found[aid] = (t, BASE + href)
        new = {k: v for k, v in found.items() if k not in out}
        if not new:
            break
        for aid, (title, href) in new.items():
            out[aid] = dict(source="politika", article_id=aid, url=href,
                            genre="kolumna" if rub == "pogledi" else "vest",
                            category=rub, topic=TOPIC[rub], date=None, title=title)
    return list(out.values())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sitemap", nargs="*", default=[], help="lokalni XML snimci")
    ap.add_argument("--poll", action="store_true", help="preuzmi svež snimak")
    ap.add_argument("--archives", action="store_true")
    a = ap.parse_args()
    if not (a.sitemap or a.poll or a.archives):
        ap.error("zadaj bar jedno: --sitemap, --poll, --archives")

    new = []
    for f in a.sitemap:
        rows = from_sitemap(open(f, encoding="utf-8").read())
        print(f"  {f}: {len(rows)} vesti"); new += rows
    if a.poll:
        import requests
        r = requests.get(f"{BASE}/sitemap.xml", headers=C.UA, timeout=30)
        rows = from_sitemap(r.text)
        print(f"  svež snimak: {len(rows)} vesti"); new += rows
    if a.archives:
        for n in sorted(ARCHIVES):
            rows = from_archive(n)
            print(f"  arhiva {n} ({ARCHIVES[n]}): {len(rows)}"); new += rows

    path = C.DATA / "inventory.jsonl"
    old = C.read_jsonl(path)
    merged = {(r["source"], r["article_id"]): r for r in old}
    added = 0
    for r in new:
        k = (r["source"], r["article_id"])
        if k in merged:                       # zadrži stariji zapis, dopuni datum
            if not merged[k].get("date") and r.get("date"):
                merged[k]["date"] = r["date"]
        else:
            merged[k] = r; added += 1
    C.write_jsonl(path, list(merged.values()))

    print(f"\n  novih: {added}   ukupno u inventaru: {len(merged)}")
    pol = [r for r in merged.values() if r["source"] == "politika"]
    for k, v in sorted(collections.Counter(
            (r["genre"], r["topic"]) for r in pol).items(),
            key=lambda kv: tuple(map(str, kv[0]))):
        print(f"    {v:5d}  {k}")

if __name__ == "__main__":
    main()
