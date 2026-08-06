# -*- coding: utf-8 -*-
"""CSV-backed user catalog, ported from utils/UserLoader.java."""
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from fullteaching_e2e.utils.user import User

USERNAME, PASSWORD, ROLES = 0, 1, 2

# resources/ lives at the project root, unlike Java's cwd-relative "src/test/resources/...".
_RESOURCES_INPUTS = Path(__file__).resolve().parents[2] / "resources" / "inputs"
DEFAULT_USER_FILE = _RESOURCES_INPUTS / "default_user_file.csv"

_users: Optional[Dict[str, User]] = None


def parse_user(csv_line: str) -> User:
    fields = csv_line.strip().split(",")
    return User(fields[USERNAME], fields[PASSWORD], fields[ROLES])


def load_users(users_file: Path = DEFAULT_USER_FILE, override: bool = False) -> None:
    global _users
    if override or _users is None:
        _users = {}
    with open(users_file, newline="", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            user = parse_user(line)
            _users[user.name] = user


def load_users_from_list(user_list: Iterable[User], override: bool = False) -> None:
    global _users
    if override or _users is None:
        _users = {}
    for user in user_list:
        _users[user.name] = user


def retrieve_user(name: str) -> Optional[User]:
    return (_users or {}).get(name)


def get_all_users() -> List[User]:
    if _users is None:
        load_users()
    return list(_users.values())
