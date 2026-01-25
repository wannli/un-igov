# Agent Instructions

## Data and Output

- The `data/` directory contains scraped iGov JSON data and must remain tracked in git so GitHub Actions can deploy with current data.
- Do not edit files under `data/` unless the user explicitly requests a re-scrape or data refresh.
- Avoid staging or committing `output/` changes unless the user explicitly asks to rebuild the site locally.

## Collaboration Flow

- Review `git status`, `git diff`, and recent `git log` before committing.
- Pull before push: always run `git pull --rebase` before `git push`.
- When the user says "remember", add the instruction to this `AGENTS.md`.
