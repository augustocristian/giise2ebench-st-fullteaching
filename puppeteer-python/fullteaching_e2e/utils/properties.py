# -*- coding: utf-8 -*-
"""Minimal java.util.Properties-style reader for resources/inputs/test.properties."""
from pathlib import Path
from typing import Dict


def load_properties(path: Path) -> Dict[str, str]:
    props: Dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            props[key.strip()] = value.strip()
    return props
