from __future__ import annotations

from pathlib import Path
import yaml
import re
from typing import Any, Optional

_templates_cache: Optional[dict] = None

UN_OFFICIAL_COUNTRY_NAMES = {
    "AFGHANISTAN": "Afghanistan",
    "ALBANIA": "Albania",
    "ALGERIA": "Algeria",
    "ANDORRA": "Andorra",
    "ANGOLA": "Angola",
    "ANTIGUA AND BARBUDA": "Antigua and Barbuda",
    "ARGENTINA": "Argentina",
    "ARMENIA": "Armenia",
    "AUSTRALIA": "Australia",
    "AUSTRIA": "Austria",
    "AZERBAIJAN": "Azerbaijan",
    "BAHAMAS": "Bahamas",
    "BAHRAIN": "Bahrain",
    "BANGLADESH": "Bangladesh",
    "BARBADOS": "Barbados",
    "BELARUS": "Belarus",
    "BELARUS ": "Belarus",
    "BELGIUM": "Belgium",
    "BELIZE": "Belize",
    "BENIN": "Benin",
    "BHUTAN": "Bhutan",
    "BOLIVARIAN REPUBLIC OF": "Bolivarian Republic of",
    "BOLIVIA": "Bolivia",
    "BOSNIA AND HERZEGOVINA": "Bosnia and Herzegovina",
    "BOTSWANA": "Botswana",
    "BRAZIL": "Brazil",
    "BRUNEI DARUSSALAM": "Brunei Darussalam",
    "BULGARIA": "Bulgaria",
    "BURKINA FASO": "Burkina Faso",
    "BURUNDI": "Burundi",
    "CABO VERDE": "Cabo Verde",
    "CAMBODIA": "Cambodia",
    "CAMEROON": "Cameroon",
    "CANADA": "Canada",
    "CENTRAL AFRICAN REPUBLIC": "Central African Republic",
    "CHAD": "Chad",
    "CHILE": "Chile",
    "CHINA": "China",
    "COLOMBIA": "Colombia",
    "COMOROS": "Comoros",
    "CONGO": "Congo",
    "COSTA RICA": "Costa Rica",
    "CÔTE D'IVOIRE": "Côte d'Ivoire",
    "CROATIA": "Croatia",
    "CUBA": "Cuba",
    "CYPRUS": "Cyprus",
    "CZECHIA": "Czechia",
    "CZECH REPUBLIC": "Czechia",
    "DEMOCRATIC PEOPLE'S REPUBLIC OF KOREA": "Democratic People's Republic of Korea",
    "DEMOCRATIC REPUBLIC OF THE CONGO": "Democratic Republic of the Congo",
    "DENMARK": "Denmark",
    "DJIBOUTI": "Djibouti",
    "DOMINICA": "Dominica",
    "DOMINICAN REPUBLIC": "Dominican Republic",
    "ECUADOR": "Ecuador",
    "EGYPT": "Egypt",
    "EL SALVADOR": "El Salvador",
    "EQUATORIAL GUINEA": "Equatorial Guinea",
    "ERITREA": "Eritrea",
    "ESTONIA": "Estonia",
    "ESWATINI": "Eswatini",
    "ETHIOPIA": "Ethiopia",
    "EUROPEAN UNION": "European Union",
    "FIJI": "Fiji",
    "FINLAND": "Finland",
    "FRANCE": "France",
    "GABON": "Gabon",
    "GAMBIA": "Gambia",
    "GEORGIA": "Georgia",
    "GERMANY": "Germany",
    "GHANA": "Ghana",
    "GREECE": "Greece",
    "GRENADA": "Grenada",
    "GUATEMALA": "Guatemala",
    "GUINEA": "Guinea",
    "GUINEA-BISSAU": "Guinea-Bissau",
    "GUYANA": "Guyana",
    "HAITI": "Haiti",
    "HONDURAS": "Honduras",
    "HUNGARY": "Hungary",
    "ICELAND": "Iceland",
    "INDIA": "India",
    "INDONESIA": "Indonesia",
    "IRAN": "Iran",
    "ISLAMIC REPUBLIC OF": "Islamic Republic of",
    "IRAQ": "Iraq",
    "IRELAND": "Ireland",
    "ISRAEL": "Israel",
    "ITALY": "Italy",
    "JAMAICA": "Jamaica",
    "JAPAN": "Japan",
    "JORDAN": "Jordan",
    "KAZAKHSTAN": "Kazakhstan",
    "KENYA": "Kenya",
    "KINGDOM OF THE": "Kingdom of the",
    "KIRIBATI": "Kiribati",
    "KUWAIT": "Kuwait",
    "KYRGYZSTAN": "Kyrgyzstan",
    "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "Lao People's Democratic Republic",
    "LATVIA": "Latvia",
    "LEBANON": "Lebanon",
    "LESOTHO": "Lesotho",
    "LIBERIA": "Liberia",
    "LIBYA": "Libya",
    "LIECHTENSTEIN": "Liechtenstein",
    "LITHUANIA": "Lithuania",
    "LUXEMBOURG": "Luxembourg",
    "MADAGASCAR": "Madagascar",
    "MALAWI": "Malawi",
    "MALAYSIA": "Malaysia",
    "MALDIVES": "Maldives",
    "MALI": "Mali",
    "MALTA": "Malta",
    "MARSHALL ISLANDS": "Marshall Islands",
    "MAURITANIA": "Mauritania",
    "MAURITIUS": "Mauritius",
    "MEXICO": "Mexico",
    "MICRONESIA": "Micronesia",
    "MONACO": "Monaco",
    "MONGOLIA": "Mongolia",
    "MONTENEGRO": "Montenegro",
    "MOROCCO": "Morocco",
    "MOZAMBIQUE": "Mozambique",
    "MYANMAR": "Myanmar",
    "NAMIBIA": "Namibia",
    "NAURU": "Nauru",
    "NEPAL": "Nepal",
    "NETHERLANDS": "Netherlands",
    "NEW ZEALAND": "New Zealand",
    "NICARAGUA": "Nicaragua",
    "NIGER": "Niger",
    "NIGERIA": "Nigeria",
    "NORTH MACEDONIA": "North Macedonia",
    "NORWAY": "Norway",
    "OMAN": "Oman",
    "PAKISTAN": "Pakistan",
    "PALAU": "Palau",
    "PANAMA": "Panama",
    "PAPUA NEW GUINEA": "Papua New Guinea",
    "PARAGUAY": "Paraguay",
    "PERU": "Peru",
    "PHILIPPINES": "Philippines",
    "POLAND": "Poland",
    "PORTUGAL": "Portugal",
    "QATAR": "Qatar",
    "REPUBLIC OF KOREA": "Republic of Korea",
    "REPUBLIC OF MOLDOVA": "Republic of Moldova",
    "ROMANIA": "Romania",
    "RUSSIAN FEDERATION": "Russian Federation",
    "RWANDA": "Rwanda",
    "SAINT KITTS AND NEVIS": "Saint Kitts and Nevis",
    "SAINT LUCIA": "Saint Lucia",
    "SAINT VINCENT AND THE GRENADINES": "Saint Vincent and the Grenadines",
    "SAMOA": "Samoa",
    "SAN MARINO": "San Marino",
    "SAO TOME AND PRINCIPE": "São Tomé and Príncipe",
    "SAUDI ARABIA": "Saudi Arabia",
    "SENEGAL": "Senegal",
    "SERBIA": "Serbia",
    "SEYCHELLES": "Seychelles",
    "SIERRA LEONE": "Sierra Leone",
    "SINGAPORE": "Singapore",
    "SLOVAKIA": "Slovakia",
    "SLOVENIA": "Slovenia",
    "SOLOMON ISLANDS": "Solomon Islands",
    "SOMALIA": "Somalia",
    "SOUTH AFRICA": "South Africa",
    "SOUTH SUDAN": "South Sudan",
    "SPAIN": "Spain",
    "SRI LANKA": "Sri Lanka",
    "SUDAN": "Sudan",
    "SURINAME": "Suriname",
    "SWEDEN": "Sweden",
    "SWITZERLAND": "Switzerland",
    "SWITZERLAND ": "Switzerland",
    "SYRIAN ARAB REPUBLIC": "Syrian Arab Republic",
    "TAJIKISTAN": "Tajikistan",
    "THAILAND": "Thailand",
    "TIMOR-LESTE": "Timor-Leste",
    "TOGO": "Togo",
    "TONGA": "Tonga",
    "TRINIDAD AND TOBAGO": "Trinidad and Tobago",
    "TUNISIA": "Tunisia",
    "TÜRKİYE": "Türkiye",
    "TURKIYE": "Türkiye",
    "TURKMENISTAN": "Turkmenistan",
    "TUVALU": "Tuvalu",
    "UGANDA": "Uganda",
    "UKRAINE": "Ukraine",
    "UNITED ARAB EMIRATES": "United Arab Emirates",
    "UNITED KINGDOM": "United Kingdom",
    "UNITED KINGDOM ": "United Kingdom",
    "UNITED REPUBLIC OF TANZANIA": "United Republic of Tanzania",
    "UNITED STATES": "United States",
    "UNITED STATES ": "United States",
    "URUGUAY": "Uruguay",
    "UZBEKISTAN": "Uzbekistan",
    "VANUATU": "Vanuatu",
    "VENEZUELA": "Venezuela",
    "VENEZUELA (BOLIVARIAN REPUBLIC OF)": "Venezuela (Bolivarian Republic of)",
    "VIET NAM": "Viet Nam",
    "YEMEN": "Yemen",
    "ZAMBIA": "Zambia",
    "ZIMBABWE": "Zimbabwe",
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
