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

## Browser Verification

When debugging issues that aren't clear from code analysis alone, check the browser to see the actual rendered output and identify visual or functional issues. Use the browser tools to:
- Navigate to the page in question
- Take a snapshot to see the accessibility tree
- Look for rendering issues that aren't visible in the code

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

- **Commit directly to main for small fixes and changes** - No need to create branches for each session.
- **Use opencode branches for significant features or multi-step changes** - When working on major updates that may span multiple sessions.
- When done with an opencode branch: merge to main promptly and delete the remote branch.
- Before pushing, run `git pull --rebase` to avoid merge conflicts.

## Collaboration Flow

- **Commit meaningful changes**: After any significant update (design changes, template updates, new features), commit immediately with a clear message. Don't batch multiple unrelated changes.
- Review `git status`, `git diff`, and recent `git log` before committing.
- Pull before push: always run `git pull --rebase` before `git push`.
- When the user says "remember", add the instruction to this `AGENTS.md`.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
