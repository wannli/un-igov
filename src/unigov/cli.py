from __future__ import annotations

import http.server
import socketserver
from pathlib import Path

import click
from rich.console import Console

from unigov.config import load_config
from unigov.generator.builder import build_all, build_category, build_environment, BuildContext
from unigov.scraper.igov import scrape_ga_session


console = Console()


def resolve_config_path(config_path: str | None) -> Path:
    if config_path:
        return Path(config_path)
    return Path(__file__).resolve().parents[2] / "config.yaml"


def parse_categories(category: str | None, all_categories: bool) -> set[str]:
    if all_categories:
        return {"meetings", "agenda", "documents", "decisions", "proposals"}
    if category:
        return {category}
    return {"meetings", "agenda", "documents", "decisions", "proposals"}


@click.group()
def cli() -> None:
    """UN iGov static site generator."""


@cli.command()
@click.option("--config", "config_path", type=str, help="Path to config.yaml")
@click.option("--session", "session_number", required=True, type=str)
@click.option("--category", type=str)
@click.option("--all", "all_categories", is_flag=True, help="Scrape all categories")
def scrape(config_path: str | None, session_number: str, category: str | None, all_categories: bool) -> None:
    """Scrape GA data into nested JSON files."""
    config = load_config(resolve_config_path(config_path))
    if session_number not in config.ga.sessions:
        raise click.ClickException(f"Unknown session {session_number}")

    session = config.ga.sessions[session_number]
    categories = parse_categories(category, all_categories)

    console.print(f"Scraping GA session {session_number} ({session.label}) -> {sorted(categories)}")
    scrape_ga_session(
        data_root=config.site.data_dir,
        session_number=session.number,
        session_label=session.label,
        decision_label=session.decision_label,
        committees=config.ga.committees,
        categories=categories,
    )


@cli.command()
@click.option("--config", "config_path", type=str, help="Path to config.yaml")
@click.option("--session", "session_number", required=True, type=str)
@click.option("--category", type=str)
@click.option("--all", "all_categories", is_flag=True, help="Build all categories")
def build(config_path: str | None, session_number: str, category: str | None, all_categories: bool) -> None:
    """Build static HTML for GA."""
    config = load_config(resolve_config_path(config_path))
    if session_number not in config.ga.sessions:
        raise click.ClickException(f"Unknown session {session_number}")

    templates = build_environment(Path(__file__).resolve().parents[2] / "templates")
    ctx = BuildContext(config=config, templates=templates)

    if all_categories or not category:
        build_all(ctx, session_number)
        console.print(f"Built all categories for GA session {session_number}.")
    else:
        build_category(ctx, session_number, category)
        console.print(f"Built {category} for GA session {session_number}.")


@cli.command()
@click.option("--config", "config_path", type=str, help="Path to config.yaml")
@click.option("--session", "session_number", required=True, type=str)
@click.option("--port", type=int, default=8000)
def serve(config_path: str | None, session_number: str, port: int) -> None:
    """Serve output directory for preview."""
    config = load_config(resolve_config_path(config_path))
    output_dir = config.site.output_dir
    if not output_dir.exists():
        raise click.ClickException("Output directory does not exist. Run build first.")

    console.print(f"Serving {output_dir} on http://localhost:{port}")
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.RequestHandlerClass.directory = str(output_dir)
        httpd.serve_forever()
