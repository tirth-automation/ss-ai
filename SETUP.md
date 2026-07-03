# AI Overview Dashboard — no API key needed

A shareable dashboard hosted free on GitHub Pages. You update it by uploading a
fresh Ahrefs export; a GitHub Action rebuilds it automatically. No API key, no admin access.

## Files
```
index.html            the dashboard (reads data.json)
data.json             the current data (already built from your June 29 export)
build_from_export.py  turns an Ahrefs export into data.json
exports/              drop new Ahrefs exports here
snapshots/            auto-created; powers the 7-day citation check
.github/workflows/build.yml   rebuilds automatically when you add an export
```

## One-time setup (~10 min)
1. Create a GitHub repo (e.g. `aio-tracker`).
2. Upload everything here to the repo root (keep the folder structure).
3. Settings → Pages → Source: "Deploy from a branch" → Branch `main` / root. Save.
4. Your link: `https://<username>.github.io/aio-tracker/` — share with the team.
   (It already shows your June 29 data.)

## Daily update (2 minutes)
1. In Ahrefs Site Explorer, open your AI-Overview organic-keywords view.
2. Click **Export** (XLSX or CSV).
3. In your GitHub repo: open the `exports/` folder → **Add file → Upload files** → drop the export in → Commit.
4. The Action runs, rebuilds `data.json`, and the live link updates in ~1 minute. Done.

## The 7-day citation check
Each upload saves a dated snapshot. After ~7 days of uploads, the dashboard
automatically turns on the "Newly cited 7d" / "Lost citation 7d" filters and the
per-prompt gained/lost badges. Upload roughly daily for it to be meaningful.

## Run locally instead (optional)
```
pip install pandas openpyxl
# put an export in ./exports then:
python3 build_from_export.py
```

## Note on other LLMs (ChatGPT / Perplexity / Gemini)
This dashboard covers Google AI Overview only, because that's what the organic-keywords
export contains. Tracking other engines needs Ahrefs Brand Radar data (a different export/report).
