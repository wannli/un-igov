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


def slugify(text: str) -> str:
    import re
    if not text:
        return "meeting"
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:60]


def meeting_url(meeting: dict) -> str:
    date = meeting.get("MT_dateTimeScheduleStart", "")[:10]
    name = slugify(meeting.get("MT_name", ""))
    return f"{date}-{name}/"


def build_environment(template_root: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_root)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["datetime_format"] = datetime_format
    env.filters["meeting_url"] = meeting_url
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


def meeting_id(meeting: dict) -> str:
    date = meeting.get("MT_dateTimeScheduleStart", "")[:10]
    name = slugify(meeting.get("MT_name", ""))
    return f"{date}-{name}"


def load_proposals_map(data_dir: Path):
    proposals_map = {}
    resolution_map = {}
    ga_dir = data_dir / "ga"
    if not ga_dir.exists():
        return proposals_map, resolution_map

    for committee in ga_dir.iterdir():
        if not committee.is_dir():
            continue
        for session in committee.iterdir():
            if not session.is_dir():
                continue
            proposals_file = session / "proposals.json"
            if not proposals_file.exists():
                continue
            proposals = load_json(proposals_file) or {}
            for proposal in proposals.get("result", []):
                for stage in proposal.get("PR_Stage", []):
                    doc_symbol = stage.get("DocSymbol", "")
                    if doc_symbol and "DR " in doc_symbol:
                        for vote in stage.get("VotesAdd", []):
                            psid = vote.get("PSID")
                            if psid:
                                if psid not in proposals_map:
                                    proposals_map[psid] = {}
                                proposals_map[psid]["draft_symbol"] = doc_symbol
                                if proposal.get("PR_Title"):
                                    proposals_map[psid]["title"] = proposal.get("PR_Title")
                    if doc_symbol and "/" in doc_symbol:
                        if doc_symbol.startswith("A/80/") and "DR " in doc_symbol:
                            resolution_num = doc_symbol.split("DR ")[-1].strip()
                            full_res = f"80/{resolution_num}"
                            if full_res not in resolution_map:
                                resolution_map[full_res] = doc_symbol
    return proposals_map, resolution_map


def build_meeting_detail(ctx: BuildContext, session_number: str, meeting_id_str: str, meeting: dict, proposals_map: dict | None = None, resolution_map: dict | None = None) -> None:
    template = ctx.templates.get_template("meeting.html")

    output = template.render(
        site=ctx.config.site,
        session=session_number,
        meeting=meeting,
        meeting_id=meeting_id_str,
        proposals_map=proposals_map or {},
        resolution_map=resolution_map or {},
    )

    output_dir = ctx.config.site.output_dir / "ga" / "plenary" / session_number / "meetings" / meeting_id_str
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_meetings(ctx: BuildContext, session_number: str) -> None:
    template = ctx.templates.get_template("meetings.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number
    meetings = load_json(data_dir / "meetings.json") or []
    current_date = datetime.now().strftime("%Y-%m-%d")

    proposals_map, resolution_map = load_proposals_map(ctx.config.site.data_dir)

    output = template.render(site=ctx.config.site, session=session_number, meetings=meetings, current_date=current_date)

    output_dir = ctx.config.site.output_dir / "ga" / "plenary" / session_number / "meetings"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")

    for meeting in meetings:
        mid = meeting_id(meeting)
        build_meeting_detail(ctx, session_number, mid, meeting, proposals_map, resolution_map)


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
