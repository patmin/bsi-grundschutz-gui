from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DOCBOOK_NS = {"d": "http://docbook.org/ns/docbook"}

MODULE_RE = re.compile(r"^(?P<prefix>[A-Z]{3,4})\.(?P<body>\d+(?:\.\d+)*)\s+(?P<title>.+)$")
REQ_RE = re.compile(
    r"^(?P<code>[A-Z]{3,4}\.[0-9.]+\.A[0-9A-Za-z]+)"
    r"\s+(?P<title>.+?)\s*\((?P<level>[BSEH])\)"
    r"(?:\s*\[(?P<roles>[^\]]+)\])?$"
)


@dataclass
class Requirement:
    code: str
    title: str
    level: str
    roles: List[str]
    description: str
    module_code: str
    module_title: str
    chapter: str


@dataclass
class Module:
    code: str
    title: str
    chapter: str
    requirements: List[Requirement] = field(default_factory=list)


@dataclass
class Compendium:
    modules: Dict[str, Module]
    requirements: Dict[str, Requirement]

    def get_module(self, code: str) -> Optional[Module]:
        return self.modules.get(code)

    def get_requirement(self, code: str) -> Optional[Requirement]:
        return self.requirements.get(code)


def load_compendium(xml_path: Path) -> Compendium:
    xml_path = xml_path.expanduser().resolve()
    if not xml_path.exists():
        raise FileNotFoundError(f"XML-Datei nicht gefunden: {xml_path}")

    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    modules: Dict[str, Module] = {}
    requirements: Dict[str, Requirement] = {}

    for chapter in root.findall("d:chapter", DOCBOOK_NS):
        chapter_title = _text_or_default(chapter.find("d:title", DOCBOOK_NS), "Unbenanntes Kapitel")
        for section in chapter.findall("d:section", DOCBOOK_NS):
            _walk_section(section, chapter_title, modules, requirements, current_module=None)

    # sort requirements inside modules for stable CLI output
    for module in modules.values():
        module.requirements.sort(key=lambda req: req.code)

    return Compendium(modules=dict(sorted(modules.items())), requirements=requirements)


def _walk_section(
    section: ET.Element,
    chapter_title: str,
    modules: Dict[str, Module],
    requirements: Dict[str, Requirement],
    current_module: Optional[Module],
) -> None:
    title_text = _text_or_default(section.find("d:title", DOCBOOK_NS), "").strip()
    module_match = MODULE_RE.match(title_text)

    if module_match:
        module_code = f"{module_match.group('prefix')}.{module_match.group('body')}"
        module_title = module_match.group("title").strip()
        module = modules.get(module_code)
        if module is None:
            module = Module(code=module_code, title=module_title, chapter=chapter_title)
            modules[module_code] = module
        current_module = module

    req_match = REQ_RE.match(title_text)
    if req_match and current_module is not None:
        req_code = req_match.group("code")
        req_title = req_match.group("title").strip()
        req_level = req_match.group("level")
        raw_roles = (req_match.group("roles") or "").strip()
        roles = _split_roles(raw_roles)
        description = _collect_text(section)

        requirement = Requirement(
            code=req_code,
            title=req_title,
            level=req_level,
            roles=roles,
            description=description,
            module_code=current_module.code,
            module_title=current_module.title,
            chapter=current_module.chapter,
        )
        requirements[req_code] = requirement
        current_module.requirements.append(requirement)

    for child in section.findall("d:section", DOCBOOK_NS):
        _walk_section(child, chapter_title, modules, requirements, current_module)


def _text_or_default(element: Optional[ET.Element], default: str) -> str:
    if element is None:
        return default
    return "".join(element.itertext())


def _collect_text(section: ET.Element) -> str:
    relevant_tags = {
        f"{{{DOCBOOK_NS['d']}}}para",
        f"{{{DOCBOOK_NS['d']}}}itemizedlist",
        f"{{{DOCBOOK_NS['d']}}}orderedlist",
        f"{{{DOCBOOK_NS['d']}}}note",
        f"{{{DOCBOOK_NS['d']}}}simpara",
        f"{{{DOCBOOK_NS['d']}}}warning",
        f"{{{DOCBOOK_NS['d']}}}important",
    }
    chunks: List[str] = []
    for child in section:
        if child.tag not in relevant_tags:
            continue
        text = " ".join(t.strip() for t in child.itertext() if t.strip())
        if text:
            text = text.replace("<?linebreak?>", " ").strip()
            chunks.append(text)
    return "\n\n".join(chunks)


def _split_roles(raw_roles: str) -> List[str]:
    if not raw_roles:
        return []
    separators = ["/", ",", " und ", " oder "]
    roles = [raw_roles]
    for sep in separators:
        roles = [part for role in roles for part in role.split(sep)]
    return [role.strip() for role in roles if role.strip()]


