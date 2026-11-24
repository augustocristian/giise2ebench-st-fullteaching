# -*- coding: utf-8 -*-
"""Ported from functional/test/teacher/CourseTeacherTest.java.

Unlike the Java source, steps are not individually wrapped in try/except + fail(label):
pytest's own traceback already pinpoints the failing line, so a manual per-step label adds
noise rather than clarity (see also base_logged_test.py's note on why ExceptionsHelper
wasn't ported).

Every course the tests create or rename is put back by a ``finally`` block, so a failing run does not leave
junk in the shared course list.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import forum_navigation_utilities as forum_nav
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils.parameter_loader import get_test_teachers
from tests.support import best_effort, open_first_course_and_visit_every_tab, timestamped

pytestmark = pytest.mark.e2e

NEW_COURSE_PREFIX = "Test Course"
EDITED_COURSE_PREFIX = "EDITION TEST"

# Quill rich-text editor of the course description (the editable box and the rendered view are in constants).
HEADER_PICKER = ".ql-picker.ql-header"  # the widget Quill builds, not the hidden <select> it replaces
PICKER_OPTIONS = ".ql-picker-options"
HEADING_OPTION = ".ql-picker-item[data-label='Heading']"
# The "preview" toggle is the only floated (left) control of the editor's button row.
PREVIEW_BUTTON = "#textEditorRowButtons .left"

DESCRIPTION_TITLE = "New Title"
DESCRIPTION_SUBHEADING = "New SubHeading"
DESCRIPTION_PARAGRAPH = "This is the normal content"
DESCRIPTION_HTML = f"<h1>{DESCRIPTION_TITLE}</h1><h2>{DESCRIPTION_SUBHEADING}</h2><p>{DESCRIPTION_PARAGRAPH}</p>"


async def _on_course_list(user: BrowserUser) -> None:
    """Goes to the dashboard and waits until its course list has rendered."""
    await navigation_utilities.to_courses_home(user)
    await user.locator(c.FIRST_COURSE).wait_for()


@asynccontextmanager
async def temporary_course(user: BrowserUser, title: str) -> AsyncIterator[str]:
    """Creates a course for the duration of the block; whatever happens, it is deleted afterwards if still there."""
    try:
        await course_nav.new_course(user, title)
        yield title
    finally:
        async def delete_if_present() -> None:
            await _on_course_list(user)
            if await course_nav.check_if_course_exists(user, title):
                await course_nav.delete_course(user, title)

        await best_effort(f"delete course {title!r}", delete_if_present)


async def _restore_course_name(user: BrowserUser, current_name: str, original_name: str) -> None:
    async def rename_back() -> None:
        await _on_course_list(user)
        if await course_nav.check_if_course_exists(user, current_name):
            await course_nav.change_course_name(user, current_name, original_name)

    await best_effort(f"rename course {current_name!r} back to {original_name!r}", rename_back)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_teacher_course_main(user: BrowserUser, mail: str, password: str, role: str) -> None:
    """Opens the first course and clicks through every tab.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READONLY,15)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)

    await open_first_course_and_visit_every_tab(user)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_teacher_create_and_delete_course(user: BrowserUser, mail: str, password: str, role: str) -> None:
    """Creates a course, confirms it exists, deletes it, confirms it's gone.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(DYNAMIC,15)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)
    course_title = timestamped(NEW_COURSE_PREFIX)

    async with temporary_course(user, course_title):
        await course_nav.assert_course_exists(user, course_title)

        await course_nav.delete_course(user, course_title)
        await course_nav.assert_course_not_exists(user, course_title)

    # Back to the landing page so the teardown logout starts from a known state.
    await user.page.goto(user.app_url)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_teacher_edit_course_values(user: BrowserUser, mail: str, password: str, role: str) -> None:
    """Renames a course and back, rewrites its rich-text description, toggles its forum,
    and checks the current user shows up (highlighted) in its attenders list.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    original_name = c.FORUM_TEST_COURSE_NAME
    edited_name = timestamped(EDITED_COURSE_PREFIX)
    user_name = await base_logged_test.slow_login(user, mail, password)
    name_restored = False

    try:
        await _on_course_list(user)
        await course_nav.assert_course_exists(user, original_name)

        await course_nav.change_course_name(user, original_name, edited_name)
        await course_nav.assert_course_exists(user, edited_name)
        await course_nav.change_course_name(user, edited_name, original_name)
        name_restored = True
        await course_nav.assert_course_exists(user, original_name)

        course = await course_nav.get_course_by_name(user, original_name)
        await course.within(c.COURSE_LIST_COURSE_TITLE).click()
        await user.locator(c.TABS_DIV).wait_for()

        await _edit_home_description(user)

        await course_nav.go2_tab(user, c.SESSION_ICON)
        # new/delete session are covered by test_rest_operations.py's sessionRestOperations

        await _toggle_forum(user)

        await course_nav.go2_tab(user, c.ATTENDERS_ICON)
        assert await course_nav.is_user_in_attenders_list(user, user_name), "User isn't in the attenders list"
        assert await course_nav.get_highlighted_attender(user) == user_name, \
            "Main user and active user doesn't match"

        # At the end of this test the header isn't reliably loaded; wait for it before finishing.
        await user.locator(c.MAIN_MENU_ARROW).wait_for()
    finally:
        if not name_restored:
            await _restore_course_name(user, edited_name, original_name)


async def _edit_home_description(user: BrowserUser) -> None:
    """Rewrites the course description through the Quill editor and checks the preview and the saved view."""
    await course_nav.go2_tab(user, c.HOME_ICON)
    await user.locator(c.EDIT_DESCRIPTION_BUTTON).click()

    editor = user.locator(c.EDIT_DESCRIPTION_CONTENT_BOX)
    await editor.wait_for()
    await editor.click()
    await editor.evaluate("(element) => { element.innerHTML = ''; }")

    await user.locator(HEADER_PICKER).click()
    await user.locator(PICKER_OPTIONS).wait_for()
    await user.locator(HEADING_OPTION).click()

    # Quill offers no UI path to type structured (h1/h2/p) content in one go, so the editor's DOM is set
    # directly; Quill's mutation observer syncs it into its model.
    await editor.evaluate("(element, html) => { element.innerHTML = html; }", DESCRIPTION_HTML)
    await user.locator(PREVIEW_BUTTON).click()
    await _expect_description_rendered(user)

    await user.locator(c.EDIT_DESCRIPTION_SAVE_BUTTON).click()
    await _expect_description_rendered(user)


async def _expect_description_rendered(user: BrowserUser) -> None:
    """The description view (preview or saved) shows the heading, subheading and paragraph as written."""
    rendered = user.locator(c.DESCRIPTION_VIEW)
    await rendered.wait_for()
    await rendered.within("h1").wait_for_text(DESCRIPTION_TITLE, exact=True)
    await rendered.within("h2").wait_for_text(DESCRIPTION_SUBHEADING, exact=True)
    await rendered.within("p").wait_for_text(DESCRIPTION_PARAGRAPH, exact=True)


async def _toggle_forum(user: BrowserUser) -> None:
    """Exercises the forum toggle from whichever state the course is in and leaves it as found."""
    await course_nav.go2_tab(user, c.FORUM_ICON)
    forum_tab = await course_nav.get_tab_content(user, c.FORUM_ICON)
    # The edit icon is always there for a teacher, so once it shows, the new-entry icon (forum on) is settled.
    await forum_tab.within(c.FORUM_EDIT_ENTRY_ICON).wait_for()
    forum_was_enabled = await forum_nav.is_forum_enabled(forum_tab)

    if not forum_was_enabled:
        await forum_nav.enable_forum(user)
    await forum_tab.within(c.FORUM_NEW_ENTRY_ICON).wait_for()
    await forum_tab.within(c.FORUM_EDIT_ENTRY_ICON).wait_for()

    await forum_nav.disable_forum(user)
    if forum_was_enabled:
        await forum_nav.enable_forum(user)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_teacher_delete_course(user: BrowserUser, mail: str, password: str, role: str) -> None:
    """Creates a dummy course and deletes it, checking the course count drops by exactly one.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)
    course_name = timestamped(NEW_COURSE_PREFIX)

    async with temporary_course(user, course_name):
        courses_before = await course_nav.get_courses_list(user)

        await course_nav.delete_course(user, course_name)

        courses_after = await course_nav.get_courses_list(user)
        assert len(courses_after) == len(courses_before) - 1, \
            f"Deleting the course must remove exactly one entry: {courses_before} -> {courses_after}"
        assert course_name not in courses_after
