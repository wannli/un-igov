# Agent Instructions

## Data and Output

- The `data/` directory contains scraped iGov JSON data and must remain tracked in git so GitHub Actions can deploy with current data.
- Do not edit files under `data/` unless the user explicitly requests a re-scrape or data refresh.
- Avoid staging or committing `output/` changes unless the user explicitly asks to rebuild the site locally.

## Design System (UN Style)

The site uses a clean, UN-inspired design matching www.un.org:

**Colors:**
- UN Blue: `#009edb` (primary accent)
- Text: `#333` (not pure black)
- Muted text: `#666`
- Borders: `#e5e5e5`
- Background: `#fff` (white)

**Typography:**
- Font: Inter (Google Fonts)
- Headings: 700 weight
- Labels: 12px, uppercase, letter-spacing 0.5px

**Layout:**
- Max-width: 1200px container
- Header: 60px height, simple horizontal nav
- Footer: gray background, simple links

**Component Patterns:**
- Use CSS classes defined in base.html rather than Tailwind utility classes where possible
- Tables for data lists (agenda, decisions, proposals)
- Card lists for richer content (meetings)
- Simple filter bars for lists

**No Tailwind in templates:** Use the CSS classes defined in base.html:
- `.page-header` + `.page-header h1` for page titles
- `.stats-grid` + `.stat-card` for index page
- `.data-table-container` + `table` for data lists
- `.content-card` for list items
- `.filter-bar` for filter controls

## Link Strategy

- **base_url**: Set to `/` in config.yaml for absolute paths
- All templates use `{{ site.base_url }}` prefix for links
- This works on GitHub Pages and locally via HTTP server
- **Local viewing**: Must use HTTP server, not file://

Example:
```html
<a href="{{ site.base_url }}ga/plenary/{{ session }}/meetings/index.html">Meetings</a>
```

## Local Development

**Keep the HTTP server running** - Always maintain the localhost server during development so the user can see changes in real-time.

**Auto-reload during rebuild:**
- Each page includes JS that polls `__build__` endpoint
- After rebuild, browser automatically refreshes
- Run rebuild in one terminal, keep browser open

**Build and serve:**
```bash
cd ~/code/un-igov
PYTHONPATH=src python3 -c "
from unigov.config import load_config
from unigov.generator.builder import build_all, build_environment, BuildContext
from pathlib import Path
config = load_config(Path('config.yaml'))
templates = build_environment(Path('templates'))
ctx = BuildContext(config=config, templates=templates)
build_all(ctx, '80')
"
# Then serve:
cd output && python3 -m http.server 8000
```

## Key File Locations

- Templates: `templates/*.html`
- Base template with CSS: `templates/base.html`
- Builder logic: `src/unigov/generator/builder.py`
- Config: `config.yaml`
- Session data: `data/ga/plenary/{session}/`

## Branch Management

- **Always create/move to an `opencode-XX` branch before committing** - This is critical for managing multiple opencode windows that may be open simultaneously.
- Before starting any work, check the current branch and create a new opencode branch if needed:
  ```bash
  git branch | grep 'opencode'  # Check existing opencode branches
  git checkout -b opencode-XX   # Create new branch if needed
  ```
- After committing, push the branch to origin: `git push -u origin opencode-XX`

## Collaboration Flow

- **Commit meaningful changes**: After any significant update (design changes, template updates, new features), commit immediately with a clear message. Don't batch multiple unrelated changes.
- Review `git status`, `git diff`, and recent `git log` before committing.
- Pull before push: always run `git pull --rebase` before `git push`.
- When the user says "remember", add the instruction to this `AGENTS.md`.
