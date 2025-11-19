from __future__ import annotations

import json
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional

from requirements_parser import Requirement

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-mini"


class ApiKeyStore:
    def __init__(self, path: Path):
        self.path = path

    def save_key(self, key: str) -> None:
        self.path.write_text(key.strip(), encoding="utf-8")

    def load_key(self) -> Optional[str]:
        if self.path.exists():
            key = self.path.read_text(encoding="utf-8").strip()
            return key or None
        return None


class AIHelpStore:
    def __init__(self, path: Path):
        self.path = path
        self._data: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self._data = {}

    def save_help(self, requirement_code: str, content: str) -> None:
        self._data[requirement_code] = content
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_help(self, requirement_code: str) -> Optional[str]:
        return self._data.get(requirement_code)


def build_prompt(requirement: Requirement) -> str:
    description = requirement.description or "Keine Beschreibung im XML gefunden."
    prompt = f"""
    Du bist ein erfahrener Informationssicherheits-Berater. 
    Erkläre Schritt für Schritt, wie ein Unternehmen die folgende IT-Grundschutz-Anforderung theoretisch und technisch umsetzen kann.

    Kapitel: {requirement.chapter}
    Baustein: {requirement.module_code} {requirement.module_title}
    Anforderung: {requirement.code} - {requirement.title} (Level {requirement.level})
    Beschreibung:
    {description}

    Gliedere in theoretisch (Policies, Überlegungen etc.) und technische Umsetzung via z.B. GPO
    
    Schreibe auf Deutsch, halte dich kurz, klar strukturiert mit Aufzählungen. Kein Markup!
    """
    return textwrap.dedent(prompt).strip()


def fetch_ai_help(requirement: Requirement, api_key: str) -> str:
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "Du bist ein hilfreicher deutschsprachiger Sicherheitsberater."},
            {"role": "user", "content": build_prompt(requirement)},
        ],
        "temperature": 0.4,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_CHAT_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as http_error:
        detail = http_error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI HTTP-Fehler: {http_error.code} {http_error.reason} – {detail}") from http_error
    except urllib.error.URLError as url_error:
        raise RuntimeError(f"Netzwerkfehler beim Abruf der KI-Hilfe: {url_error}") from url_error

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as parse_error:
        raise RuntimeError(f"Antwort der KI konnte nicht interpretiert werden: {body}") from parse_error

    return content.strip()
