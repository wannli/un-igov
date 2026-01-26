from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from unigov.config import Config
from unigov.generator.renderer import render_procedure_steps, group_steps_by_segment


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


def process_footnotes(text: str) -> tuple[str, list[str]]:
    import re
    if not text:
        return "", []

    footnotes: list[str] = []
    result = text

    while True:
        match = re.search(r"\((?:[Ff]ootnote)\s*:\s*", result)
        if not match:
            break

        start = match.start()
        open_paren = match.end() - 1
        depth = 1
        i = open_paren + 1

        while depth > 0 and i < len(result):
            if result[i] == '(':
                depth += 1
            elif result[i] == ')':
                depth -= 1
            i += 1

        if depth > 0:
            break

        footnote_content = result[open_paren + 1:i - 1].strip()
        footnote_num = len(footnotes) + 1
        footnotes.append(footnote_content)

        replacement = f'<sup><a href="#fn{footnote_num}" id="fnref{footnote_num}">{footnote_num}</a></sup>'
        result = result[:start] + replacement + result[i:]

    return result, footnotes


def get_footnotes(text: str) -> list[str]:
    """Extract footnotes from text without processing."""
    import re
    if not text:
        return []

    footnotes: list[str] = []
    result = text

    while True:
        match = re.search(r"\((?:[Ff]ootnote)\s*:\s*", result)
        if not match:
            break

        start = match.start()
        open_paren = match.end() - 1
        depth = 1
        i = open_paren + 1

        while depth > 0 and i < len(result):
            if result[i] == '(':
                depth += 1
            elif result[i] == ')':
                depth -= 1
            i += 1

        if depth > 0:
            break

        footnote_content = result[open_paren + 1:i - 1].strip()
        footnotes.append(footnote_content)
        result = result[i:]

    return footnotes


def get_base_url(config: Config) -> str:
    """Get the base URL with trailing slash."""
    base_url = config.site.base_url or ""
    if not base_url.endswith("/"):
        base_url = base_url + "/"
    return base_url


def make_breadcrumb(label: str, url: str) -> dict[str, str]:
    """Create a single breadcrumb item."""
    return {"label": label, "url": url}


def home_breadcrumb(config: Config) -> dict[str, str]:
    """Create the home breadcrumb item."""
    return make_breadcrumb("Home", get_base_url(config))


def ga_plenary_breadcrumb(session: str, config: Config) -> dict[str, str]:
    """Create General Assembly plenary breadcrumb."""
    base = get_base_url(config)
    return make_breadcrumb("General Assembly", f"{base}ga/plenary/{session}/index.html")


def ga_committee_breadcrumb(committee: str, session: str, config: Config) -> dict[str, str]:
    """Create GA committee breadcrumb."""
    base = get_base_url(config)
    committee_names = {
        "c1": "First Committee",
        "c2": "Second Committee",
        "c3": "Third Committee",
        "c4": "Fourth Committee",
        "c5": "Fifth Committee",
    }
    name = committee_names.get(committee, committee.upper())
    return make_breadcrumb(name, f"{base}ga/{committee}/{session}/index.html")


def ecosoc_plenary_breadcrumb(session: str, config: Config) -> dict[str, str]:
    """Create ECOSOC plenary breadcrumb."""
    base = get_base_url(config)
    return make_breadcrumb("ECOSOC", f"{base}ecosoc/plenary/{session}/index.html")


def ecosoc_body_breadcrumb(body_code: str, session: str, config: Config) -> dict[str, str]:
    """Create ECOSOC body breadcrumb."""
    base = get_base_url(config)
    body_names = {
        "hlpf": "High-level Political Forum",
        "csw": "Commission on the Status of Women",
        "ggim": "Committee of Experts on GGIM",
        "unff": "UN Forum on Forests",
        "ungegn": "Group of Experts on Geographical Names",
    }
    name = body_names.get(body_code, body_code.upper())
    return make_breadcrumb(name, f"{base}ecosoc/{body_code}/{session}/index.html")


def conference_breadcrumb(code: str, session: str, config: Config) -> dict[str, str]:
    """Create conference breadcrumb."""
    base = get_base_url(config)
    conference_names = {
        "ffd4": "Fourth International Conference on Financing for Development",
        "ffd4pc": "FFD4 PrepCom",
    }
    name = conference_names.get(code, code.upper())
    return make_breadcrumb(name, f"{base}conferences/{code}/{session}/index.html")


def session_breadcrumb(label: str, url: str) -> dict[str, str]:
    """Create a session breadcrumb item."""
    return make_breadcrumb(label, url)


def page_breadcrumb(label: str) -> dict[str, str]:
    """Create a page breadcrumb item (current page, no URL)."""
    return {"label": label}


def build_environment(template_root: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_root)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["datetime_format"] = datetime_format
    env.filters["meeting_url"] = meeting_url
    env.filters["process_footnotes"] = lambda text: process_footnotes(text)[0]
    env.globals["datetime"] = datetime
    env.globals["get_footnotes"] = get_footnotes
    return env


def build_ga_breadcrumbs(
    session: str,
    page_class: str,
    config: Config,
    specific: str | None = None,
) -> list[dict[str, str]]:
    """Build breadcrumbs for GA plenary pages.

    Pattern: Home → General Assembly → 80 → Class → Specific
    """
    base = get_base_url(config)
    breadcrumbs = [
        make_breadcrumb("Home", f"{base}index.html"),
        make_breadcrumb("General Assembly", f"{base}ga/plenary/{session}/index.html"),
        make_breadcrumb(session, f"{base}ga/plenary/{session}/index.html"),
        make_breadcrumb(page_class.title(), f"{base}ga/plenary/{session}/{page_class}/index.html"),
    ]
    if specific:
        breadcrumbs.append({"label": specific})
    return breadcrumbs


def build_ga_committee_breadcrumbs(
    committee: str,
    session: str,
    page_class: str | None,
    config: Config,
    specific: str | None = None,
) -> list[dict[str, str]]:
    """Build breadcrumbs for GA committee pages.

    Pattern: Home → General Assembly → 80 → Committee → Class → Specific
    """
    base = get_base_url(config)
    committee_names = {
        "c1": "First Committee",
        "c2": "Second Committee",
        "c3": "Third Committee",
        "c4": "Fourth Committee",
        "c5": "Fifth Committee",
    }
    committee_name = committee_names.get(committee, committee.upper())
    breadcrumbs = [
        make_breadcrumb("Home", f"{base}index.html"),
        make_breadcrumb("General Assembly", f"{base}ga/plenary/{session}/index.html"),
        make_breadcrumb(session, f"{base}ga/plenary/{session}/index.html"),
        make_breadcrumb(committee_name, f"{base}ga/{committee}/{session}/index.html"),
    ]
    if page_class:
        breadcrumbs.append(
            make_breadcrumb(page_class.title(), f"{base}ga/{committee}/{session}/{page_class}/index.html")
        )
    if specific:
        breadcrumbs.append({"label": specific})
    return breadcrumbs


def build_ecosoc_breadcrumbs(
    session: str,
    body_code: str | None,
    page_class: str | None,
    config: Config,
    specific: str | None = None,
) -> list[dict[str, str]]:
    """Build breadcrumbs for ECOSOC pages.

    Pattern: Home → Economic and Social Council → 2025 → Body → Class → Specific
    """
    base = get_base_url(config)
    breadcrumbs = [
        make_breadcrumb("Home", f"{base}index.html"),
        make_breadcrumb("Economic and Social Council", f"{base}ecosoc/plenary/{session}/index.html"),
        make_breadcrumb(session, f"{base}ecosoc/plenary/{session}/index.html"),
    ]
    if body_code:
        body_names = {
            "hlpf": "High-level Political Forum",
            "csw": "Commission on the Status of Women",
            "ggim": "Committee of Experts on GGIM",
            "unff": "UN Forum on Forests",
            "ungegn": "Group of Experts on Geographical Names",
        }
        body_name = body_names.get(body_code, body_code.upper())
        breadcrumbs.append(
            make_breadcrumb(body_name, f"{base}ecosoc/{body_code}/{session}/index.html")
        )
        if page_class:
            breadcrumbs.append(
                make_breadcrumb(page_class.title(), f"{base}ecosoc/{body_code}/{session}/{page_class}/index.html")
            )
    elif page_class:
        breadcrumbs.append(
            make_breadcrumb(page_class.title(), f"{base}ecosoc/plenary/{session}/{page_class}/index.html")
        )
    if specific:
        breadcrumbs.append({"label": specific})
    return breadcrumbs


def build_conference_breadcrumbs(
    code: str,
    session: str,
    page_class: str | None,
    config: Config,
    specific: str | None = None,
) -> list[dict[str, str]]:
    """Build breadcrumbs for conference pages.

    Pattern: Home → Conference Name → 2025 → Class → Specific
    """
    base = get_base_url(config)
    conference_names = {
        "ffd4": "Fourth International Conference on Financing for Development",
        "ffd4pc": "FFD4 PrepCom",
    }
    conference_name = conference_names.get(code, code.upper())
    breadcrumbs = [
        make_breadcrumb("Home", f"{base}index.html"),
        make_breadcrumb(conference_name, f"{base}conferences/{code}/{session}/index.html"),
        make_breadcrumb(session, f"{base}conferences/{code}/{session}/index.html"),
    ]
    if page_class:
        breadcrumbs.append(
            make_breadcrumb(page_class.title(), f"{base}conferences/{code}/{session}/{page_class}/index.html")
        )
    if specific:
        breadcrumbs.append({"label": specific})
    return breadcrumbs


def build_meeting_detail_breadcrumbs(
    meeting: dict,
    session: str,
    config: Config,
) -> list[dict[str, str]]:
    """Build breadcrumbs for individual meeting page.

    Pattern: Home → General Assembly → 80 → Meetings → Meeting Name
    """
    base = get_base_url(config)
    meeting_name = meeting.get("MT_name", "Meeting")
    breadcrumbs = [
        make_breadcrumb("Home", f"{base}index.html"),
        make_breadcrumb("General Assembly", f"{base}ga/plenary/{session}/index.html"),
        make_breadcrumb(session, f"{base}ga/plenary/{session}/index.html"),
        make_breadcrumb("Meetings", f"{base}ga/plenary/{session}/meetings/index.html"),
        {"label": meeting_name},
    ]
    return breadcrumbs


def _extract_date_parts(dt_str: str) -> tuple[str, str]:
    """Extract YYMMDD and HH from datetime string.

    Handles formats like:
    - '2025-09-09T10:00:00' (ISO format)
    - '2026-06-04 10:00' (space separator)

    Returns:
        date_part: YYMMDD format (e.g., '250909')
        time_part: HH format (e.g., '09')
    """
    if not dt_str:
        return "000000", "00"

    # Handle space-separated format: '2026-06-04 10:00'
    if " " in dt_str:
        date_part_raw, time_part = dt_str.split(" ")
        parts = date_part_raw.split("-")
        if len(parts) >= 3:
            year = parts[0][2:]  # Get YY from YYYY
            month = parts[1]  # MM
            day = parts[2]  # DD
            date_part = f"{year}{month}{day}"  # YYMMDD
        else:
            date_part = "000000"
        return date_part, time_part.split(":")[0] if ":" in time_part else time_part

    # Handle ISO format: '2025-09-09T10:00:00'
    if "T" in dt_str:
        parts = dt_str.split("T")[0].split("-")
        if len(parts) >= 3:
            year = parts[0][2:]
            month = parts[1]
            day = parts[2]
            date_part = f"{year}{month}{day}"
        else:
            date_part = "000000"
        time_part = dt_str.split("T")[1].split(":")[0]
        return date_part, time_part

    return "000000", "00"


def meeting_url(meeting: dict) -> str:
    """Generate flat meeting URL like '25090910-informal-meeting-on-un80-initiative'."""
    dt_str = meeting.get("MT_dateTimeScheduleStart", "")
    date_part, time_part = _extract_date_parts(dt_str)
    name = slugify(meeting.get("MT_name", ""))[:50]
    return f"{date_part}{time_part}-{name}"


def meeting_id(meeting: dict) -> str:
    """Generate meeting folder ID like '25090910-informal-meeting-on-un80-initiative'."""
    return meeting_url(meeting)


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


def build_meeting_detail(ctx: BuildContext, base_path: str, session: str, meeting_id_str: str, meeting: dict, proposals_map: dict | None = None, resolution_map: dict | None = None) -> None:
    template = ctx.templates.get_template("meeting.html")

    rendered_steps = render_procedure_steps(meeting.get("procedureStep", []))
    steps_by_segment = group_steps_by_segment(rendered_steps)

    output = template.render(
        site=ctx.config.site,
        session=session,
        meeting=meeting,
        meeting_id=meeting_id_str,
        proposals_map=proposals_map or {},
        resolution_map=resolution_map or {},
        rendered_procedure_steps=rendered_steps,
        steps_by_segment=steps_by_segment,
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path / meeting_id_str
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_meetings_page(
    ctx: BuildContext,
    base_path: str,
    session: str,
    template_name: str = "list_meetings.html",
    parent_label: str = "General Assembly",
) -> None:
    template = ctx.templates.get_template(template_name)
    data_path = ctx.config.site.data_dir / base_path.replace("/", "/")
    meetings = load_json(data_path / "meetings.json") or []
    current_date = datetime.now().strftime("%Y-%m-%d")

    proposals_map, resolution_map = load_proposals_map(ctx.config.site.data_dir)

    output = template.render(
        site=ctx.config.site,
        session=session,
        meetings=meetings,
        current_date=current_date,
        breadcrumb_items=build_ga_breadcrumbs(session, "meetings", ctx.config),
        page_heading=f"Meetings — {session} Session",
        page_subtitle="Official meeting records and proceedings",
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path / "meetings"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")

    for meeting in meetings:
        mid = meeting_id(meeting)
        build_meeting_detail(ctx, base_path, session, mid, meeting, proposals_map, resolution_map)


def build_agenda_page(
    ctx: BuildContext,
    base_path: str,
    session: str,
    template_name: str = "list_table.html",
    parent_label: str = "General Assembly",
) -> None:
    template = ctx.templates.get_template(template_name)
    data_path = ctx.config.site.data_dir / base_path.replace("/", "/")
    agenda = load_json(data_path / "agenda.json") or []
    output = template.render(
        site=ctx.config.site,
        session=session,
        table_type="agenda",
        items=agenda,
        empty_message="No agenda data available yet.",
        breadcrumb_items=build_ga_breadcrumbs(session, "agenda", ctx.config),
        page_heading=f"Agenda — {session} Session",
        page_subtitle="Complete list of agenda items for the session",
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path / "agenda"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_consolidated_agenda_page(
    ctx: BuildContext,
    session: str,
    parent_label: str = "General Assembly",
) -> None:
    """Build a consolidated agenda page for the entire GA session.

    UNGA has one agenda for the session covering all Main Committees.
    Items show with their subheadings (AG_Heading) displayed as sub-items.
    """
    template = ctx.templates.get_template("agenda.html")
    data_path = ctx.config.site.data_dir / "ga" / "plenary" / session
    agenda = load_json(data_path / "agenda.json") or []
    grouped_items = group_agenda_items(agenda)

    output = template.render(
        site=ctx.config.site,
        session=session,
        grouped_items=grouped_items,
        empty_message="No agenda data available yet.",
        breadcrumb_items=build_ga_breadcrumbs(session, "agenda", ctx.config),
        page_heading=f"Agenda — {session} Session",
        page_subtitle="Complete list of agenda items for the session",
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / "ga" / "plenary" / session / "agenda"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_documents_page(
    ctx: BuildContext,
    base_path: str,
    session: str,
    template_name: str = "list_table.html",
    parent_label: str = "General Assembly",
) -> None:
    template = ctx.templates.get_template(template_name)
    data_path = ctx.config.site.data_dir / base_path.replace("/", "/")
    documents = load_json(data_path / "documents.json") or []

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

    output = template.render(
        site=ctx.config.site,
        session=session,
        table_type="documents",
        items=flattened,
        empty_message="No documents data available yet.",
        breadcrumb_items=build_ga_breadcrumbs(session, "documents", ctx.config),
        page_heading=f"Documents — {session} Session",
        page_subtitle="Official documents, resolutions, and reports",
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path / "documents"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_decisions_page(
    ctx: BuildContext,
    base_path: str,
    session: str,
    template_name: str = "decisions.html",
    parent_label: str = "General Assembly",
) -> None:
    template = ctx.templates.get_template(template_name)
    data_path = ctx.config.site.data_dir / base_path.replace("/", "/")
    decisions = load_json(data_path / "decisions.json") or []
    output = template.render(
        site=ctx.config.site,
        session=session,
        items=decisions,
        empty_message="No decisions data available yet.",
        breadcrumb_items=build_ga_breadcrumbs(session, "decisions", ctx.config),
        page_heading=f"Decisions — {session} Session",
        page_subtitle="Decisions adopted by the body",
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path / "decisions"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_proposals_page(
    ctx: BuildContext,
    base_path: str,
    session: str,
    template_name: str = "list_table.html",
    parent_label: str = "General Assembly",
) -> None:
    template = ctx.templates.get_template(template_name)
    data_path = ctx.config.site.data_dir / base_path.replace("/", "/")
    proposals = load_json(data_path / "proposals.json") or {"result": []}
    output = template.render(
        site=ctx.config.site,
        session=session,
        table_type="proposals",
        items=proposals.get("result", []),
        empty_message="No proposals data available yet.",
        breadcrumb_items=build_ga_breadcrumbs(session, "proposals", ctx.config),
        page_heading=f"Proposals — {session} Session",
        page_subtitle="Draft resolutions and amendments",
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path / "proposals"
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_ga_plenary(ctx: BuildContext, session_number: str) -> None:
    base_path = f"ga/plenary/{session_number}"
    template = ctx.templates.get_template("session.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number

    output = template.render(
        site=ctx.config.site,
        session=session_number,
        body="GA",
        body_name="General Assembly",
        body_description="Plenary",
        body_about="The General Assembly is the main deliberative, policymaking and representative organ of the United Nations.",
        base_path=base_path,
        breadcrumb_items=[
            make_breadcrumb("Home", f"{ctx.config.site.base_url}index.html"),
            make_breadcrumb("General Assembly", f"{ctx.config.site.base_url}ga/plenary/{session_number}/index.html"),
            make_breadcrumb(session_number, f"{ctx.config.site.base_url}ga/plenary/{session_number}/index.html"),
        ],
        stats=get_stats(data_dir),
        recent_meetings=get_recent_meetings(data_dir),
        recent_decisions=get_recent_decisions(data_dir),
        next_meeting=get_next_meeting(data_dir),
        tabs=[
            {"label": "Plenary", "url": f"{ctx.config.site.base_url}ga/plenary/{session_number}/index.html", "active": True},
            {"label": "C1", "url": f"{ctx.config.site.base_url}ga/c1/{session_number}/index.html"},
            {"label": "C2", "url": f"{ctx.config.site.base_url}ga/c2/{session_number}/index.html"},
            {"label": "C3", "url": f"{ctx.config.site.base_url}ga/c3/{session_number}/index.html"},
            {"label": "C4", "url": f"{ctx.config.site.base_url}ga/c4/{session_number}/index.html"},
            {"label": "C5", "url": f"{ctx.config.site.base_url}ga/c5/{session_number}/index.html"},
        ],
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")

    build_meetings_page(ctx, base_path, session_number, parent_label="General Assembly")
    build_consolidated_agenda_page(ctx, session_number, parent_label="General Assembly")
    build_documents_page(ctx, base_path, session_number, parent_label="General Assembly")
    build_decisions_page(ctx, base_path, session_number, parent_label="General Assembly")
    build_proposals_page(ctx, base_path, session_number, parent_label="General Assembly")


def build_ga_committee(ctx: BuildContext, committee: str, session_number: str) -> None:
    base_path = f"ga/{committee}/{session_number}"
    template = ctx.templates.get_template("session.html")
    data_dir = ctx.config.site.data_dir / "ga" / committee / session_number

    committee_info = {
        "c1": ("First Committee", "Disarmament and international security matters"),
        "c2": ("Second Committee", "Economic and financial matters"),
        "c3": ("Third Committee", "Social, humanitarian and cultural affairs"),
        "c4": ("Fourth Committee", "Special political and decolonization matters"),
        "c5": ("Fifth Committee", "Administrative and budgetary matters"),
    }

    body_name, body_description = committee_info.get(committee, (committee.upper(), ""))

    body_about = f"The {body_name} is one of the six main committees of the General Assembly. It addresses {body_description.lower()}."

    output = template.render(
        site=ctx.config.site,
        body="GA",
        body_name=body_name,
        body_description=body_description,
        body_about=body_about,
        session=session_number,
        base_path=base_path,
        breadcrumb_items=build_ga_committee_breadcrumbs(committee, session_number, None, ctx.config),
        stats=get_stats(data_dir),
        recent_meetings=get_recent_meetings(data_dir),
        recent_decisions=get_recent_decisions(data_dir),
        next_meeting=get_next_meeting(data_dir),
        tabs=[
            {"label": "Plenary", "url": f"{ctx.config.site.base_url}ga/plenary/{session_number}/index.html"},
            {"label": "C1", "url": f"{ctx.config.site.base_url}ga/c1/{session_number}/index.html", "active": committee == "c1"},
            {"label": "C2", "url": f"{ctx.config.site.base_url}ga/c2/{session_number}/index.html", "active": committee == "c2"},
            {"label": "C3", "url": f"{ctx.config.site.base_url}ga/c3/{session_number}/index.html", "active": committee == "c3"},
            {"label": "C4", "url": f"{ctx.config.site.base_url}ga/c4/{session_number}/index.html", "active": committee == "c4"},
            {"label": "C5", "url": f"{ctx.config.site.base_url}ga/c5/{session_number}/index.html", "active": committee == "c5"},
        ],
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_ecosoc_plenary(ctx: BuildContext, session: str) -> None:
    base_path = f"ecosoc/plenary/{session}"
    template = ctx.templates.get_template("session.html")
    data_dir = ctx.config.site.data_dir / "ecosoc" / "plenary" / session

    output = template.render(
        site=ctx.config.site,
        body="ECOSOC",
        body_name="Plenary",
        body_description="The plenary is the main deliberative body of the Economic and Social Council",
        body_about="The Economic and Social Council is the principal body for coordination, policy review, policy dialogue and recommendations on economic, social and environmental issues.",
        session=session,
        base_path=base_path,
        breadcrumb_items=build_ecosoc_breadcrumbs(session, None, None, ctx.config),
        stats=get_stats(data_dir),
        recent_meetings=get_recent_meetings(data_dir),
        recent_decisions=get_recent_decisions(data_dir),
        next_meeting=get_next_meeting(data_dir),
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_ecosoc_body(ctx: BuildContext, body_code: str, session: str) -> None:
    base_path = f"ecosoc/{body_code}/{session}"
    template = ctx.templates.get_template("session.html")
    data_dir = ctx.config.site.data_dir / "ecosoc" / body_code / session

    body_info = {
        "hlpf": ("High-level political forum on sustainable development", "Convened under the auspices of the Council to follow up and review the implementation of the 2030 Agenda"),
        "csw": ("Commission on the Status of Women", "Promoting women's rights and gender equality"),
        "ggim": ("Committee of Experts on Global Geospatial Information Management", "Providing a platform for the development of global geospatial information"),
        "unff": ("United Nations Forum on Forests", "International arrangement on forests"),
        "ungegn": ("United Nations Group of Experts on Geographical Names", "Standardization of geographical names"),
    }

    body_name, body_description = body_info.get(body_code, (body_code.upper(), ""))

    output = template.render(
        site=ctx.config.site,
        body="ECOSOC",
        body_name=body_name,
        body_description=body_description,
        body_about=f"The {body_name} is a body of the Economic and Social Council.",
        session=session,
        base_path=base_path,
        breadcrumb_items=build_ecosoc_breadcrumbs(session, body_code, None, ctx.config),
        stats=get_stats(data_dir),
        recent_meetings=get_recent_meetings(data_dir),
        recent_decisions=get_recent_decisions(data_dir),
        next_meeting=get_next_meeting(data_dir),
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_conference(ctx: BuildContext, code: str, session: str) -> None:
    base_path = f"conferences/{code}/{session}"
    template = ctx.templates.get_template("session.html")
    data_dir = ctx.config.site.data_dir / "conferences" / code / session

    conference_info = {
        "ffd4": ("Fourth International Conference on Financing for Development", "Accelerating implementation of the Addis Ababa Action Agenda", "The Fourth International Conference on Financing for Development will review the implementation of the Addis Ababa Action Agenda and address new and emerging topics."),
        "ffd4pc": ("FFD4 PrepCom", "Third preparatory committee session", "The third preparatory committee session for the Fourth International Conference on Financing for Development."),
    }

    conference_name, conference_session, conference_about = conference_info.get(code, (code.upper(), session, ""))
    conference_description = f"{conference_session} Session"

    output = template.render(
        site=ctx.config.site,
        body="Conferences",
        conference_name=conference_name,
        conference_description=f"{conference_session} Session",
        conference_about=conference_about,
        session=conference_session,
        body_name=conference_name,
        body_description=conference_description,
        body_about=conference_about,
        base_path=base_path,
        breadcrumb_items=build_conference_breadcrumbs(code, session, None, ctx.config),
        stats=get_stats(data_dir),
        recent_meetings=get_recent_meetings(data_dir),
        recent_decisions=get_recent_decisions(data_dir),
        next_meeting=get_next_meeting(data_dir),
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir / base_path
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def count_documents(items: list[dict[str, Any]]) -> int:
    total = 0
    for item in items:
        docs = item.get("documents") or []
        total += len(docs)
    return total


def get_stats(data_dir: Path) -> dict[str, int]:
    meetings = load_json(data_dir / "meetings.json") or []
    agenda = load_json(data_dir / "agenda.json") or []
    documents = load_json(data_dir / "documents.json") or []
    decisions = load_json(data_dir / "decisions.json") or []
    proposals = load_json(data_dir / "proposals.json") or {"result": []}
    return {
        "meetings": len(meetings),
        "agenda": len(agenda),
        "documents": count_documents(documents),
        "decisions": len(decisions),
        "proposals": len(proposals.get("result", [])),
    }


def group_agenda_items(agenda: list[dict]) -> list[dict]:
    """Group agenda items by section (AG_Heading) and nest sub-items.

    Structure:
    - Sections (A, B, C...) group multiple items
    - Items like '16(a)', '72(b)' are sub-items under parent item
    - Some items have no section (standalone procedural items)
    """
    sections: dict[str, list[dict]] = {}
    standalone_items: list[dict] = []

    for item in agenda:
        item_num = item.get("AG_Item", "").strip()
        title = item.get("AG_Title", "")
        heading = item.get("AG_Heading", "")

        item_data = {
            "item_number": item_num,
            "title": title,
            "subitems": [],
        }

        if heading:
            if heading not in sections:
                sections[heading] = []
            sections[heading].append(item_data)
        else:
            standalone_items.append(item_data)

    def process_items(items: list[dict]) -> list[dict]:
        result: list[dict] = []
        item_map: dict[str, dict] = {}

        for item in items:
            item_map[item["item_number"]] = item
            result.append(item)

        subitems_to_move: list[tuple[str, dict]] = []
        for item_num, item in item_map.items():
            if "(" in item_num and ")" in item_num:
                parent_num = item_num.split("(")[0].strip()
                if parent_num in item_map:
                    subitems_to_move.append((item_num, item_map[parent_num]))

        for subitem_num, parent in subitems_to_move:
            parent["subitems"].append(item_map[subitem_num])
            if parent in result:
                result.remove(item_map[subitem_num])

        return sorted(result, key=lambda x: float(x["item_number"]) if x["item_number"].replace(".", "", 1).isdigit() else float("inf"))

    result = []
    for heading, items in sections.items():
        result.extend(process_items(items))
    result.extend(process_items(standalone_items))

    return result


def get_recent_meetings(data_dir: Path, limit: int = 3) -> list[dict]:
    meetings = load_json(data_dir / "meetings.json") or []
    return sorted(
        meetings,
        key=lambda m: m.get("MT_dateTimeScheduleStart", ""),
        reverse=True,
    )[:limit]


def get_recent_decisions(data_dir: Path, limit: int = 3) -> list[dict]:
    decisions = load_json(data_dir / "decisions.json") or []

    def decision_date(item: dict) -> str:
        meetings = item.get("ED_Meeting") or []
        if meetings:
            return meetings[0].get("ED_Date", "")
        return ""

    return sorted(decisions, key=decision_date, reverse=True)[:limit]


def get_next_meeting(data_dir: Path) -> dict | None:
    meetings = load_json(data_dir / "meetings.json") or []
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = [m for m in meetings if m.get("MT_dateTimeScheduleStart", "")[:10] > today]
    if upcoming:
        return sorted(upcoming, key=lambda m: m["MT_dateTimeScheduleStart"])[0]
    return None


def build_home(ctx: BuildContext, session_number: str) -> None:
    template = ctx.templates.get_template("index.html")
    data_dir = ctx.config.site.data_dir / "ga" / "plenary" / session_number
    ga_session_path = f"ga/plenary/{session_number}"

    output = template.render(
        site=ctx.config.site,
        ga_session_path=ga_session_path,
        recent_meetings=get_recent_meetings(data_dir),
        recent_decisions=get_recent_decisions(data_dir),
        next_meeting=get_next_meeting(data_dir),
        last_build_timestamp=int(datetime.now().timestamp()),
    )

    output_dir = ctx.config.site.output_dir
    ensure_dir(output_dir)
    (output_dir / "index.html").write_text(output, encoding="utf-8")


def build_all(ctx: BuildContext, session_number: str) -> None:
    build_home(ctx, session_number)
    build_ga_plenary(ctx, session_number)
    for committee in ["c1", "c2", "c3", "c4", "c5"]:
        build_ga_committee(ctx, committee, session_number)
    build_ecosoc_plenary(ctx, "2026")
    for body in ["hlpf", "csw", "ggim", "unff", "ungegn"]:
        build_ecosoc_body(ctx, body, "2025")
    build_conference(ctx, "ffd4", "2025")
    build_conference(ctx, "ffd4pc", "3")
    copy_static_assets(ctx.config)
