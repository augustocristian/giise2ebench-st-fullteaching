# -*- coding: utf-8 -*-
"""pytest.mark.parametrize data providers, ported from utils/ParameterLoader.java.

Java exposes these as `@MethodSource` streams; the pytest idiom is a plain list of
tuples consumed directly by `@pytest.mark.parametrize("mail,password,role", ...)`.
"""
import logging
from typing import List, Tuple

from fullteaching_e2e.utils.user_loader import get_all_users

logger = logging.getLogger(__name__)

UserParams = List[Tuple[str, str, str]]


def _is_student(user) -> bool:
    return user.role.strip().upper() == "STUDENT"


def _is_teacher(user) -> bool:
    return user.role.strip().upper() == "TEACHER"


def get_test_users() -> UserParams:
    users = get_all_users()
    logger.debug("get_test_users -- %d users", len(users))
    return [(u.name, u.password, u.role) for u in users]


def get_test_students() -> UserParams:
    users = get_all_users()
    return [(u.name, u.password, u.role) for u in users if _is_student(u) and not _is_teacher(u)]


def get_test_teachers() -> UserParams:
    users = get_all_users()
    return [(u.name, u.password, u.role) for u in users if _is_teacher(u) and not _is_student(u)]
