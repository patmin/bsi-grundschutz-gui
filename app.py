from __future__ import annotations

import argparse
import getpass
from pathlib import Path
from typing import Iterable, List, Optional

from ai_helper import AIHelpStore, ApiKeyStore, fetch_ai_help
from requirements_parser import Compendium, Requirement, load_compendium
from status_store import StatusStore, VALID_STATUSES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI zum Arbeiten mit dem IT-Grundschutz-Kompendium.")
    parser.add_argument("--xml", default="XML_Kompendium_2023.xml", help="Pfad zur XML-Datei des Kompendiums.")
    parser.add_argument("--status-file", default="status.json", help="Pfad zur Status-Datei (JSON).")
    parser.add_argument("--api-key-file", default="openai_key.txt", help="Pfad zur Datei mit dem OpenAI API-Key.")
    parser.add_argument("--ai-help-file", default="ai_help_store.json", help="Pfad zur Datei fuer gespeicherte KI-Hilfen.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    modules_parser = subparsers.add_parser("modules", help="Bausteine anzeigen.")
    modules_parser.add_argument("--search", help="Nach Teilstring im Modulcode oder -titel filtern.")

    req_parser = subparsers.add_parser("requirements", help="Anforderungen eines Bausteins auflisten.")
    req_parser.add_argument("module_code", help="Bausteincode, z. B. APP.1.1.")
    req_parser.add_argument("--status", choices=VALID_STATUSES, help="Nach Status filtern.")

    show_parser = subparsers.add_parser("show", help="Details zu einer Anforderung anzeigen.")
    show_parser.add_argument("requirement_code", help="Anforderungscode, z. B. APP.1.1.A3")

    set_parser = subparsers.add_parser("set-status", help="Status fuer eine Anforderung setzen.")
    set_parser.add_argument("requirement_code", help="Anforderungscode.")
    set_parser.add_argument("status", choices=VALID_STATUSES, help="Neuer Status.")
    set_parser.add_argument("--note", help="Optionaler Kommentar.")

    list_parser = subparsers.add_parser("statuses", help="Alle gesetzten Status anzeigen.")
    list_parser.add_argument("--status", choices=VALID_STATUSES, help="Nur bestimmte Status anzeigen.")

    api_parser = subparsers.add_parser("set-api-key", help="OpenAI API-Key speichern.")
    api_parser.add_argument("--key", help="Optional: API-Key direkt uebergeben.")

    ai_parser = subparsers.add_parser("ai-help", help="KI-Hilfe generieren und speichern.")
    ai_parser.add_argument("requirement_code", help="Anforderungscode.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    compendium = load_compendium(Path(args.xml))
    status_store = StatusStore(Path(args.status_file))
    api_key_store = ApiKeyStore(Path(args.api_key_file))
    ai_help_store = AIHelpStore(Path(args.ai_help_file))

    if args.command == "modules":
        _cmd_modules(compendium, status_store, args.search)
    elif args.command == "requirements":
        _cmd_requirements(compendium, status_store, args.module_code, args.status)
    elif args.command == "show":
        _cmd_show(compendium, status_store, ai_help_store, args.requirement_code)
    elif args.command == "set-status":
        _cmd_set_status(compendium, status_store, args.requirement_code, args.status, args.note)
    elif args.command == "statuses":
        _cmd_statuses(compendium, status_store, args.status)
    elif args.command == "set-api-key":
        _cmd_set_api_key(api_key_store, args.key)
    elif args.command == "ai-help":
        _cmd_ai_help(compendium, api_key_store, ai_help_store, args.requirement_code)
    else:
        parser.print_help()


def _cmd_modules(compendium: Compendium, store: StatusStore, search: Optional[str]) -> None:
    search_lower = search.lower() if search else None
    for module in compendium.modules.values():
        if search_lower and search_lower not in module.code.lower() and search_lower not in module.title.lower():
            continue
        total = len(module.requirements)
        done = sum(1 for req in module.requirements if store.get_status(req.code) == "done")
        in_progress = sum(1 for req in module.requirements if store.get_status(req.code) == "in_progress")
        print(f"{module.code:<10} {module.title} [{done}/{total} erledigt, {in_progress} in Arbeit] - {module.chapter}")


def _cmd_requirements(
    compendium: Compendium,
    store: StatusStore,
    module_code: str,
    status_filter: Optional[str],
) -> None:
    module = compendium.get_module(module_code)
    if module is None:
        print(f"Baustein {module_code} nicht gefunden.")
        return

    print(f"{module.code} - {module.title} ({module.chapter})")
    for req in module.requirements:
        current_status = store.get_status(req.code) or "open"
        if status_filter and current_status != status_filter:
            continue
        print(f"  {req.code}: {req.title} ({req.level}) - Status: {current_status}")


def _cmd_show(compendium: Compendium, store: StatusStore, ai_help_store: AIHelpStore, requirement_code: str) -> None:
    req = compendium.get_requirement(requirement_code)
    if req is None:
        print(f"Anforderung {requirement_code} nicht gefunden.")
        return

    status = store.get(requirement_code) or {}
    print(f"{req.code} - {req.title}")
    print(f"Kapitel: {req.chapter} | Baustein: {req.module_code} {req.module_title}")
    print(f"Level: {req.level} | Rollen: {', '.join(req.roles) if req.roles else '---'}")
    print(f"Status: {status.get('status', 'open')} | Notiz: {status.get('note', '-')}")
    print("\nBeschreibung:")
    print(req.description or "(Kein Beschreibungstext gefunden.)")
    print("\nKI Hilfe:")
    help_text = ai_help_store.get_help(req.code)
    if help_text:
        print(help_text)
    else:
        print(f"Keine KI-Hilfe gespeichert. Verwende 'python app.py ai-help {req.code}' oder den Button in der GUI-Schaltflaeche.")


def _cmd_set_status(
    compendium: Compendium,
    store: StatusStore,
    requirement_code: str,
    status: str,
    note: Optional[str],
) -> None:
    req = compendium.get_requirement(requirement_code)
    if req is None:
        print(f"Anforderung {requirement_code} nicht gefunden.")
        return
    store.set_status(requirement_code, status, note)
    store.save()
    print(f"Status fuer {requirement_code} aktualisiert: {status}")



def _cmd_set_api_key(api_key_store: ApiKeyStore, key_arg: Optional[str]) -> None:
    key = key_arg or getpass.getpass("OpenAI API-Key: ")
    key = (key or "").strip()
    if not key:
        print("Kein API-Key angegeben.")
        return
    api_key_store.save_key(key)
    print("API-Key gespeichert.")


def _cmd_ai_help(
    compendium: Compendium,
    api_key_store: ApiKeyStore,
    help_store: AIHelpStore,
    requirement_code: str,
) -> None:
    req = compendium.get_requirement(requirement_code)
    if req is None:
        print(f"Anforderung {requirement_code} nicht gefunden.")
        return
    api_key = api_key_store.load_key()
    if not api_key:
        print("Kein API-Key gespeichert. Bitte zuerst 'python app.py set-api-key' ausfuehren.")
        return
    try:
        content = fetch_ai_help(req, api_key)
    except RuntimeError as error:
        print(f"Fehler bei der KI-Abfrage: {error}")
        return
    help_store.save_help(req.code, content)
    print("KI-Hilfe gespeichert.")
    print(content)

def _cmd_statuses(compendium: Compendium, store: StatusStore, status_filter: Optional[str]) -> None:
    for req_code, data in store.iter_statuses():
        if status_filter and data.get("status") != status_filter:
            continue
        req = compendium.get_requirement(req_code)
        title = req.title if req else "Unbekannte Anforderung"
        print(f"{req_code}: {title} - Status: {data.get('status')} - Notiz: {data.get('note', '-')}")


if __name__ == "__main__":
    main()


