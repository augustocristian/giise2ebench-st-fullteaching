# -*- coding: utf-8 -*-
"""Ported from functional/test/media/FullTeachingLoggedVideoSessionTests.java.

`studentNameList`/`studentNamesList`/`studentPassList` from the Java class are not ported:
they're populated in initializeStudents() but never read anywhere afterwards (write-only
dead fields) - only the actual BrowserUser list matters, which browser_factory already
tracks for us.

The teacher and every student are real, simultaneous users, each one in its own browser context. The session
the test creates is deleted by a ``finally`` block, from a fresh context, even when the run fails half way
(the failing users' pages may be stuck inside the session view).
"""
from dataclasses import dataclass
from datetime import datetime

import pytest

from fullteaching_e2e.browser import Locator
from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.common import session_navigation_utilities as session_nav
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.common.config import INPUTS_DIR
from fullteaching_e2e.utils import wait
from fullteaching_e2e.utils.parameter_loader import get_test_teachers
from tests.support import MEDIA_WAIT_MS, REALTIME_WAIT_MS, UserCreator, best_effort, timestamped

pytestmark = pytest.mark.e2e

STUDENTS_FILE = INPUTS_DIR / "default_user_LoggedVideoStudents.csv"
SESSION_NAME_PREFIX = "Today's Session"
SESSION_DESCRIPTION = "Wow today session will be amazing"
CLEANUP_USER_IDENTIFIER = "CLEANUP"
STUDENT_ENTRY_SEPARATOR = ";"
STUDENT_FIELD_SEPARATOR = ":"

# <input type=date> and <input type=time> only take ISO 8601 values, whatever the display locale is.
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

REALTIME_WAIT_S = REALTIME_WAIT_MS / 1000
# The delete button of the session edit modal: a <button> in the current SUT, an <a> in older builds.
SESSION_DELETE_BUTTON = "button, a"


@dataclass(frozen=True)
class Credentials:
    user_id: str
    password: str


# Students

def _parse_students(raw: str) -> list[Credentials]:
    """Parses the "user:password:browser;user:password:browser" students file (the browser is not needed)."""
    students = []
    for entry in filter(None, (entry.strip() for entry in raw.strip().split(STUDENT_ENTRY_SEPARATOR))):
        fields = entry.split(STUDENT_FIELD_SEPARATOR)
        if len(fields) < 2:
            raise ValueError(f"Malformed student entry {entry!r} in {STUDENTS_FILE}: expected user:password")
        students.append(Credentials(user_id=fields[0], password=fields[1]))
    return students


async def _login_students(browser_factory: UserCreator) -> list[BrowserUser]:
    students = []
    for credentials in _parse_students(STUDENTS_FILE.read_text(encoding="utf-8")):
        student = await browser_factory(credentials.user_id, seconds_of_wait=c.MEDIA_WAIT_SECONDS)
        await base_logged_test.slow_login(student, credentials.user_id, credentials.password)
        students.append(student)
    return students


# Session helpers (all of them work on the sessions tab of an open course)

async def _wait_for_session(user: BrowserUser, session_name: str) -> Locator:
    """Waits until the sessions tab lists a session with exactly this name and returns its row."""
    return await wait.poll_until(lambda: session_nav.get_session(user, session_name),
                                 f"session {session_name!r} to be listed", REALTIME_WAIT_S)


async def _wait_for_session_gone(user: BrowserUser, session_name: str) -> None:
    async def gone() -> bool:
        return session_name not in await session_nav.get_full_session_list(user)

    await wait.poll_until(gone, f"session {session_name!r} to disappear from the list", REALTIME_WAIT_S)


async def _open_sessions_tab(user: BrowserUser, course_name: str) -> None:
    """Goes to the dashboard, opens the course and its sessions tab."""
    await navigation_utilities.to_courses_home(user)
    course = await wait.poll_until(lambda: course_nav.get_course_by_name(user, course_name),
                                   f"course {course_name!r} to be listed", REALTIME_WAIT_S)
    await course.within(c.COURSE_LIST_COURSE_TITLE).click()
    await user.locator(c.TABS_DIV).wait_for()
    await course_nav.go2_tab(user, c.SESSION_ICON)


async def _create_session(user: BrowserUser, course_name: str, session_name: str) -> None:
    await _open_sessions_tab(user, course_name)
    await user.locator(c.SESSION_LIST_NEW_SESSION_ICON).click()

    modal = user.locator(c.SESSION_LIST_NEW_SESSION_MODAL)
    await modal.wait_for()
    await modal.within(c.SESSION_LIST_NEW_SESSION_MODAL_TITLE).fill(session_name)
    await modal.within(c.SESSION_LIST_NEW_SESSION_MODAL_CONTENT).fill(SESSION_DESCRIPTION)

    now = datetime.now()
    expected_date = now.strftime(DATE_FORMAT)
    date_field = modal.within(c.SESSION_LIST_NEW_SESSION_MODAL_DATE)
    await date_field.fill(expected_date)
    assert await date_field.input_value() == expected_date, "Failed to set the session date"
    await modal.within(c.SESSION_LIST_NEW_SESSION_MODAL_TIME).fill(now.strftime(TIME_FORMAT))
    await modal.within(c.SESSION_LIST_NEW_SESSION_MODAL_POST_BUTTON).click()

    await _wait_for_session(user, session_name)


async def _join_session(user: BrowserUser, session_name: str) -> None:
    session = await _wait_for_session(user, session_name)
    await session.within(c.SESSION_LIST_SESSION_ACCESS).with_timeout(REALTIME_WAIT_MS).click()
    await user.locator(c.SESSION_LEFT_MENU_BUTTON, MEDIA_WAIT_MS).wait_for()


async def _leave_session(user: BrowserUser) -> None:
    await user.locator(c.SESSION_LEFT_MENU_BUTTON).click()
    # The exit icon sits in a sliding side menu; clicking it through the DOM does not depend on that animation.
    await user.locator(c.SESSION_EXIT_ICON).js_click()
    await user.locator(c.COURSE_TABS, REALTIME_WAIT_MS).wait_for()


async def _delete_session(user: BrowserUser, session_name: str) -> None:
    await course_nav.go2_tab(user, c.SESSION_ICON)
    session = await _wait_for_session(user, session_name)
    await session.within(c.SESSION_LIST_SESSION_EDIT_ICON).click()

    modal = user.locator(c.SESSION_LIST_EDIT_MODAL)
    await modal.wait_for()
    delete_div = modal.within(c.SESSION_LIST_EDIT_MODAL_DELETE_DIV)
    await delete_div.within("label").click()
    await delete_div.within(SESSION_DELETE_BUTTON).click()

    await _wait_for_session_gone(user, session_name)


async def _delete_leftover_session(browser_factory: UserCreator, mail: str, password: str, session_name: str) -> None:
    """Removes a session a failed run may have left behind, from a fresh browser context."""
    async def delete_if_present() -> None:
        cleaner = await browser_factory(CLEANUP_USER_IDENTIFIER)
        await base_logged_test.slow_login(cleaner, mail, password)
        await _open_sessions_tab(cleaner, c.FORUM_TEST_COURSE_NAME)
        if session_name in await session_nav.get_full_session_list(cleaner):
            await _delete_session(cleaner, session_name)

    await best_effort(f"delete session {session_name!r}", delete_if_present)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_session(user: BrowserUser, browser_factory: UserCreator, mail: str, password: str,
                       role: str) -> None:
    """Creates a video session, has the teacher and every student join it, then everyone
    leaves and the session is deleted.

    Resources: loginservice(READONLY,10) openvidu(READWRITE,10) session(READONLY,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    teacher = user
    session_name = timestamped(SESSION_NAME_PREFIX)
    await base_logged_test.slow_login(teacher, mail, password)
    students = await _login_students(browser_factory)
    session_deleted = False

    try:
        await _create_session(teacher, c.FORUM_TEST_COURSE_NAME, session_name)
        await _join_session(teacher, session_name)
        for student in students:
            await _open_sessions_tab(student, c.FORUM_TEST_COURSE_NAME)
            await _join_session(student, session_name)

        for student in students:
            await _leave_session(student)
        await _leave_session(teacher)

        await _delete_session(teacher, session_name)
        session_deleted = True
    finally:
        if not session_deleted:
            await _delete_leftover_session(browser_factory, mail, password, session_name)
