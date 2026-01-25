from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from unigov.config import Config


@dataclass(frozen=True)
class BuildContext:
    config: Config
    templates: Environment


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_static_assets(config: Config) -> None:
    source = config.site.output_dir.parent / "static"
    target = config.site.output_dir / "static"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def datetime_format(value: str, format: str = "%B %d, %Y") -> str:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime(format)
    except (ValueError, AttributeError):
        return value


def build_environment(template_root: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_root)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["datetime_format"] = datetime_format
    return env


def build_index(ctx: BuildContext, session_number: str) -> None:
    template = ctx.templates.get_template("index.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number
    meetings = load_json(data_dir / "meetings.json") or []
    documents = load_json(data_dir / "documents.json") or []
    agenda = load_json(data_dir / "agenda.json") or []
    decisions = load_json(data_dir / "decisions.json") or []
    proposals = load_json(data_dir / "proposals.json") or {"result": []}

    def count_documents(items: list[dict[str, Any]]) -> int:
        total = 0
        for item in items:
            docs = item.get("documents") or []
            total += len(docs)
        return total

    output = template.render(
        site=ctx.config.site,
        session=session_number,
        stats={
            "meetings": len(meetings),
            "agenda": len(agenda),
            "documents": count_documents(documents),
            "decisions": len(decisions),
            "proposals": len(proposals.get("result", [])),
        },
    )

    output_dir = ctx.config.site.output_dir
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_meetings(ctx: BuildContext, session_number: str) -> None:
    template = ctx.templates.get_template("meetings.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number
    meetings = load_json(data_dir / "meetings.json") or []
    current_date = datetime.now().strftime("%Y-%m-%d")
    output = template.render(site=ctx.config.site, session=session_number, meetings=meetings, current_date=current_date)

    output_dir = ctx.config.site.output_dir / "ga" / "plenary" / session_number / "meetings"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_agenda(ctx: BuildContext, session_number: str) -> None:
    template = ctx.templates.get_template("agenda.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number
    agenda = load_json(data_dir / "agenda.json") or []
    output = template.render(site=ctx.config.site, session=session_number, agenda=agenda)

    output_dir = ctx.config.site.output_dir / "ga" / "plenary" / session_number / "agenda"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_documents(ctx: BuildContext, session_number: str) -> None:
    template = ctx.templates.get_template("documents.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number
    documents = load_json(data_dir / "documents.json") or []

    flattened = []
    for item in documents:
        agenda_title = item.get("AG_Title")
        agenda_item = item.get("AG_Item")
        for doc in item.get("documents") or []:
            flattened.append({
                "agenda_title": agenda_title,
                "agenda_item": agenda_item,
                "symbol": doc.get("DD_symbol1"),
                "title": doc.get("DD_officialTitle") or doc.get("DD_workingTitle"),
                "doc_type": doc.get("DD_documentType"),
                "date": doc.get("DD_officialDate"),
            })

    output = template.render(site=ctx.config.site, session=session_number, documents=flattened)

    output_dir = ctx.config.site.output_dir / "ga" / "plenary" / session_number / "documents"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_decisions(ctx: BuildContext, session_number: str) -> None:
    template = ctx.templates.get_template("decisions.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number
    decisions = load_json(data_dir / "decisions.json") or []
    output = template.render(site=ctx.config.site, session=session_number, decisions=decisions)

    output_dir = ctx.config.site.output_dir / "ga" / "plenary" / session_number / "decisions"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_proposals(ctx: BuildContext, session_number: str) -> None:
    template = ctx.templates.get_template("proposals.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number
    proposals = load_json(data_dir / "proposals.json") or {"result": []}
    output = template.render(site=ctx.config.site, session=session_number, proposals=proposals.get("result", []))

    output_dir = ctx.config.site.output_dir / "ga" / "plenary" / session_number / "proposals"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_category(ctx: BuildContext, session_number: str, category: str) -> None:
    builders = {
        "meetings": build_meetings,
        "agenda": build_agenda,
        "documents": build_documents,
        "decisions": build_decisions,
        "proposals": build_proposals,
    }

    if category not in builders:
        raise ValueError(f"Unknown category: {category}")

    builders[category](ctx, session_number)
    build_index(ctx, session_number)
    copy_static_assets(ctx.config)


def build_all(ctx: BuildContext, session_number: str) -> None:
    categories = ["meetings", "agenda", "documents", "decisions", "proposals"]
    for category in categories:
        if category == "meetings":
            build_meetings(ctx, session_number)
        elif category == "agenda":
            build_agenda(ctx, session_number)
        elif category == "documents":
            build_documents(ctx, session_number)
        elif category == "decisions":
            build_decisions(ctx, session_number)
        elif category == "proposals":
            build_proposals(ctx, session_number)
    build_index(ctx, session_number)
    copy_static_assets(ctx.config)
