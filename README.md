# UN iGov Static

A static site generator for the UN iGov portal, transforming intergovernmental body data into browsable static HTML.

## Overview

UN iGov Static scrapes official UN General Assembly data from the [iGov API](https://igov.un.org/) and generates a static website containing:

- **Meetings**: Plenary meeting schedules and proceedings
- **Agenda**: Session agenda items
- **Documents**: Official meeting documents organized by agenda
- **Decisions**: Official GA decisions
- **Proposals**: Draft resolutions and proposals from plenary and committees

The tool supports multiple GA sessions and all six Main Committees (First through Sixth).

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/un-igov.git
cd un-igov

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e .

# Scrape data for GA session 80
unigov scrape --session 80 --all

# Build static HTML
unigov build --session 80 --all

# Preview locally
unigov serve --session 80 --port 8000
```

Visit `http://localhost:8000` to preview the generated site.

## CLI Commands

### Scrape

Fetch data from the UN iGov API and save as JSON:

```bash
unigov scrape --session 80 --category meetings    # Single category
unigov scrape --session 80 --all                  # All categories
unigov scrape --session 79 --all                  # Different session
```

Available categories: `meetings`, `agenda`, `documents`, `decisions`, `proposals`

### Build

Generate static HTML from scraped data:

```bash
unigov build --session 80 --category meetings     # Single category
unigov build --session 80 --all                   # All categories
```

### Serve

Preview the generated site locally:

```bash
unigov serve --session 80 --port 8000
```

## Data Structure

Scraped data is stored in `data/ga/`:

```
data/
  ga/
    plenary/
      80/
        meetings.json
        agenda.json
        documents.json
        decisions.json
        proposals.json
    c1/                      # First Committee
      80/
        proposals.json
    c2/                      # Second Committee
      80/
        proposals.json
    ...
    c6/                      # Sixth Committee
      80/
        proposals.json
```

## Configuration

Edit `config.yaml` to customize:

- Site title and base URL
- Output/data directory paths
- Available GA sessions
- Committee names and codes

```yaml
site:
  title: "iGov: portal to the work of intergovernmental bodies"
  output_dir: "output"
  data_dir: "data"

ga:
  sessions:
    "80":
      label: "EIGHTIETH"
      decision_label: "80th session of the General Assembly"
  committees:
    c1: "First Committee"
    c2: "Second Committee"
    ...
```

## Project Structure

```
un-igov/
  src/unigov/
    cli.py           # Click CLI entry points
    config.py        # YAML configuration loading
    scraper/igov.py  # iGov API client and scraping logic
    generator/       # Jinja2 templating and HTML generation
  templates/         # Jinja2 HTML templates
  static/            # CSS and assets
  data/              # Scraped JSON data (gitignored)
  output/            # Generated HTML (gitignored)
  .github/workflows/ # CI/CD automation
  config.yaml        # Site configuration
  pyproject.toml     # Package metadata
```

## GitHub Pages Deployment

The repository includes automated workflows:

1. **scrape.yml**: Runs daily and on push to scrape latest data
2. **pages.yml**: Rebuilds and deploys the static site

### Setup

1. Push to `main` branch
2. Enable GitHub Pages: Settings → Pages → Source: GitHub Actions
3. Workflows will automatically:
   - Scrape updated data nightly at 06:00 UTC
   - Commit any changes to the `data/` directory
   - Rebuild and deploy to GitHub Pages

## Dependencies

- **click**: CLI framework
- **httpx**: HTTP client for API requests
- **jinja2**: HTML templating
- **pyyaml**: Configuration parsing
- **rich**: Terminal output formatting

See `pyproject.toml` for exact versions.

## Development

```bash
# Run tests (if configured)
pytest

# Lint (if configured)
ruff check src/

# Type check (if configured)
mypy src/
```

## License

UN iGov Static is provided for educational and informational purposes. Data sourced from the official UN iGov portal remains the property of the United Nations.
