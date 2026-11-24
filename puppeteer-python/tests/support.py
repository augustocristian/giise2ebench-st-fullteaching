# -*- coding: utf-8 -*-
"""Small helpers shared by the browser test modules (import as ``from tests.support import ...``).

Waiting is not here on purpose: use ``Locator.wait_for`` / ``Locator.wait_for_text`` for selector conditions
and ``fullteaching_e2e.utils.wait.poll_until`` for computed ones.

API:
    timestamped(prefix) -> str                       unique name ``<prefix>_<epoch millis>``
    best_effort(description, cleanup) -> None        run a cleanup step, log (never raise) its failure
    open_first_course_and_visit_every_tab(user)      dashboard -> first course -> every tab
    open_first_session(user)                         dashboard -> first course -> sessions -> first ready session
    STUDENT_IDENTIFIER / STUDENT_MAIL / STUDENT_PASSWORD   the student that joins the teacher's live sessions
    REALTIME_WAIT_MS / MEDIA_WAIT_MS                 timeouts for what another user does / for the media server
    ALL_TAB_ICONS                                    icons of the five course tabs
    UserCreator                                      type of the ``browser_factory`` fixture
"""
import logging
import time
from collections.abc import Awaitable, Callable

from fullteaching_e2e.browser import ElementTimeoutError
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.common.browser_user import BrowserUser

log = logging.getLogger(__name__)

# The ``browser_factory`` fixture: ``await browser_factory("IDENTIFIER", seconds_of_wait)`` -> a new BrowserUser
UserCreator = Callable[..., Awaitable[BrowserUser]]

# The student that joins the teacher's live sessions
STUDENT_IDENTIFIER = "STUDENT"
STUDENT_MAIL = "student1@gmail.com"
STUDENT_PASSWORD = "pass"

REALTIME_WAIT_MS = 30_000  # something another user has to do (chat message, grant) shows up
MEDIA_WAIT_MS = c.MEDIA_WAIT_SECONDS * 1000  # the media server connects and starts relaying streams

ALL_TAB_ICONS = (c.HOME_ICON, c.SESSION_ICON, c.FORUM_ICON, c.FILES_ICON, c.ATTENDERS_ICON)

# Dashboard of a live-session user: first course, and the first session that can be entered
_FIRST_COURSE_TITLE = "ul.collection li.collection-item:first-child div.course-title"
_FIRST_READY_SESSION = "ul div:first-child li.session-data div.session-ready"


def timestamped(prefix: str) -> str:
    """A name that no earlier run can have used: ``<prefix>_<epoch millis>``."""
    return f"{prefix}_{time.time_ns() // 1_000_000}"


async def best_effort(description: str, cleanup: Callable[[], Awaitable[None]]) -> None:
    """Runs a cleanup step without letting its own failure mask the real outcome of the test."""
    try:
        await cleanup()
    except Exception as error:  # noqa: BLE001 - cleanup must never replace the test's own failure
        log.warning("Cleanup failed (%s): %s", description, error)


async def open_first_course_and_visit_every_tab(user: BrowserUser) -> None:
    """From anywhere: goes to the dashboard, opens the first course and clicks through each of its tabs."""
    await navigation_utilities.to_courses_home(user)
    first_course = user.locator(c.FIRST_COURSE)
    try:
        await first_course.wait_for()
    except ElementTimeoutError as error:
        raise AssertionError("No courses available for the test user") from error
    await first_course.within(c.COURSE_TITLE).click()
    await user.locator(c.TABS_DIV).wait_for()

    for icon in ALL_TAB_ICONS:
        await course_nav.go2_tab(user, icon)


async def open_first_session(user: BrowserUser) -> None:
    """From the dashboard: opens the first course, its sessions tab and enters its first ready session."""
    await user.locator(_FIRST_COURSE_TITLE, REALTIME_WAIT_MS).click()
    await course_nav.go2_tab(user, c.SESSION_ICON)
    await user.locator(_FIRST_READY_SESSION, REALTIME_WAIT_MS).click()
