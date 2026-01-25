# UN iGov Static

Static site generator for the UN iGov portal, starting with General Assembly data.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

unigov scrape --session 80 --category meetings
unigov build --session 80 --category meetings
```

## Commands

- `unigov scrape --session 80 --category meetings`
- `unigov build --session 80 --category meetings`
- `unigov build --session 80 --all`

## GitHub Pages

This repo includes a GitHub Pages workflow that:

1. Scrapes GA session data
2. Builds the static site
3. Deploys `output/` to Pages

After pushing to `main`, enable Pages in the repo settings:

Settings → Pages → Source: GitHub Actions

## Data layout

```
data/ga/plenary/80/meetings.json
data/ga/plenary/80/agenda.json
data/ga/plenary/80/documents.json
data/ga/plenary/80/decisions.json
data/ga/plenary/80/proposals.json
```

Committee proposals live under `data/ga/c1/80/`, `data/ga/c2/80/`, etc.
