
import argparse
import csv
import os
import random
import re
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    import certifi
    _CA_BUNDLE = certifi.where()
except ImportError:
    _CA_BUNDLE = True

try:
    import lxml 
    _PARSER = "lxml"
except ImportError:
    _PARSER = "html.parser"


BASE_URL = "https://n1info.rs"

SECTIONS = [
    ("Region",          "https://n1info.rs/region/",            "/region/",        "svet"),
    ("Kultura",         "https://n1info.rs/kultura/",           "/kultura/",       "kultura"),
    ("Ustavokrsitelj",  "https://n1info.rs/ustavokrsitelj/",    "/ustavokrsitelj/","pol-drustvo"),
    ("Biznis",          "https://n1info.rs/biznis/",            "/biznis/",        "ekonomija"),
]

SEED = 20260827
WINDOW = 8                 
PER_TOPIC_DEFAULT = 40
MAX_LISTING_PAGES = 40     
REQUEST_DELAY = 0.8        
OUT_DIR = "clanci_n1"
INDEX_FILE = "clanci_index.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "sr,en;q=0.8",
}

CONTENT_SELECTORS = [
    "div.entry-content",
    "div.article__content",
    "div.single__content",
    "div.post-content",
    "article .content",
    "article",
]


_ABBREVIATIONS = {
    "г", "гг", "др", "мр", "проф", "ул", "бр", "стр", "тзв", "нпр", "итд",
    "тј", "год", "в", "св", "ум", "н", "мин", "макс", "тел",
    "g", "gg", "dr", "mr", "prof", "ul", "br", "str", "tzv", "npr", "itd",
    "tj", "god", "v", "sv", "min", "maks", "tel",
}
_DOT = "\uE000"

_BOILERPLATE = re.compile(
    r"(foto\s*:|izvor\s*:|autor\s*:|video\s*:|bonus video|pratite nas|"
    r"pro[cč]itajte (jo[sš]|i)|vezane vesti|podeli|tagovi|kurir|"
    r"n1 televizij|copyright|sva prava zadr)",
    re.IGNORECASE,
)


def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).strip()
    abbr = re.compile(
        r"\b(?:%s)\." % "|".join(sorted(_ABBREVIATIONS, key=len, reverse=True)),
        re.IGNORECASE,
    )
    protected = abbr.sub(lambda m: m.group(0)[:-1] + _DOT, text)
    protected = re.sub(r"(\d)\.(\d)", rf"\1{_DOT}\2", protected)
    parts = re.split(r'(?<=[.!?…])["»”\')\]]*\s+', protected)
    return [p.replace(_DOT, ".").strip() for p in parts if len(p.strip()) > 1]


def clean_sentences(sentences: list[str]) -> list[str]:
    """Drop boilerplate, too-short, and non-prose lines."""
    out = []
    for s in sentences:
        if _BOILERPLATE.search(s):
            continue
        if len(s.split()) < 4:          
            continue
        if not re.search(r"[A-Za-zА-Яа-яЂ-џ]", s): 
            continue
        out.append(s)
    return out


def fetch(url: str, session: requests.Session):
    """Return (text_or_None, status_code_or_None)."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=20, verify=session.verify)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text, resp.status_code
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else None
        if code != 404:
            print(f"[warn] fetch failed {url}: {e}", file=sys.stderr)
        return None, code
    except requests.RequestException as e:
        print(f"[warn] fetch failed {url}: {e}", file=sys.stderr)
        return None, None


def listing_page_url(section_url: str, page: int) -> str:
    return section_url if page <= 1 else f"{section_url}{page}/"


def collect_links(html: str, base_url: str, domain: str, path_key: str) -> list[str]:
    soup = BeautifulSoup(html, _PARSER)
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"]).split("#")[0].split("?")[0]
        parsed = urlparse(href)
        if not parsed.netloc.endswith(domain):
            continue
        path = parsed.path.rstrip("/")
        last = path.split("/")[-1]
        if last.isdigit():                     
            continue
        if "/page/" in path:
            continue

        if path_key:
            if path_key not in parsed.path:
                continue
            if path.endswith(path_key.rstrip("/")):  
                continue
            if path.count("/") >= 2:            
                links.add(href)
        else:
            if "-" in last and len(last) >= 12:
                links.add(href)
    return sorted(links)


def _from_jsonld(soup):
    import json
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        cand = data if isinstance(data, list) else [data]
        for c in list(cand):
            if isinstance(c, dict) and "@graph" in c:
                cand.extend(c["@graph"])
        for c in cand:
            if isinstance(c, dict) and c.get("articleBody"):
                return c["articleBody"]
    return None


def _from_selectors(soup):
    for sel in CONTENT_SELECTORS:
        node = soup.select_one(sel)
        if not node:
            continue
        for junk in node.select(
            "script, style, figure, figcaption, aside, .advertisement, "
            ".related, .newsletter, .share, nav, .tags"
        ):
            junk.decompose()
        paras = [p.get_text(" ", strip=True) for p in node.find_all("p")]
        text = " ".join(t for t in paras if t)
        if len(text) > 120:
            return text
    return None


def extract(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, _PARSER)
    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    body = _from_jsonld(soup) or _from_selectors(soup) or ""
    clean = clean_sentences(split_sentences(body))
    return {"url": url, "title": title.strip(), "clean_sents": clean}


def collect_section(session, name, section_url, path_key, target) -> list[dict]:
    print(f"\n[info] === {name} (target {target}) ===", file=sys.stderr)
    collected, seen = [], set()
    examined = rejected_short = fetch_failed = 0

    p = urlparse(section_url)
    base_url = f"{p.scheme}://{p.netloc}"
    domain = p.netloc

    for page in range(1, MAX_LISTING_PAGES + 1):
        if len(collected) >= target:
            break
        lurl = listing_page_url(section_url, page)
        html, status = fetch(lurl, session)
        if status == 404:
            print(f"[info]   page {page} 404 -- no more listing pages "
                  f"(section has {page - 1} page(s))", file=sys.stderr)
            break
        if not html:
            continue
        links = [l for l in collect_links(html, base_url, domain, path_key)
                 if l not in seen]
        if not links:
            print(f"[info]   page {page}: no new links, stopping", file=sys.stderr)
            break
        print(f"[info]   page {page}: {len(links)} new links", file=sys.stderr)

        for url in links:
            if len(collected) >= target:
                break
            seen.add(url)
            ahtml, _ = fetch(url, session)
            time.sleep(REQUEST_DELAY)
            if not ahtml:
                fetch_failed += 1
                continue
            examined += 1
            art = extract(ahtml, url)
            n_clean = len(art["clean_sents"])
            if n_clean >= WINDOW:              
                collected.append(art)
                print(f"[info]   [{len(collected)}/{target}] ({n_clean} sents) "
                      f"{art['title'][:55]}", file=sys.stderr)
            else:
                rejected_short += 1
        time.sleep(REQUEST_DELAY)

    print(f"[info]   {name}: examined {examined} articles -> kept {len(collected)}, "
          f"rejected {rejected_short} (<{WINDOW} sentences), "
          f"fetch-failed {fetch_failed}", file=sys.stderr)
    if len(collected) < target:
        if rejected_short > len(collected):
            print(f"[warn] {name}: shortfall is mostly REJECTED articles -- body "
                  f"extraction is likely failing. Check CONTENT_SELECTORS.",
                  file=sys.stderr)
        else:
            print(f"[warn] {name}: shortfall is mostly RAN OUT OF PAGES -- the "
                  f"section paginates differently or uses infinite scroll.",
                  file=sys.stderr)

    collected.sort(key=lambda a: a["url"])
    return collected


def slugify(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-z0-9\-]+", "-", slug.lower()).strip("-")
    return slug[:60] or "article"


def main():
    ap = argparse.ArgumentParser(description="Build n1info.rs topic-labelled dataset.")
    ap.add_argument("--per-topic", type=int, default=PER_TOPIC_DEFAULT)
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--equalize", action="store_true",
                    help="trim every topic to the smallest count reached")
    ap.add_argument("--insecure", action="store_true", help="skip TLS verification")
    args = ap.parse_args()

    session = requests.Session()
    if args.insecure:
        session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print("[warn] TLS verification DISABLED (--insecure)", file=sys.stderr)
    else:
        session.verify = _CA_BUNDLE

    per_section = {}
    for name, url, key, topic in SECTIONS:
        per_section[topic] = collect_section(session, name, url, key, args.per_topic)

    if args.equalize:
        m = min(len(v) for v in per_section.values())
        per_section = {t: v[:m] for t, v in per_section.items()}
        print(f"\n[info] equalized every topic to {m} articles", file=sys.stderr)

    os.makedirs(args.out_dir, exist_ok=True)
    rng = random.Random(SEED)
    index_rows = []
    counters = {t: 0 for t in per_section}

    for _name, _url, _key, topic in SECTIONS:
        for art in per_section.get(topic, []):
            clean_sents = art["clean_sents"]
            n = min(WINDOW, len(clean_sents))
            start = rng.randrange(0, len(clean_sents) - n + 1)
            window = clean_sents[start:start + n]

            counters[topic] += 1
            idx = counters[topic]
            fname = f"{topic}_{idx:03d}_{slugify(art['url'])}.txt"
            fpath = os.path.join(args.out_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(" ".join(window) + "\n")  

            index_rows.append({
                "filename": fname,
                "topic": topic,
                "title": art["title"],
                "url": art["url"],
                "start_index": start,
                "n_sentences": n,
                "text": " ".join(window),
                "sentences": window,
            })

    index_path = os.path.join(args.out_dir, INDEX_FILE)
    with open(index_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "filename", "topic", "title", "url", "start_index", "n_sentences"])
        w.writeheader()
        for r in index_rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    dataset_path = os.path.join(args.out_dir, "dataset.csv")
    with open(dataset_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "topic", "url", "filename", "sentence_no", "sentence"])
        w.writeheader()
        for r in index_rows:
            for i, sent in enumerate(r["sentences"], 1):
                w.writerow({
                    "topic": r["topic"],
                    "url": r["url"],
                    "filename": r["filename"],
                    "sentence_no": i,
                    "sentence": sent,
                })

    print("\n[done] wrote:", file=sys.stderr)
    for t, c in counters.items():
        print(f"        {t}: {c} files", file=sys.stderr)
    print(f"        total: {len(index_rows)} articles in '{args.out_dir}/'",
          file=sys.stderr)
    print(f"        index: {index_path}", file=sys.stderr)
    print(f"        dataset: {dataset_path}", file=sys.stderr)
    if len(set(counters.values())) > 1:
        print("[note] topic counts are unequal -- rerun with --equalize to trim.",
              file=sys.stderr)


if __name__ == "__main__":
    main()