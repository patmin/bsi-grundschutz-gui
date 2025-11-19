from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional

from practice_guidance import generate_practical_hints
from requirements_parser import Compendium, Requirement, load_compendium
from status_store import StatusStore, VALID_STATUSES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI zum Arbeiten mit dem IT-Grundschutz-Kompendium.")
    parser.add_argument("--xml", default="XML_Kompendium_2023.xml", help="Pfad zur XML-Datei des Kompendiums.")
    parser.add_argument("--status-file", default="status.json", help="Pfad zur Status-Datei (JSON).")

    subparsers = parser.add_subparsers(dest="command", required=True)

    modules_parser = subparsers.add_parser("modules", help="Bausteine anzeigen.")
    modules_parser.add_argument("--search", help="Nach Teilstring im Modulcode oder -titel filtern.")

    req_parser = subparsers.add_parser("requirements", help="Anforderungen eines Bausteins auflisten.")
    req_parser.add_argument("module_code", help="Bausteincode, z. B. APP.1.1.")
    req_parser.add_argument("--status", choices=VALID_STATUSES, help="Nach Status filtern.")

    show_parser = subparsers.add_parser("show", help="Details zu einer Anforderung anzeigen.")
    show_parser.add_argument("requirement_code", help="Anforderungscode, z. B. APP.1.1.A3")

    set_parser = subparsers.add_parser("set-status", help="Status fÃ¼r eine Anforderung setzen.")
    set_parser.add_argument("requirement_code", help="Anforderungscode.")
    set_parser.add_argument("status", choices=VALID_STATUSES, help="Neuer Status.")
    set_parser.add_argument("--note", help="Optionaler Kommentar.")

    list_parser = subparsers.add_parser("statuses", help="Alle gesetzten Status anzeigen.")
    list_parser.add_argument("--status", choices=VALID_STATUSES, help="Nur bestimmte Status anzeigen.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    compendium = load_compendium(Path(args.xml))
    status_store = StatusStore(Path(args.status_file))

    if args.command == "modules":
        _cmd_modules(compendium, status_store, args.search)
    elif args.command == "requirements":
        _cmd_requirements(compendium, status_store, args.module_code, args.status)
    elif args.command == "show":
        _cmd_show(compendium, status_store, args.requirement_code)
    elif args.command == "set-status":
        _cmd_set_status(compendium, status_store, args.requirement_code, args.status, args.note)
    elif args.command == "statuses":
        _cmd_statuses(compendium, status_store, args.status)
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


def _cmd_show(compendium: Compendium, store: StatusStore, requirement_code: str) -> None:
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
    print("\nPraxis-Impulse:")
    for hint in generate_practical_hints(req):
        print(f"  - {hint}")


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
    print(f"Status fÃ¼r {requirement_code} aktualisiert: {status}")


def _cmd_statuses(compendium: Compendium, store: StatusStore, status_filter: Optional[str]) -> None:
    for req_code, data in store.iter_statuses():
        if status_filter and data.get("status") != status_filter:
            continue
        req = compendium.get_requirement(req_code)
        title = req.title if req else "Unbekannte Anforderung"
        print(f"{req_code}: {title} - Status: {data.get('status')} - Notiz: {data.get('note', '-')}")


if __name__ == "__main__":
    main()

