from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

VALID_STATUSES = ["open", "in_progress", "done", "not_applicable"]


class StatusStore:
    def __init__(self, path: Path):
        self.path = path
        self._data: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as handle:
                try:
                    self._data = json.load(handle)
                except json.JSONDecodeError:
                    self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2, ensure_ascii=False)

    def get(self, requirement_code: str) -> Optional[Dict[str, str]]:
        return self._data.get(requirement_code)

    def get_status(self, requirement_code: str) -> Optional[str]:
        record = self.get(requirement_code)
        if record:
            return record.get("status")
        return None

    def set_status(self, requirement_code: str, status: str, note: Optional[str] = None) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"UngÃ¼ltiger Status: {status}. Erlaubt: {', '.join(VALID_STATUSES)}")

        self._data[requirement_code] = {"status": status}
        if note is not None:
            self._data[requirement_code]["note"] = note

    def iter_statuses(self):
        for req_code, data in sorted(self._data.items()):
            yield req_code, data


