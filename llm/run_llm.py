import os, re, io, csv, sys, json, time, hashlib, argparse, pathlib, collections
import threading
from concurrent.futures import ThreadPoolExecutor
import prompts as P

_lock = threading.Lock()

CACHE = pathlib.Path("cache_llm"); CACHE.mkdir(exist_ok=True)
OUT = pathlib.Path("llm_preds"); OUT.mkdir(exist_ok=True)

MODELS = {           
    "chatgpt": os.environ.get("OPENAI_MODEL", "gpt-4.1"),
    "gemini":  os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
}


def call_openai(sys_p, usr_p, model):
    from openai import OpenAI
    r = OpenAI().chat.completions.create(
        model=model, temperature=0,
        messages=[{"role": "system", "content": sys_p},
                  {"role": "user", "content": usr_p}])
    u = r.usage
    return r.choices[0].message.content, {"in": u.prompt_tokens, "out": u.completion_tokens}


def call_gemini(sys_p, usr_p, model):
    from google import genai
    from google.genai import types
    c = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    r = c.models.generate_content(
        model=model, contents=usr_p,
        config=types.GenerateContentConfig(system_instruction=sys_p, temperature=0))
    u = getattr(r, "usage_metadata", None)
    return r.text, {"in": getattr(u, "prompt_token_count", 0),
                    "out": getattr(u, "candidates_token_count", 0)}


CALL = {"chatgpt": call_openai, "gemini": call_gemini}

RETRIES = 6            


def backoff(exc, attempt):
    """Koliko čekati posle greške.

    Kod 429 poruka često sadrži koliko treba čekati ("try again in 1.81s").
    Ako je ima, poštuje se, uz malu rezervu; inače se ide eksponencijalno.
    Ograničenje po tokenima u minuti se obnavlja svakih 60 sekundi, pa čekanje
    ide do te granice.
    """
    msg = str(exc)
    m = re.search(r"try again in ([\d.]+)s", msg)
    if m:
        return min(60.0, float(m.group(1)) + 1.0)
    if "429" in msg or "rate" in msg.lower() or "quota" in msg.lower():
        return min(60.0, 5.0 * 2 ** (attempt - 1))
    return min(30.0, 2.0 * attempt)


def parse(text, n):
    """Vadi {broj: oznaka} iz odgovora. Vraća None ako ne pokriva celu grupu."""
    if not text:
        return None
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    out = {}
    for k, v in d.items():
        k = str(k).strip()
        v = str(v).strip().upper()
        if k.isdigit() and v in ("OBJ", "SUBJ"):
            out[int(k)] = v
    return out if len(out) == n else None


def cache_path(model, cfg):
    return CACHE / f"{model}-{cfg}.jsonl"


def load_cache(model, cfg):
    """Učitava samo USPEŠNE zapise.

    Zapisi sa greškom (429, prekid veze, pokvaren JSON) se preskaču, pa ih
    ponovno pokretanje automatski ponavlja. Bez ovoga bi jednom neuspela grupa
    zauvek ostala neuspela, jer bi je keš vraćao kao gotovu.
    """
    p = cache_path(model, cfg)
    if not p.exists():
        return {}
    ok, bad = {}, 0
    for d in (json.loads(l) for l in p.open(encoding="utf-8")):
        if parse(d.get("raw"), d["n"]):
            ok[d["key"]] = d
        else:
            bad += 1
    if bad:
        print(f"    (u kešu {bad} neuspelih grupa — biće ponovljene)")
    return ok


def append_cache(model, cfg, rec):
    with _lock:                               
        with cache_path(model, cfg).open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(rows, model, lang, shots, batch, sleep, workers=1):
    cfg = f"{lang}-{shots}"
    name = P.config_name(model, lang, shots)
    sys_p = P.system_prompt(lang, shots)
    cache = load_cache(model, cfg)
    groups = [rows[i:i+batch] for i in range(0, len(rows), batch)]

    preds, fails, usage = {}, [], collections.Counter()
    counter = {"done": 0, "new": 0}

    def handle(item):
        gi, g = item
        sents = [r.get("text_marked") or r["text"] for r in g]
        key = hashlib.sha1(("\n".join(sents)).encode()).hexdigest()[:16]
        if key in cache:
            rec = cache[key]
        else:
            usr_p = P.user_prompt(sents, lang)
            raw, tok = None, {"in": 0, "out": 0}
            for attempt in range(1, RETRIES + 1):
                try:
                    raw, tok = CALL[model](sys_p, usr_p, MODELS[model])
                    if parse(raw, len(g)):
                        break
                    time.sleep(sleep)              # odgovor stigao ali ne valja
                except Exception as e:
                    raw = f"ERROR: {e!r}"
                    wait = backoff(e, attempt)
                    if attempt < RETRIES:
                        time.sleep(wait)
            rec = {"key": key, "raw": raw, "n": len(g), "tok": tok,
                   "ids": [r["sentence_id"] for r in g]}
            append_cache(model, cfg, rec)
            with _lock:
                counter["new"] += 1
            time.sleep(sleep)
        with _lock:
            usage["in"] += rec["tok"]["in"]; usage["out"] += rec["tok"]["out"]
            got = parse(rec["raw"], rec["n"])
            for j, r in enumerate(g, 1):
                preds[r["sentence_id"]] = got[j] if got else "PARSE_FAIL"
            if not got:
                fails.append(rec["ids"][0])
            counter["done"] += 1
            if counter["done"] % 25 == 0 or counter["done"] == len(groups):
                print(f"    {counter['done']}/{len(groups)} grupa   novih poziva "
                      f"{counter['new']}   neuspelih {len(fails)}", flush=True)

    items = list(enumerate(groups, 1))
    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(handle, items))
    else:
        for it in items:
            handle(it)

    rate = len(fails) / max(1, len(groups))
    print(f"  {name}: {len(preds)} rečenica, neuspelih grupa "
          f"{len(fails)}/{len(groups)} ({rate:.1%}), "
          f"tokeni {usage['in']:,}/{usage['out']:,}")

    with io.open(OUT / f"{name}.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quotechar=None,
                       quoting=csv.QUOTE_NONE, lineterminator="\n")
        w.writerow(["sentence_id", "pred", "model", "lang", "shots"])
        for sid, p in preds.items():
            w.writerow([sid, p, MODELS[model], lang, shots])
    print(f"  -> {OUT}/{name}.tsv")
    return rate, usage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--lang", choices=["sr", "en"])
    ap.add_argument("--shots", choices=["zero", "few"])
    ap.add_argument("--all", action="store_true", help="sve 4 konfiguracije")
    ap.add_argument("--data", default="../corpus.tsv")
    ap.add_argument("--batch", type=int, default=15)
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--workers", type=int, default=1,
                    help="paralelnih poziva; sa naplatom 8 je bezbedno, "
                         "na besplatnom nivou ostaviti 1")
    ap.add_argument("--limit", type=int, help="probno: samo prvih N rečenica")
    a = ap.parse_args()

    rows = list(csv.DictReader(io.open(a.data, encoding="utf-8", newline=""),
                               delimiter="\t", quotechar=None,
                               quoting=csv.QUOTE_NONE))
    rows = [r for r in rows if r["sentence_id"] not in P.FEWSHOT_IDS]
    if a.limit:
        rows = rows[:a.limit]
    print(f"{len(rows)} rečenica (bez {len(P.FEWSHOT_IDS)} few-shot primera)")
    print(f"model: {MODELS[a.model]}\n")

    cfgs = P.CONFIGS if a.all else [(a.lang or "sr", a.shots or "zero")]
    tot = collections.Counter()
    for lang, shots in cfgs:
        print(f"[{lang}-{shots}]")
        _, u = run(rows, a.model, lang, shots, a.batch, a.sleep, a.workers)
        tot["in"] += u["in"]; tot["out"] += u["out"]
    print(f"\nukupno tokena: ulaz {tot['in']:,}  izlaz {tot['out']:,}")


if __name__ == "__main__":
    main()
