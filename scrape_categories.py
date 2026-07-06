#!/usr/bin/env python3
"""
Scrape the breadcrumb "primary category" for each cited URL.
============================================================
Reads unique ranking URLs (from data.json, else the newest export in exports/),
fetches each page, and extracts the breadcrumb category (e.g. Home > Document
Management > ... -> "Document Management"). Writes url_categories.json (a URL ->
category map) that build_from_export.py joins onto every prompt.

INCREMENTAL: only fetches URLs not already in url_categories.json, so re-runs are fast.

USAGE
  pip install requests beautifulsoup4
  python3 scrape_categories.py --sample 15   # test on 15 URLs, prints results
  python3 scrape_categories.py               # full run -> url_categories.json
"""
import os, sys, json, glob, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "url_categories.json")
PRE = "https://www.softwaresuggest.com"
UA = {"User-Agent": "Mozilla/5.0 (compatible; SS-CategoryBot/1.0)"}

def pick(names):
    names = [n for n in names if n]
    if names and names[0].lower() == "home": names = names[1:]
    if len(names) >= 2: return names[-2]
    if len(names) == 1: return names[0]
    return None

def extract_category(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try: data = json.loads(tag.string or "")
        except Exception: continue
        for block in (data if isinstance(data, list) else [data]):
            graph = block.get("@graph", [block]) if isinstance(block, dict) else [block]
            for node in graph:
                if isinstance(node, dict) and node.get("@type") == "BreadcrumbList":
                    names = []
                    for it in sorted(node.get("itemListElement", []), key=lambda x: x.get("position", 0)):
                        nm = it.get("name")
                        if not nm and isinstance(it.get("item"), dict): nm = it["item"].get("name")
                        if nm: names.append(str(nm).strip())
                    c = pick(names)
                    if c: return c
    for sel in ['[class*="breadcrumb"]', 'nav[aria-label*="readcrumb"]', 'ol.breadcrumb', 'ul.breadcrumb']:
        el = soup.select_one(sel)
        if el:
            names, seen = [a.get_text(strip=True) for a in el.find_all(["a","span","li"])], []
            for n in names:
                if n and (not seen or seen[-1] != n): seen.append(n)
            c = pick(seen)
            if c: return c
    return "Uncategorized"

def fetch(url):
    try:
        r = requests.get(url, headers=UA, timeout=20)
        if r.status_code == 200:
            return url, extract_category(r.text)
        return url, f"HTTP {r.status_code}"
    except Exception as e:
        return url, "error"

def unique_urls():
    dj = os.path.join(HERE, "data.json")
    if os.path.exists(dj):
        rows = json.load(open(dj)).get("rows", [])
        return sorted({r["u"] for r in rows if r.get("u")})
    import pandas as pd
    files = sum([glob.glob(os.path.join(HERE, p)) for p in ("*.xlsx","*.csv","exports/*.xlsx","exports/*.csv")], [])
    if not files: sys.exit("No data.json or export found to read URLs from.")
    newest = max(files, key=os.path.getmtime)
    df = pd.read_excel(newest) if newest.endswith(("xlsx","xls")) else pd.read_csv(newest)
    col = next(c for c in df.columns if c.lower() in ("current url","url"))
    return sorted({str(u) for u in df[col].dropna()})

def main():
    sample = None
    if "--sample" in sys.argv:
        sample = int(sys.argv[sys.argv.index("--sample")+1])
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    urls = unique_urls()
    todo = [u for u in urls if u not in cache]
    if sample: todo = todo[:sample]
    print(f"{len(urls)} unique URLs; {len(todo)} to fetch ({len(cache)} cached).")
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch, u): u for u in todo}
        for f in as_completed(futs):
            u, cat = f.result(); cache[u] = cat; done += 1
            if sample or done % 100 == 0:
                print(f"  [{done}/{len(todo)}] {cat}  <- {u[len(PRE):] if u.startswith(PRE) else u}")
    if not sample:
        json.dump(cache, open(CACHE, "w"), indent=0)
        from collections import Counter
        c = Counter(cache.values())
        print(f"\nWrote url_categories.json ({len(cache)} URLs).")
        print("Top categories:", dict(c.most_common(12)))
        print("Uncategorized:", c.get("Uncategorized", 0))
    else:
        print("\nSample only — nothing saved. If these look right, run without --sample.")

if __name__ == "__main__":
    main()
