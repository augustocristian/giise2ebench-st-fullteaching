"""Data providers for ``@pytest.mark.parametrize("mail,password,role", ...)``.

Ported from ``utils/ParameterLoader.java``: Java streams ``Arguments``, pytest takes plain tuples.
"""
from fullteaching_e2e.utils.user import User
from fullteaching_e2e.utils.user_loader import get_all_users

UserParams = list[tuple[str, str, str]]


def _params(users: list[User]) -> UserParams:
    return [(user.name, user.password, user.role) for user in users]


def get_test_users() -> UserParams:
    """``(mail, password, role)`` of every user."""
    return _params(get_all_users())


def get_test_students() -> UserParams:
    """``(mail, password, role)`` of the users that are students and not teachers."""
    return _params([user for user in get_all_users() if user.is_student and not user.is_teacher])


def get_test_teachers() -> UserParams:
    """``(mail, password, role)`` of the users that are teachers and not students."""
    return _params([user for user in get_all_users() if user.is_teacher and not user.is_student])
