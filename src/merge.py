import csv, json, re, sys, argparse, collections, io
import common as C

COLS   = C.COLS
GENRES = set(C.GENRES)
TOPICS = set(C.TOPICS)

ID_RE = re.compile(r"^([a-z0-9]{3})-(\d+)-(\d{3})$")
WINDOW = C.WINDOW
NEAR_DUP = 0.90

log_lines = []
def log(s=""):
    print(s)
    log_lines.append(s)

def validate(path):
    rows = C.read_tsv(path)
    errs, warns = [], []

    if not rows:
        return rows, ["fajl je prazan"], []
    got = list(rows[0].keys())
    if got[:len(COLS)] != COLS:
        errs.append("prvih %d kolona ne odgovara šemi\n    očekivano: %s\n    dobijeno:  %s"
                    % (len(COLS), COLS, got[:len(COLS)]))
        return rows, errs, warns
    extra = got[len(COLS):]
    if extra:
        warns.append("dodatne kolone (prenose se dalje): %s" % extra)

    seen_ids, per_article = set(), collections.Counter()
    for n, r in enumerate(rows, start=2):          
        sid = r["sentence_id"]
        m = ID_RE.match(sid)
        if not m:
            errs.append(f"red {n}: sentence_id '{sid}' ne odgovara obliku <3 znaka>-<id>-<nnn>")
            continue
        pre, aid, idx = m.groups()
        if not r["source"].startswith(pre):
            errs.append(f"red {n}: prefiks '{pre}' ne odgovara izvoru '{r['source']}'")
        if aid != r["article_id"]:
            errs.append(f"red {n}: article_id u ID-u ({aid}) != koloni ({r['article_id']})")
        if r["sent_idx"] and int(r["sent_idx"]) != int(idx):
            errs.append(f"red {n}: sent_idx ({r['sent_idx']}) != sufiks ID-a ({idx})")
        if sid in seen_ids:
            errs.append(f"red {n}: duplirani sentence_id '{sid}'")
        seen_ids.add(sid)
        per_article[(r["source"], r["article_id"])] += 1

        if r["genre"] not in GENRES:
            errs.append(f"red {n}: genre '{r['genre']}' nije iz {sorted(GENRES)}")
        if r["topic"] not in TOPICS:
            errs.append(f"red {n}: topic '{r['topic']}' nije iz {sorted(TOPICS)}")
        if not r["text"].strip():
            errs.append(f"red {n}: prazan text")
        if "\t" in r["text"]:
            errs.append(f"red {n}: tabulator unutar text")
        if not r["url"].startswith("http"):
            warns.append(f"red {n}: sumnjiv url '{r['url'][:40]}'")

    over = {k: v for k, v in per_article.items() if v > WINDOW}
    if over:
        errs.append("%d članaka daje više od %d rečenica, npr. %s"
                    % (len(over), WINDOW, list(over.items())[:3]))
    return rows, errs, warns

cramers_v = C.cramers_v

def balance_report(rows, label):
    arts = {}
    for r in rows:                                  
        arts[(r["source"], r["article_id"])] = r
    a = list(arts.values())
    log(f"\n  {label}: {len(rows)} rečenica iz {len(a)} članaka")
    for name, pairs in [
        ("tema x žanr",  [(r["topic"],  r["genre"]) for r in a]),
        ("izvor x žanr", [(r["source"], r["genre"]) for r in a]),
    ]:
        chi2, dof, v, _ = cramers_v(pairs)
        flag = "" if v < 0.15 else "   <-- PROVERITI"
        log(f"    {name:14s} chi2({dof})={chi2:6.2f}  V={v:.3f}{flag}")
    ct = collections.Counter((r["genre"], r["topic"]) for r in a)
    log("    članci po žanru i temi: " +
        ", ".join(f"{g}/{t}={n}" for (g, t), n in sorted(ct.items())))

norm = C.norm

def dedup_exact(rows):
    seen, keep, dropped = {}, [], []
    for r in rows:
        k = norm(r["text"])
        if k in seen:
            dropped.append((r, seen[k]))
        else:
            seen[k] = r; keep.append(r)
    return keep, dropped

def dedup_near(rows, thr=NEAR_DUP):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
    except ImportError:
        log("\n  [preskočeno] near-dup traži scikit-learn: pip install scikit-learn")
        return rows, []
    V = TfidfVectorizer(analyzer="char_wb", ngram_range=(4, 4), min_df=2)
    X = V.fit_transform([r["text"] for r in rows])
    keep, dropped, killed = [], [], set()
    for i in range(0, X.shape[0], 500):                       
        S = cosine_similarity(X[i:i+500], X)
        for bi, row in enumerate(S):
            gi = i + bi
            if gi in killed: continue
            for gj in np.where(row >= thr)[0]:
                if gj > gi and gj not in killed:
                    killed.add(int(gj)); dropped.append((rows[gj], rows[gi]))
    keep = [r for n, r in enumerate(rows) if n not in killed]
    return keep, dropped

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+")
ap.add_argument("--context", nargs="*", default=[])
ap.add_argument("--out", default="corpus.tsv")
args = ap.parse_args()

log("=" * 72)
log("FAZA 1 — validacija")
log("=" * 72)
parts, fatal = [], False
for f in args.files:
    rows, errs, warns = validate(f)
    log(f"\n{f}: {len(rows)} redova")
    for w in warns[:5]: log("  upozorenje: " + w)
    if warns[5:]: log(f"  ... i još {len(warns)-5} upozorenja")
    if errs:
        fatal = True
        log(f"  NEISPRAVNO ({len(errs)} grešaka):")
        for e in errs[:12]: log("    - " + e)
        if errs[12:]: log(f"    ... i još {len(errs)-12}")
    else:
        log("  u redu")
        parts.append((f, rows))

if fatal:
    log("\nSpajanje prekinuto. Ispravi fajlove iznad pa pokreni ponovo.")
    io.open("merge_report.txt", "w", encoding="utf-8").write("\n".join(log_lines))
    sys.exit(1)

log("\n" + "=" * 72)
log("FAZA 2 — izbalansiranost po članu")
log("=" * 72)
for f, rows in parts:
    balance_report(rows, f)

log("\n" + "=" * 72)
log("FAZA 3 — spajanje")
log("=" * 72)
merged = []
for f, rows in parts:
    for r in rows:
        r["member"] = f
        merged.append(r)
log(f"  ukupno pre deduplikacije: {len(merged)}")

log("\n" + "=" * 72)
log("FAZA 4 — deduplikacija")
log("=" * 72)
merged, dx = dedup_exact(merged)
log(f"  tačnih duplikata uklonjeno: {len(dx)}  -> ostalo {len(merged)}")
pairs = collections.Counter(tuple(sorted((a["source"], b["source"]))) for a, b in dx)
for k, v in pairs.most_common(8): log(f"    {k[0]} / {k[1]}: {v}")
for a, b in dx[:3]: log(f"    npr. {a['sentence_id']} == {b['sentence_id']}: {a['text'][:70]}")

merged, dn = dedup_near(merged)
log(f"  približnih duplikata (cos >= {NEAR_DUP}) uklonjeno: {len(dn)}  -> ostalo {len(merged)}")
for a, b in dn[:3]:
    log(f"    npr. {a['sentence_id']} ~ {b['sentence_id']}")
    log(f"       A: {a['text'][:78]}")
    log(f"       B: {b['text'][:78]}")

log("\n" + "=" * 72)
log("FAZA 5 — statistika spojenog korpusa")
log("=" * 72)
arts = {(r["source"], r["article_id"]) for r in merged}
log(f"\n  {len(merged)} rečenica iz {len(arts)} članaka")
for f in ("source", "genre", "topic"):
    log(f"\n  {f}:")
    for k, v in sorted(collections.Counter(r[f] for r in merged).items(),
                       key=lambda kv: -kv[1]):
        log(f"    {v:6d}  {k}")

one = {}
for r in merged: one[(r["source"], r["article_id"])] = r
a = list(one.values())
log("")
for name, prs in [("tema x žanr",  [(r["topic"],  r["genre"]) for r in a]),
                  ("izvor x žanr", [(r["source"], r["genre"]) for r in a])]:
    chi2, dof, v, (rr, cc, tab) = cramers_v(prs)
    flag = "" if v < 0.15 else "   <-- PROVERITI"
    log(f"  {name}: chi2({dof})={chi2:.2f}  Cramerovo V={v:.3f}{flag}")
    log("    " + " " * 14 + "".join(f"{c:>10s}" for c in cc))
    for i, rlab in enumerate(rr):
        log(f"    {rlab:>14s}" + "".join(f"{x:10d}" for x in tab[i]))

tok = sorted(len(r["text"].split()) for r in merged)
log(f"\n  dužina rečenice: min {tok[0]}  medijana {tok[len(tok)//2]}  max {tok[-1]}")


extra = [c for c in dict.fromkeys(k for r in merged for k in r)
         if c not in COLS + ["member"]]
for c in extra:
    have = {r["member"] for r in merged if c in r}
    miss = {r["member"] for r in merged} - have
    if miss:
        log(f"\n  UPOZORENJE: kolona '{c}' postoji u nekim fajlovima a nedostaje u: "
            f"{sorted(miss)}\n  Ti redovi dobijaju praznu vrednost — ponovo obradi "
            f"te fajlove sa build.py --from-context.")
out_cols = COLS + extra + ["member"]
with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n", **C.TSV)
    w.writerow(out_cols)
    for r in merged: w.writerow([r.get(c, "") for c in out_cols])
log(f"\n  kolone u izlazu: {out_cols}")

if args.context:
    if len(args.context) != len(parts):
        log(f"\n  UPOZORENJE: {len(args.context)} context fajlova za {len(parts)} "
            f"delova korpusa — moraju biti u istom redosledu kao TSV fajlovi.")
    ctx, clash = {}, 0
    for (f, rows), cfile in zip(parts, args.context):
        pre_of = {r["article_id"]: r["sentence_id"][:3] for r in rows}
        for aid, text in json.load(io.open(cfile, encoding="utf-8")).items():
            pre = pre_of.get(aid)
            if pre is None:
                continue                      
            k = f"{pre}-{aid}"
            if k in ctx: clash += 1
            ctx[k] = text
    json.dump(ctx, io.open("context.json", "w", encoding="utf-8"), ensure_ascii=False)
    log(f"\n  context.json: {len(ctx)} članaka (ključ: prefiks-article_id)")
    if clash: log(f"  {clash} ponovljenih ključeva unutar istog izvora")
    missing = {f'{r["sentence_id"][:3]}-{r["article_id"]}' for r in merged} - set(ctx)
    if missing:
        log(f"  UPOZORENJE: {len(missing)} članaka bez konteksta, npr. {list(missing)[:3]}")

io.open("merge_report.txt", "w", encoding="utf-8").write("\n".join(log_lines))
log(f"\n-> {args.out}")
log("-> merge_report.txt")
log("\nSledeći korak: kalibracija — uzorak od ~350 rečenica iz corpus.tsv")
