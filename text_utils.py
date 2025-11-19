from __future__ import annotations

TRANSLATION_TABLE = str.maketrans(
    {
        "\u2013": "-",
        "\u2014": "-",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201a": "'",
    }
)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    candidate = value
    try:
        candidate = value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        candidate = value
    return candidate.translate(TRANSLATION_TABLE)
