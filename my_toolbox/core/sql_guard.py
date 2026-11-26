"""Read-only SQL check shared by the SQL and warehouse helpers (stdlib only)."""

import re

_WRITE_WORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|merge|attach|copy|call|exec)\b",
    re.IGNORECASE,
)


def is_read_only(sql: str) -> bool:
    """True for a single SELECT/WITH/EXPLAIN-style statement with no write keywords."""
    stripped = re.sub(r"--.*?$|/\*.*?\*/", " ", sql, flags=re.S | re.M).strip().rstrip(";").strip()
    if not stripped or ";" in stripped:
        return False
    if stripped.split(None, 1)[0].lower() not in ("select", "with", "explain", "show", "describe"):
        return False
    return not _WRITE_WORDS.search(stripped)
