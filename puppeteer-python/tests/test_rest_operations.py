# -*- coding: utf-8 -*-
"""REST-backed UI operations of a course, ported from functional/test/media/FullTeachingEndToEndRESTTests.java.

Covers course/session/forum/file/attenders CRUD through the UI. Every test works on its own
course (COURSE_NAME), created by the ``teacher`` fixture, which also deletes it again, whatever
the outcome of the test (it may have been renamed or left half-built by a failure).
"""
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import Literal

import pytest

from fullteaching_e2e.browser import BrowserError, Locator
from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import forum_navigation_utilities as forum_nav
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.common.config import RESOURCES_DIR
from fullteaching_e2e.common.exceptions import ElementNotFoundException
from fullteaching_e2e.utils import wait
from fullteaching_e2e.utils.parameter_loader import get_test_teachers

logger = logging.getLogger(__name__)

COURSE_NAME = "TEST_COURSE"
EDITED = " EDITED"
EDITED_COURSE_NAME = COURSE_NAME + EDITED
TEST_COURSE_INFO = "TEST_COURSE_INFO"
TEST_FILE = RESOURCES_DIR / "testFile.txt"

UNREGISTERED_ATTENDER = "studentFail@gmail.com"
REGISTERED_ATTENDER = "student1@gmail.com"

# The relative-date pipe flips from "a few seconds ago" to "a minute ago" after ~45 seconds.
JUST_CREATED = ("a few seconds ago", "a minute ago")

# Longest the upload of a file may take, in milliseconds.
UPLOAD_TIMEOUT_MS = 20_000

# Native <dialog> ids, used to wait for each kind of dialog to close.
POST_DIALOG_ID = c.FORUM_NEW_ENTRY_MODAL.removeprefix("#")
PUT_DELETE_DIALOG_ID = c.ENABLE_FORUM_MODAL.removeprefix("#")
PUT_DELETE_COURSE_DIALOG_ID = c.EDIT_DELETE_MODAL.removeprefix("#")

# Selectors that are only used here (the Java source keeps them inline as well).
# Generic dialogs: the same ids are shared by the forum, session and file dialogs.
_POST_TITLE_FIELD = c.FORUM_NEW_ENTRY_MODAL_TITLE
_POST_COMMENT_FIELD = c.FORUM_NEW_ENTRY_MODAL_CONTENT
_POST_BUTTON = c.FORUM_NEW_ENTRY_MODAL_POST_BUTTON
_PUT_BUTTON = c.ENABLE_FORUM_MODAL_SAVE_BUTTON
_DELETE_CHECKBOX = c.EDIT_COURSE_DELETE_CHECK
_WARNING_PANEL = "app-error-message .card-panel.warning"
_FAIL_PANEL = "app-error-message .card-panel.fail"
_CORRECT_PANEL = "app-error-message .card-panel.correct"
_PANEL_CLOSE_ICON = ".material-icons"
# The icon sits inside the actual "back to the entries list" button.
_BACK_TO_ENTRIES_BUTTON = f"button:has({c.BACK_TO_ENTRIES_LIST_ICON})"

# Courses
_MAIN_COURSE_TITLE = "#main-course-title"
_ACTIVE_TAB_WARNING = ".md-tab-body.md-tab-active .card-panel.warning"

# Sessions
_DELETE_SESSION_BUTTON = "#delete-session-btn"
_SESSION_DESCRIPTION = ".session-description"
_SESSION_DATETIME = ".session-datetime"

# Forum
_ENTRY_DATE = ".forum-entry-date"

# Files
_ADD_FILE_GROUP_ICON = "#add-files-icon"
_EDIT_FILE_GROUP_ICON = "#edit-filegroup-icon"
_DELETE_FILE_GROUP_ICON = "app-file-group .delete-filegroup-icon"
_ADD_SUBGROUP_BUTTON = ".add-subgroup-btn"
_ADD_FILE_BUTTON = "app-file-group app-file-group .add-file-btn"
_EDIT_FILE_NAME_ICON = "app-file-group app-file-group .edit-file-name-icon"
_FILE_TITLE_FIELD = "#input-file-title"
_FILE_GROUP_TITLE = "app-file-group .file-group-title h5"
_SUBGROUP_TITLE = "app-file-group app-file-group .file-group-title h5"
_SUBGROUP_FILE_NAME = "app-file-group app-file-group .chip .file-name-div"
_FILE_UPLOADER = ".input-file-uploader"
_UPLOAD_ALL_BUTTON = "#upload-all-btn"
_UPLOAD_PROGRESS_DONE = ".determinate[style*='width: 100']"
_UPLOAD_STATUS_ICON = "i[class*='icon-status-upload']"
_CLOSE_UPLOAD_BUTTON = "#close-upload-modal-btn"

# Attenders
_ADD_ATTENDERS_ICON = "#add-attenders-icon"
_EDIT_ATTENDERS_ICON = "#edit-attenders-icon"
_DELETE_ATTENDER_ICON = ".del-attender-icon"
_ATTENDER_FIELD = "#input-attender-simple"

# One test case per configured teacher; the id keeps credentials out of the test names.
TEACHERS = [pytest.param(mail, password, id=mail) for mail, password, _role in get_test_teachers()]
with_each_teacher = pytest.mark.parametrize("mail,password", TEACHERS)


@dataclass(frozen=True)
class SessionData:
    """The values of the new/edit session form and how the sessions list displays them."""

    title: str
    comment: str
    day: date
    at: time

    @property
    def displayed_date_time(self) -> str:
        """Date and time as rendered by the sessions list, e.g. ``Mar 1, 2018 - 15:10``."""
        return f"{self.day:%b} {self.day.day}, {self.day.year} - {self.at:%H:%M}"


# ── Fixtures ─────────────────────────────────────────────────────────────────────────────────

async def _delete_leftover_courses(user: BrowserUser) -> None:
    """Best-effort removal of the test course (under either of its names) if a test left it behind.

    A failure here is only logged, so it never hides the failure of the test itself.
    """
    try:
        await user.page.goto(user.app_url)  # drops any dialog the test left open
        listed_titles = await course_nav.get_courses_list(user)
        for course_name in (COURSE_NAME, EDITED_COURSE_NAME):
            if course_name in listed_titles:
                await course_nav.delete_course(user, course_name)
    except (BrowserError, ElementNotFoundException, TimeoutError, AssertionError) as error:
        logger.warning("Could not delete the leftover test course: %s", error)


@pytest.fixture
async def teacher(user: BrowserUser, mail: str, password: str) -> AsyncIterator[BrowserUser]:
    """A logged-in teacher (``mail``/``password`` come from ``with_each_teacher``) with a new COURSE_NAME course."""
    await base_logged_test.slow_login(user, mail, password)
    try:
        await course_nav.new_course(user, COURSE_NAME)
        yield user
    finally:
        await _delete_leftover_courses(user)


# ── Helpers ──────────────────────────────────────────────────────────────────────────────────

async def _wait_for_count(locator: Locator, expected: int) -> None:
    """Waits until ``locator`` matches exactly ``expected`` elements."""
    async def _matches() -> bool:
        return await locator.count() == expected

    await wait.poll_until(_matches, f"{locator} to match {expected} elements")


async def _enter_course_and_open_tab(user: BrowserUser, tab_icon: str) -> None:
    """Opens COURSE_NAME from the dashboard and switches to the tab with the given icon."""
    course = await course_nav.get_course_by_name(user, COURSE_NAME)
    await course.within(c.COURSE_LIST_COURSE_TITLE).click()
    await user.locator(_MAIN_COURSE_TITLE).wait_for_text(COURSE_NAME, exact=True)
    await course_nav.go2_tab(user, tab_icon)


async def _post(user: BrowserUser, opener: str, error_message: str,
                title: str | None = None, comment: str | None = None) -> None:
    """Opens a "new element" dialog, fills in whichever of title/comment are given and sends it."""
    await base_logged_test.open_dialog(user, opener)
    if title is not None:
        await user.locator(_POST_TITLE_FIELD).fill(title)
    if comment is not None:
        await user.locator(_POST_COMMENT_FIELD).fill(comment)
    await user.locator(_POST_BUTTON).click()
    await base_logged_test.wait_for_dialog_closed(user, POST_DIALOG_ID, error_message)


async def _put(user: BrowserUser, opener: str, field: str, value: str, error_message: str) -> None:
    """Opens an "edit" dialog, sets one text field and sends it."""
    await base_logged_test.open_dialog(user, opener)
    await user.locator(field).fill(value)
    await user.locator(_PUT_BUTTON).click()
    await base_logged_test.wait_for_dialog_closed(user, PUT_DELETE_DIALOG_ID, error_message)


async def _upload_file(user: BrowserUser, file_input: str, path: Path) -> None:
    """Selects a file in a (possibly hidden) ``<input type=file>``."""
    await user.locator(file_input).upload_file(path)


async def _fill_session_form(user: BrowserUser, mode: Literal["post", "put"], session: SessionData) -> None:
    """Fills and sends the new (post) or edit (put) session form.

    ``<input type=date>`` takes ``yyyy-MM-dd`` and ``<input type=time>`` ``HH:mm`` whatever the
    locale of the browser is.
    """
    await user.locator(f"#input-{mode}-title").fill(session.title)
    await user.locator(f"#input-{mode}-comment").fill(session.comment)
    await user.locator(f"#input-{mode}-date").fill(session.day.isoformat())
    await user.locator(f"#input-{mode}-time").fill(session.at.isoformat(timespec="minutes"))
    await user.locator(f"#{mode}-modal-btn").click()


async def _expect_session(user: BrowserUser, session: SessionData) -> None:
    """Checks that the sessions list shows the session."""
    row = c.SESSION_LIST_SESSION_ROW
    await user.locator(f"{row} {c.SESSION_LIST_SESSION_NAME}").wait_for_text(session.title, exact=True)
    await user.locator(f"{row} {_SESSION_DESCRIPTION}").wait_for_text(session.comment, exact=True)
    await user.locator(f"{row} {_SESSION_DATETIME}").wait_for_text(session.displayed_date_time, exact=True)


# ── Tests ────────────────────────────────────────────────────────────────────────────────────

@with_each_teacher
async def test_course_rest_operations(teacher: BrowserUser) -> None:
    """A teacher can create (fixture), rename and delete a course.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    # Act + assert: rename the course through its edit dialog
    course = await course_nav.get_course_by_name(teacher, COURSE_NAME)
    await base_logged_test.open_dialog(teacher, course.within(c.EDIT_COURSE_BUTTON))
    await teacher.locator(c.EDIT_COURSE_MODAL_NAME_FIELD).fill(EDITED_COURSE_NAME)
    await teacher.locator(c.EDIT_COURSE_MODAL_SAVE).click()
    await base_logged_test.wait_for_dialog_closed(teacher, PUT_DELETE_COURSE_DIALOG_ID, "Edition of course failed")
    await course_nav.assert_course_exists(teacher, EDITED_COURSE_NAME)

    # Act + assert: delete it
    await course_nav.delete_course(teacher, EDITED_COURSE_NAME)
    await course_nav.assert_course_not_exists(teacher, EDITED_COURSE_NAME)


@with_each_teacher
async def test_course_info_rest_operations(teacher: BrowserUser) -> None:
    """A teacher can edit the course description in the Home tab and see it rendered.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) information(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await _enter_course_and_open_tab(teacher, c.HOME_ICON)
    await teacher.locator(_ACTIVE_TAB_WARNING).first().wait_for("visible")  # a new course has no info yet

    await teacher.locator(c.EDIT_DESCRIPTION_BUTTON).click()
    await teacher.locator(c.EDIT_DESCRIPTION_CONTENT_BOX).type(TEST_COURSE_INFO)
    await teacher.locator(c.EDIT_DESCRIPTION_SAVE_BUTTON).click()

    await teacher.locator(c.DESCRIPTION_VIEW_TEXT).wait_for_text(TEST_COURSE_INFO, exact=True)


@with_each_teacher
async def test_session_rest_operations(teacher: BrowserUser) -> None:
    """A teacher can create, edit and delete a session of a course.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) session(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    created = SessionData("TEST LESSON NAME", "TEST LESSON COMMENT", date(2018, 3, 1), time(15, 10))
    edited = SessionData(created.title + EDITED, created.comment + EDITED, date(2019, 4, 2), time(5, 10))
    await _enter_course_and_open_tab(teacher, c.SESSION_ICON)

    # Create
    await base_logged_test.open_dialog(teacher, c.SESSION_LIST_NEW_SESSION_ICON)
    await _fill_session_form(teacher, "post", created)
    await base_logged_test.wait_for_dialog_closed(teacher, POST_DIALOG_ID, "Addition of session failed")
    await _expect_session(teacher, created)

    # Edit
    await base_logged_test.open_dialog(teacher, c.SESSION_LIST_SESSION_EDIT_ICON)
    await _fill_session_form(teacher, "put", edited)
    await base_logged_test.wait_for_dialog_closed(teacher, PUT_DELETE_DIALOG_ID, "Edition of session failed")
    await _expect_session(teacher, edited)

    # Delete
    await base_logged_test.open_dialog(teacher, c.SESSION_LIST_SESSION_EDIT_ICON)
    await teacher.locator(_DELETE_CHECKBOX).click()
    await teacher.locator(_DELETE_SESSION_BUTTON).click()
    await base_logged_test.wait_for_dialog_closed(teacher, PUT_DELETE_DIALOG_ID, "Deletion of session failed")
    await _wait_for_count(teacher.locator(c.SESSION_LIST_SESSION_ROW), 0)


@with_each_teacher
async def test_forum_rest_operations(teacher: BrowserUser) -> None:
    """A teacher can add a forum entry and a reply to its comment, then deactivate the forum.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    title, comment, reply = "TEST FORUM ENTRY", "TEST FORUM COMMENT", "TEST FORUM REPLY"
    await _enter_course_and_open_tab(teacher, c.FORUM_ICON)

    # Add an entry
    await _post(teacher, c.FORUM_NEW_ENTRY_ICON, "Addition of entry failed", title=title, comment=comment)
    entry = teacher.locator(c.FORUM_ENTRY_ROW).first()
    await entry.within(c.FORUM_ENTRY_LIST_ENTRY_TITLE).wait_for_text(title, exact=True)
    await entry.within(c.FORUM_ENTRY_LIST_ENTRY_USER).wait_for_text(c.TEACHER_NAME, exact=True)
    entry_date = (await entry.within(_ENTRY_DATE).first().text()).strip()  # rendered together with the row
    assert entry_date in JUST_CREATED, f"Unexpected entry date '{entry_date}'"

    # The entry's original comment
    await entry.click()
    first_comment = (await forum_nav.get_comments(teacher))[0]
    await first_comment.within(c.FORUM_COMMENT_LIST_COMMENT_CONTENT).first().wait_for_text(comment, exact=True)
    await first_comment.within(c.FORUM_COMMENT_LIST_COMMENT_USER).first().wait_for_text(c.TEACHER_NAME, exact=True)

    # Reply to it (the reply icon selector is that of the text reply, not the video one)
    await _post(teacher, c.FORUM_COMMENT_LIST_COMMENT_REPLY_ICON, "Addition of entry reply failed", comment=reply)

    async def _first_reply() -> Locator | None:
        replies = await forum_nav.get_replies(first_comment)
        return replies[0] if replies else None

    first_reply = await wait.poll_until(_first_reply, "the reply to be listed")
    await first_reply.within(c.FORUM_COMMENT_LIST_COMMENT_CONTENT).first().wait_for_text(reply, exact=True)
    await first_reply.within(c.FORUM_COMMENT_LIST_COMMENT_USER).first().wait_for_text(c.TEACHER_NAME, exact=True)

    # Deactivate the forum
    await teacher.locator(_BACK_TO_ENTRIES_BUTTON).click()
    await base_logged_test.open_dialog(teacher, c.FORUM_EDIT_ENTRY_ICON)
    await teacher.locator(c.DISABLE_FORUM_BUTTON).click()
    await teacher.locator(_PUT_BUTTON).click()
    await base_logged_test.wait_for_dialog_closed(teacher, PUT_DELETE_DIALOG_ID, "Deactivation of forum failed")
    await teacher.locator(_WARNING_PANEL).first().wait_for("visible")


@with_each_teacher
async def test_files_rest_operations(teacher: BrowserUser) -> None:
    """A teacher can create, rename and delete file groups, sub-groups and uploaded files.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) files(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    file_group, file_subgroup = "TEST FILE GROUP", "TEST FILE SUBGROUP"
    edited_file_name = "testFileEDITED.txt"
    await _enter_course_and_open_tab(teacher, c.FILES_ICON)
    await teacher.locator(_WARNING_PANEL).first().wait_for("visible")  # a new course has no files yet

    # File group
    await _post(teacher, _ADD_FILE_GROUP_ICON, "Addition of file group failed", title=file_group)
    await teacher.locator(_FILE_GROUP_TITLE).wait_for_text(file_group, exact=True)
    await _put(teacher, _EDIT_FILE_GROUP_ICON, _FILE_TITLE_FIELD, file_group + EDITED, "Edition of file group failed")
    await teacher.locator(_FILE_GROUP_TITLE).wait_for_text(file_group + EDITED, exact=True)

    # File sub-group
    await _post(teacher, _ADD_SUBGROUP_BUTTON, "Addition of file sub-group failed", title=file_subgroup)
    await teacher.locator(_SUBGROUP_TITLE).wait_for_text(file_subgroup, exact=True)

    # File
    await base_logged_test.open_dialog(teacher, _ADD_FILE_BUTTON)
    await _upload_file(teacher, _FILE_UPLOADER, TEST_FILE)
    await teacher.locator(_UPLOAD_ALL_BUTTON).click()
    await teacher.locator(_UPLOAD_PROGRESS_DONE, UPLOAD_TIMEOUT_MS).wait_for("visible")
    await teacher.locator(_UPLOAD_STATUS_ICON).wait_for_text("done", exact=True)
    await teacher.locator(_CLOSE_UPLOAD_BUTTON).click()
    await base_logged_test.wait_for_dialog_closed(teacher, POST_DIALOG_ID, "Upload of file failed")
    await teacher.locator(_SUBGROUP_FILE_NAME).wait_for_text(TEST_FILE.name, exact=True)

    await _put(teacher, _EDIT_FILE_NAME_ICON, _FILE_TITLE_FIELD, edited_file_name, "Edition of file failed")
    await teacher.locator(_SUBGROUP_FILE_NAME).wait_for_text(edited_file_name, exact=True)

    # Delete the group (and with it its sub-group and file)
    await teacher.locator(_DELETE_FILE_GROUP_ICON).first().click()
    await teacher.locator(_WARNING_PANEL).first().wait_for("visible")


@with_each_teacher
async def test_attenders_rest_operations(teacher: BrowserUser) -> None:
    """A teacher cannot add an unregistered attender, can add a registered one and can remove them.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) attenders(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    rows = teacher.locator(c.ATTENDERS_LIST_ROWS)
    await _enter_course_and_open_tab(teacher, c.ATTENDERS_ICON)

    # A new course only has its teacher as attender
    await _wait_for_count(rows, 1)
    await rows.within(c.ATTENDERS_LIST_HIGHLIGHTED_ROW).wait_for_text(c.TEACHER_NAME, exact=True)

    # Add an unregistered attender: rejected
    await _put(teacher, _ADD_ATTENDERS_ICON, _ATTENDER_FIELD, UNREGISTERED_ATTENDER, "Addition of attender fail")
    await teacher.locator(_FAIL_PANEL).first().wait_for("visible")
    await _wait_for_count(rows, 1)
    await teacher.locator(f"{_FAIL_PANEL} {_PANEL_CLOSE_ICON}").first().click()

    # Add a registered attender: accepted
    await _put(teacher, _ADD_ATTENDERS_ICON, _ATTENDER_FIELD, REGISTERED_ATTENDER, "Addition of attender failed")
    await teacher.locator(_CORRECT_PANEL).first().wait_for("visible")
    await _wait_for_count(rows, 2)
    await teacher.locator(f"{_CORRECT_PANEL} {_PANEL_CLOSE_ICON}").first().click()

    # Remove the attender
    await teacher.locator(_EDIT_ATTENDERS_ICON).click()
    await teacher.locator(_DELETE_ATTENDER_ICON).first().click()
    await _wait_for_count(rows, 1)
