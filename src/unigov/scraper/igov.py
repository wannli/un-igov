from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://igov.un.org/igov/api"


class IGovClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def get(self, path: str) -> Any:
        response = self._client.get(f"{BASE_URL}/{path}")
        response.raise_for_status()
        return response.json()

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        response = self._client.post(f"{BASE_URL}/{path}", json=payload)
        response.raise_for_status()
        return response.json()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def fetch_ga_meetings(client: IGovClient, session_label: str) -> Any:
    return client.get(f"meetings/getbysession/{session_label}?body=GA")


def fetch_ga_agenda(client: IGovClient, session_number: str) -> Any:
    return client.get(f"getlookups/getAgendas/{session_number}")


def fetch_ga_documents(client: IGovClient, session_label: str) -> Any:
    return client.get(f"meetings/getdocumentsbysession/{session_label}?body=GA")


def fetch_ga_decisions(client: IGovClient, decision_label: str) -> Any:
    return client.get(f"decision/getbysession/{decision_label}")


def fetch_ga_proposals(client: IGovClient, session_label: str, committee_name: str) -> Any:
    committee_value = httpx.QueryParams({"c": committee_name}).get("c")
    return client.get(f"proposals/{session_label}/{committee_value}?env=prod")


def scrape_ga_session(
    data_root: Path,
    session_number: str,
    session_label: str,
    decision_label: str,
    committees: dict[str, str],
    categories: set[str],
) -> None:
    client = IGovClient()
    try:
        plenary_dir = data_root / "ga" / "plenary" / session_number
        ensure_dir(plenary_dir)

        if "meetings" in categories:
            meetings = fetch_ga_meetings(client, session_label)
            write_json(plenary_dir / "meetings.json", meetings)

        if "agenda" in categories:
            agenda = fetch_ga_agenda(client, session_number)
            write_json(plenary_dir / "agenda.json", agenda)

        if "documents" in categories:
            documents = fetch_ga_documents(client, session_label)
            write_json(plenary_dir / "documents.json", documents)

        if "decisions" in categories:
            decisions = fetch_ga_decisions(client, decision_label)
            write_json(plenary_dir / "decisions.json", decisions)

        if "proposals" in categories:
            proposals = fetch_ga_proposals(client, session_label, "GA")
            write_json(plenary_dir / "proposals.json", proposals)
            for code, name in committees.items():
                committee_dir = data_root / "ga" / code / session_number
                ensure_dir(committee_dir)
                committee_payload = fetch_ga_proposals(client, session_label, name)
                write_json(committee_dir / "proposals.json", committee_payload)
    finally:
        client.close()
