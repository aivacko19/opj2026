import argparse
import csv
import hashlib
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

SECTIONS = [
    ("Sport",     "https://www.rts.rs/lat/sport.html",           "/sport",      "sport",       80),
    ("Politika",  "https://www.rts.rs/lat/vesti/politika.html",  "/politika",   "pol-drustvo", 40),
    ("Ekonomija", "https://www.rts.rs/lat/vesti/ekonomija.html", "/ekonomija",  "ekonomija",   40),
    ("Svet",      "https://www.rts.rs/lat/vesti/svet.html",      "/svet",       "svet",        40),
    ("Kultura",   "https://www.rts.rs/lat/magazin/kultura.html", "/kultura",    "kultura",     40),
    ("Hronika",   "https://www.rts.rs/lat/vesti/hronika.html",   "/hronika",    "hronika",     80),
]

SEED = 20260827
WINDOW = 8                

POSITION_START = 1
POSITION_STEP = 1
MAX_LISTING_PAGES = 60     

REQUEST_DELAY = 1.2      
OUT_DIR = "rts"
INDEX_FILE = "rts_index.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sr,en;q=0.8",
    "Referer": "https://www.rts.rs/",
    "Connection": "close", 
}

MAX_RETRIES = 4            

CONTENT_SELECTORS = [
    "#story-text",
    "#text",
    "div.story-wrapper",
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
    r"pro[cč]itajte (jo[sš]|i)|vezane vesti|podeli|tagovi|"
    r"copyright|sva prava zadr|rts|"
    r"извор\s*:|фото\s*:|аутор\s*:|видео\s*:|прочитајте|подели)",
    re.IGNORECASE,
)

_DATELINE = re.compile(
    r"^\s*(pon|uto|sre|[cč]et|pet|sub|ned|"
    r"понедељак|уторак|среда|четвртак|петак|субота|недеља)"
    r".*\d{1,2}[.:]\d{2}", re.IGNORECASE)


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
    out = []
    for s in sentences:
        if _BOILERPLATE.search(s):
            continue
        if _DATELINE.search(s):
            continue
        if len(s.split()) < 4:
            continue
        if not re.search(r"[A-Za-zА-Яа-яЂ-џ]", s):
            continue
        out.append(cyr_to_lat(s))
    return out

_CYR_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ђ": "đ", "е": "e",
    "ж": "ž", "з": "z", "и": "i", "ј": "j", "к": "k", "л": "l", "љ": "lj",
    "м": "m", "н": "n", "њ": "nj", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "ћ": "ć", "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "č",
    "џ": "dž", "ш": "š",
}

for _c, _l in list(_CYR_LAT.items()):
    _CYR_LAT[_c.upper()] = _l[:1].upper() + _l[1:]


def cyr_to_lat(text: str) -> str:
    if not text:
        return text
    return "".join(_CYR_LAT.get(ch, ch) for ch in text)


def fetch(url: str, session: requests.Session):
    """Return (text_or_None, status_code_or_None). Retries drops and
    transient HTTP errors (408 timeout, 429 too-many, 5xx) with backoff."""
    RETRYABLE = {408, 429, 500, 502, 503, 504}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=25,
                               verify=session.verify)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text, resp.status_code
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else None
            if code in RETRYABLE and attempt < MAX_RETRIES:
                time.sleep(2.0 * (2 ** (attempt - 1)))   # 2, 4, 8, 16 sekundi
                continue
            if code != 404:
                print(f"[warn] fetch failed {url}: {e}", file=sys.stderr)
            return None, code
        except requests.RequestException as e:
            if attempt < MAX_RETRIES:
                time.sleep(2.0 * (2 ** (attempt - 1)))
                continue
            print(f"[warn] fetch failed {url}: {e}", file=sys.stderr)
            return None, None


def listing_page_url(section_url: str, page: int) -> str:
    pos = POSITION_START + (page - 1) * POSITION_STEP
    sep = "&" if "?" in section_url else "?"
    return f"{section_url}{sep}position={pos}"


def collect_links(html: str, base_url: str, domain: str, path_key: str) -> list[str]:
    """RTS articles look like /sport/fudbal/6037981/slug.html --
    section keyword in path, a numeric story-id, ending in .html (no /lat/)."""
    soup = BeautifulSoup(html, _PARSER)
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"]).split("#")[0].split("?")[0]
        parsed = urlparse(href)
        if not parsed.netloc.endswith(domain):
            continue
        path = parsed.path
        if not path.endswith(".html"):
            continue
        if path_key not in path:
            continue
        if not re.search(r"/\d{5,}/", path): 
            continue
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
    return {"url": url, "title": cyr_to_lat(title.strip()), "clean_sents": clean}


def collect_section(session, name, section_url, path_key, target, topic,
                    out_dir, counters, index_rows) -> int:
    print(f"\n[info] === {name} -> {topic} (target {target}) ===", file=sys.stderr)
    kept, seen = 0, set()
    examined = rejected_short = fetch_failed = 0

    p = urlparse(section_url)
    base_url = f"{p.scheme}://{p.netloc}"
    domain = p.netloc

    for page in range(1, MAX_LISTING_PAGES + 1):
        if kept >= target:
            break
        lurl = listing_page_url(section_url, page)
        html, status = fetch(lurl, session)
        if status == 404:
            print(f"[info]   position {page} 404 -- no more pages", file=sys.stderr)
            break
        if not html:
            continue
        links = [l for l in collect_links(html, base_url, domain, path_key)
                 if l not in seen]
        if not links:
            print(f"[info]   position {page}: no new links, stopping", file=sys.stderr)
            break
        print(f"[info]   position {page}: {len(links)} new links", file=sys.stderr)

        for j, url in enumerate(links, 1):
            if kept >= target:
                break
            seen.add(url)
            print(f"[info]   ({j}/{len(links)}) fetching {url[-55:]}",
                  file=sys.stderr, flush=True)
            ahtml, _ = fetch(url, session)
            time.sleep(REQUEST_DELAY)
            if not ahtml:
                fetch_failed += 1
                print("[info]     -> connection failed (after retries), skipped",
                      file=sys.stderr, flush=True)
                continue
            examined += 1
            art = extract(ahtml, url)
            n_clean = len(art["clean_sents"])
            if n_clean >= WINDOW:
                start, n, window = window_for(art["clean_sents"], url)
                counters[topic] = counters.get(topic, 0) + 1
                idx = counters[topic]
                fname = write_txt(out_dir, topic, idx, url, window)
                index_rows.append({
                    "filename": fname, "topic": topic, "source": name,
                    "title": art["title"], "url": url,
                    "start_index": start, "n_sentences": n, "sentences": window,
                })
                flush_outputs(out_dir, index_rows)   
                kept += 1
                print(f"[info]     -> KEPT [{kept}/{target}] ({n_clean} sents)",
                      file=sys.stderr, flush=True)
            else:
                rejected_short += 1
                print(f"[info]     -> only {n_clean} sentences, skipped",
                      file=sys.stderr, flush=True)
        time.sleep(REQUEST_DELAY)

    print(f"[info]   {name}: examined {examined} -> kept {kept}, "
          f"rejected {rejected_short} (<{WINDOW} sentences), "
          f"fetch-failed {fetch_failed}", file=sys.stderr)
    if kept < target:
        if rejected_short > kept:
            print(f"[warn] {name}: shortfall is mostly REJECTED -- body extraction "
                  f"likely failing. Check CONTENT_SELECTORS.", file=sys.stderr)
        else:
            print(f"[warn] {name}: shortfall is mostly RAN OUT OF PAGES / drops -- "
                  f"check pagination or slow down.", file=sys.stderr)
    return kept



def slugify(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"\.html?$", "", slug.lower())
    slug = re.sub(r"[^a-z0-9\-]+", "-", slug).strip("-")
    return slug[:60] or "article"


def write_txt(out_dir, topic, idx, url, window):
    fname = f"{topic}_{idx:03d}_{slugify(url)}.txt"
    with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
        f.write(" ".join(window) + "\n")
    return fname


def window_for(clean_sents, url):
    """Exactly 8 consecutive sentences from a seeded-random start. The seed is
    derived from SEED + the article URL, so each window is reproducible
    regardless of the order articles happen to be scraped in."""
    n = min(WINDOW, len(clean_sents))
    seed = SEED ^ int(hashlib.md5(url.encode("utf-8")).hexdigest()[:8], 16)
    r = random.Random(seed)
    start = r.randrange(0, len(clean_sents) - n + 1)
    return start, n, clean_sents[start:start + n]


def flush_outputs(out_dir, index_rows):
    """Re-write the index and dataset CSVs from the rows collected so far.
    Called after every kept article so progress is never lost."""
    index_path = os.path.join(out_dir, INDEX_FILE)
    with open(index_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "filename", "topic", "source", "title", "url",
            "start_index", "n_sentences"])
        w.writeheader()
        for r in index_rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    dataset_path = os.path.join(out_dir, "dataset.csv")
    with open(dataset_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "topic", "source", "url", "filename", "sentence_no", "sentence"])
        w.writeheader()
        for r in index_rows:
            for i, sent in enumerate(r["sentences"], 1):
                w.writerow({
                    "topic": r["topic"], "source": r["source"], "url": r["url"],
                    "filename": r["filename"], "sentence_no": i, "sentence": sent,
                })
    return index_path, dataset_path


def main():
    ap = argparse.ArgumentParser(description="Build an RTS topic-labelled dataset.")
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--limit", type=int, default=0,
                    help="cap each section's target (for a quick test run)")
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

    os.makedirs(args.out_dir, exist_ok=True)
    counters, index_rows = {}, []


    for name, url, key, topic, target in SECTIONS:
        if args.limit:
            target = min(target, args.limit)
        collect_section(session, name, url, key, target, topic,
                        args.out_dir, counters, index_rows)

    index_path, dataset_path = flush_outputs(args.out_dir, index_rows)

    print("\n[done] wrote:", file=sys.stderr)
    for t, c in counters.items():
        print(f"        {t}: {c} files", file=sys.stderr)
    print(f"        total: {len(index_rows)} articles in '{args.out_dir}/'",
          file=sys.stderr)
    print(f"        index: {index_path}", file=sys.stderr)
    print(f"        dataset: {dataset_path}", file=sys.stderr)


if __name__ == "__main__":
    main()