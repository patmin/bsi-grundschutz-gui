from __future__ import annotations

from typing import List

from requirements_parser import Requirement

LEVEL_HINTS = {
    "B": "Basis-Anforderung: definiere verbindliche MindestmaÃŸnahmen, dokumentiere Verantwortlichkeiten und setze diese als festen Bestandteil des ISMS um.",
    "S": "Standard-Anforderung: ergÃ¤nze die bestehenden Basis-MaÃŸnahmen um proaktive Prozesse, regelmÃ¤ÃŸige WirksamkeitsprÃ¼fungen und belastbare Nachweise.",
    "H": "Hoch-Anforderung: plane zusÃ¤tzliche Schutzschichten fÃ¼r hohen Schutzbedarf, trenne Aufgaben konsequent und sorge fÃ¼r vertieftes Monitoring.",
    "E": "ErgÃ¤nzende Anforderung",
}

KEYWORD_HINTS = [
    ("Planung", "Lege Scope, Zeitplan und benÃ¶tigte Ressourcen schriftlich fest und stimme sie mit den betroffenen Rollen ab."),
    ("Konfiguration", "Halte Soll-Konfigurationen versioniert fest und setze sie automatisiert (z. B. IaC, Gruppenrichtlinien, Ansible) um."),
    ("Monitoring", "Integriere den Punkt in das zentrale Monitoring bzw. SIEM und definiere konkrete Schwellenwerte und Reaktionsprozesse."),
    ("Protokollierung", "Aktiviere aussagekrÃ¤ftige Logquellen, sichere sie manipulationsgeschÃ¼tzt und werte sie regelmÃ¤ÃŸig aus."),
    ("Schulung", "Plane zielgruppenspezifische Schulungen bzw. Awareness-Formate und dokumentiere Teilnahme sowie Lerninhalte."),
    ("Test", "Hinterlege TestfÃ¤lle oder Abnahmekriterien und fÃ¼hre sie vor Produktivsetzung sowie nach Ã„nderungen erneut durch."),
    ("Netz", "ÃœberprÃ¼fe Netzsegmente, Firewall-Regeln und ggf. NAC-Policies, dokumentiere Freigaben und setze das Prinzip minimaler Rechte um."),
    ("Zugriff", "Setze Rollen- und Berechtigungskonzepte technisch durch, nutze Mehrfaktorauthentisierung und Ã¼berprÃ¼fe Freigaben zyklisch."),
    ("Notfall", "Aktualisiere Notfall- und WiederanlaufplÃ¤ne, teste Szenarien regelmÃ¤ÃŸig und halte Kommunikationsketten bereit."),
    ("Dokumentation", "FÃ¼hre eine nachvollziehbare Dokumentation (Versionierung, Ã„nderungsdatum, Genehmigungen), damit Audits den Status bewerten kÃ¶nnen."),
]


def generate_practical_hints(req: Requirement) -> List[str]:
    if "ENTFALLEN" in req.title.upper():
        return [
            "Dieser Punkt ist laut Kompendium entfallen. Dokumentiere nachvollziehbar, warum die Anforderung nicht mehr umzusetzen ist, und verweise auf die Edition 2023.",
            "Falls AltmaÃŸnahmen betroffen sind, halte eine kontrollierte Stilllegung bzw. Migration fest.",
        ]

    hints: List[str] = []
    level_hint = LEVEL_HINTS.get(req.level, "")
    if level_hint:
        hints.append(level_hint)

    if req.roles:
        hints.append(
            f"Binde die genannten Rollen ({', '.join(req.roles)}) mit klaren Aufgaben, Freigaben und Nachweisen ein."
        )

    title_lower = req.title.lower()
    description_lower = (req.description or "").lower()
    for keyword, hint_text in KEYWORD_HINTS:
        if keyword.lower() in title_lower or keyword.lower() in description_lower:
            hints.append(hint_text)

    if not hints:
        hints.append("Analysiere den Originaltext und leite konkrete Arbeitspakete (Policy, Prozess, Technik, Kontrolle) ab.")

    fallback_sentences = _extract_sentences(req.description)
    for sentence in fallback_sentences[:2]:
        hints.append(f"Setze dies praktisch so um: {sentence}")

    return hints


def _extract_sentences(text: str | None) -> List[str]:
    if not text:
        return []
    cleaned = text.replace("\n", " ")
    raw_sentences = [s.strip() for s in cleaned.split(".") if s.strip()]
    return raw_sentences


