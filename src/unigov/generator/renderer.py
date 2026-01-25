from __future__ import annotations

from pathlib import Path
import yaml
import re
from typing import Any, Optional

_templates_cache: Optional[dict] = None

UN_OFFICIAL_COUNTRY_NAMES = {
    "ARGENTINA": "Argentina",
    "AUSTRALIA": "Australia",
    "AZERBAIJAN": "Azerbaijan",
    "BELARUS": "Belarus",
    "BELARUS ": "Belarus",
    "BOLIVARIAN REPUBLIC OF": "Bolivarian Republic of",
    "CAMBODIA": "Cambodia",
    "CANADA": "Canada",
    "CHINA": "China",
    "CROATIA": "Croatia",
    "CUBA": "Cuba",
    "DENMARK": "Denmark",
    "EGYPT": "Egypt",
    "EL SALVADOR": "El Salvador",
    "EUROPEAN UNION": "European Union",
    "FRANCE": "France",
    "HUNGARY": "Hungary",
    "INDONESIA": "Indonesia",
    "INTERNATIONAL COMMITTEE OF THE RED CROSS": "International Committee of the Red Cross",
    "INTERNATIONAL FEDERATION OF RED CROSS AND RED CRESCENT SOCIETIES": "International Federation of Red Cross and Red Crescent Societies",
    "IRAN": "Iran",
    "ISLAMIC REPUBLIC OF": "Islamic Republic of",
    "IRAQ": "Iraq",
    "ISRAEL": "Israel",
    "KAZAKHSTAN": "Kazakhstan",
    "KINGDOM OF THE": "Kingdom of the",
    "MALDIVES": "Maldives",
    "MEXICO": "Mexico",
    "MOROCCO": "Morocco",
    "NETHERLANDS": "Netherlands",
    "NEW ZEALAND": "New Zealand",
    "NICARAGUA": "Nicaragua",
    "NORWAY": "Norway",
    "PAKISTAN": "Pakistan",
    "PARAGUAY": "Paraguay",
    "POLAND": "Poland",
    "QATAR": "Qatar",
    "RUSSIAN FEDERATION": "Russian Federation",
    "SERBIA": "Serbia",
    "SLOVAKIA": "Slovakia",
    "SPAIN": "Spain",
    "SWITZERLAND": "Switzerland",
    "SWITZERLAND ": "Switzerland",
    "THAILAND": "Thailand",
    "TIMOR-LESTE": "Timor-Leste",
    "TÜRKİYE": "Türkiye",
    "TURKIYE": "Türkiye",
    "UKRAINE": "Ukraine",
    "UNITED ARAB EMIRATES": "United Arab Emirates",
    "UNITED KINGDOM": "United Kingdom",
    "UNITED KINGDOM ": "United Kingdom",
    "UNITED STATES": "United States",
    "UNITED STATES ": "United States",
    "VENEZUELA": "Venezuela",
    "VENEZUELA (BOLIVARIAN REPUBLIC OF)": "Venezuela (Bolivarian Republic of)",
}


def normalize_country_name(name: str) -> str:
    name = name.strip()

    parenthesized = ""
    if "(" in name and name.endswith(")"):
        paren_start = name.rfind("(")
        parenthesized = name[paren_start:]
        name = name[:paren_start].strip()

    name_upper = name.upper()
    if name_upper in UN_OFFICIAL_COUNTRY_NAMES:
        name = UN_OFFICIAL_COUNTRY_NAMES[name_upper]

    if parenthesized:
        normalized_paren = parenthesized
        for upper_name, official in UN_OFFICIAL_COUNTRY_NAMES.items():
            if upper_name in parenthesized.upper():
                normalized_paren = re.sub(
                    re.escape(upper_name),
                    official,
                    normalized_paren,
                    flags=re.IGNORECASE,
                )
        name = f"{name} {normalized_paren}"

    return name


def get_templates_path() -> Path:
    return Path(__file__).parent.parent.parent.parent / "templates" / "procedure_steps.yaml"


def load_templates() -> dict:
    global _templates_cache
    if _templates_cache is None:
        path = get_templates_path()
        with open(path) as f:
            _templates_cache = yaml.safe_load(f)
    assert _templates_cache is not None
    return _templates_cache


def get_field(data: Any, path: str) -> Any:
    keys = path.split(".")
    value = data
    for key in keys:
        if value is None:
            return ""
        if isinstance(value, list):
            try:
                idx = int(key)
                value = value[idx] if idx < len(value) else ""
            except ValueError:
                return ""
        elif isinstance(value, dict):
            value = value.get(key, "")
        else:
            return ""
        if value is None:
            return ""
    return value


def transform_value(value: str, transforms: list[str]) -> str:
    for t in transforms:
        if t.startswith("strip_prefix:"):
            prefix = t.split(":", 1)[1]
            if value.startswith(prefix):
                value = value[len(prefix):]
        elif t.startswith("strip_suffix:"):
            suffix = t.split(":", 1)[1]
            if value.endswith(suffix):
                value = value[:-len(suffix)]
    return value


def check_condition(step: dict, condition: dict) -> bool:
    for key, expected in condition.items():
        actual = get_field(step, key)
        if expected == "present":
            if not actual:
                return False
        elif actual != expected:
            return False
    return True


def render_step_text(step: dict, template: str, fields: dict) -> str:
    text = template
    for placeholder, field_config in fields.items():
        if isinstance(field_config, dict):
            path = field_config.get("path", "")
            transforms = field_config.get("transform", [])
            if isinstance(transforms, str):
                transforms = [transforms]
            value = get_field(step, path)
            if value:
                value = transform_value(str(value), transforms)
        else:
            value = get_field(step, field_config)
        text = text.replace(f"{{{placeholder}}}", str(value) if value else "")
    return text


def render_step_speakers(step: dict, speakers_config: dict) -> list[dict]:
    speakers = []
    path = speakers_config.get("path", "")
    name_field = speakers_config.get("name_field", "SP_entity.SP_entity")
    raw_speakers = get_field(step, path)
    if isinstance(raw_speakers, list):
        for sp in raw_speakers:
            name = get_field(sp, name_field)
            if name and not name.startswith("------"):
                name = normalize_country_name(name)
                speakers.append({"name": name})
    return speakers


def to_title_case(text: str) -> str:
    small_words = {"a", "an", "the", "of", "and", "or", "in", "on", "at", "to", "for", "by", "with", "of"}
    result = []
    for i, word in enumerate(text.split()):
        if word.lower() in small_words and i > 0:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    return " ".join(result)


def render_step(step: dict, templates: dict) -> dict:
    step_type = step.get("PS_type_label", "")
    template_config = templates.get(step_type, [])

    variants = []
    if isinstance(template_config, list):
        variants = template_config
    elif isinstance(template_config, dict):
        variants = [template_config]

    for variant in variants:
        condition = variant.get("condition", {})
        if condition and not check_condition(step, condition):
            continue

        template = variant.get("template", "")
        fields = variant.get("fields", {})
        speakers_config = variant.get("speakers", {})

        text = render_step_text(step, template, fields)
        speakers = render_step_speakers(step, speakers_config) if speakers_config else []

        text = text.strip()
        if not text:
            text = step.get("PS_title", "").strip()

        return {
            "type_label": step_type,
            "text": text,
            "speakers": speakers,
            "seqNo": step.get("seqNo"),
        }

    fallback = step.get("PS_title", "").strip() or step_type
    return {
        "type_label": step_type,
        "text": fallback,
        "speakers": [],
        "seqNo": step.get("seqNo"),
    }


def render_procedure_steps(steps: list[dict]) -> list[dict]:
    templates = load_templates()
    return [render_step(step, templates) for step in steps]


def get_step_segment_id(step: dict) -> int:
    """Extract segment number from step seqNo (e.g., '1.03' -> 1, '2.01' -> 2)."""
    seq_no = step.get("seqNo", "")
    if isinstance(seq_no, (int, float)):
        return int(seq_no)
    if isinstance(seq_no, str):
        parts = seq_no.split(".")
        if parts:
            try:
                return int(float(parts[0]))
            except ValueError:
                return 0
    return 0


def group_steps_by_segment(steps: list[dict]) -> dict[int, list[dict]]:
    """Group rendered steps by their segment ID."""
    groups: dict[int, list[dict]] = {}
    for step in steps:
        seg_id = get_step_segment_id(step)
        if seg_id not in groups:
            groups[seg_id] = []
        groups[seg_id].append(step)
    return groups
