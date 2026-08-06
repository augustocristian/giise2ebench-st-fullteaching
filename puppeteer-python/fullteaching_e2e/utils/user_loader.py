"""CSV-backed user catalog, ported from ``utils/UserLoader.java``."""
from functools import cache
from pathlib import Path

from fullteaching_e2e.common.config import INPUTS_DIR
from fullteaching_e2e.utils.user import User

DEFAULT_USER_FILE = INPUTS_DIR / "default_user_file.csv"


def parse_user(csv_line: str) -> User:
    """Builds a user from a ``name,password,role[,...]`` line."""
    name, password, role, *_ = csv_line.strip().split(",")
    return User(name, password, role)


@cache
def load_users(users_file: Path = DEFAULT_USER_FILE) -> dict[str, User]:
    """Reads (once per file) the users file into a ``name -> User`` dict, skipping blank lines."""
    lines = users_file.read_text(encoding="utf-8").splitlines()
    return {user.name: user for user in (parse_user(line) for line in lines if line.strip())}


def retrieve_user(name: str, users_file: Path = DEFAULT_USER_FILE) -> User | None:
    """The user with that name, if the file has one."""
    return load_users(users_file).get(name)


def get_all_users(users_file: Path = DEFAULT_USER_FILE) -> list[User]:
    """Every user of the file, in file order."""
    return list(load_users(users_file).values())
