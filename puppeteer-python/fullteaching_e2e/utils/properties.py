"""Minimal ``java.util.Properties``-style reader for ``resources/inputs/test.properties``."""
from pathlib import Path


def load_properties(path: Path) -> dict[str, str]:
    """Parses a flat ``key=value`` file, ignoring blank lines and ``#`` comments."""
    properties: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        properties[key.strip()] = value.strip()
    return properties
