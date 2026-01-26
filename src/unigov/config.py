from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class SessionConfig:
    number: str
    label: str
    decision_label: str


@dataclass(frozen=True)
class SiteConfig:
    title: str
    base_url: str
    output_dir: Path
    data_dir: Path


@dataclass(frozen=True)
class GaConfig:
    body_code: str
    sessions: dict[str, SessionConfig]
    committees: dict[str, str]


@dataclass(frozen=True)
class Config:
    site: SiteConfig
    ga: GaConfig


def load_config(path: Path) -> Config:
    raw = yaml.safe_load(path.read_text())
    base_dir = path.parent
    site = raw["site"]
    ga = raw["ga"]

    sessions = {
        key: SessionConfig(number=key, label=value["label"], decision_label=value["decision_label"])
        for key, value in ga["sessions"].items()
    }

    base_url = os.environ.get("BASE_URL") or site["base_url"]

    return Config(
        site=SiteConfig(
            title=site["title"],
            base_url=base_url,
            output_dir=base_dir / site["output_dir"],
            data_dir=base_dir / site["data_dir"],
        ),
        ga=GaConfig(body_code=ga["body_code"], sessions=sessions, committees=ga["committees"]),
    )
