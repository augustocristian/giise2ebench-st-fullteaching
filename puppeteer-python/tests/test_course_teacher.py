# -*- coding: utf-8 -*-
"""Ported from functional/test/teacher/CourseTeacherTest.java.

Unlike the Java source, steps are not individually wrapped in try/except + fail(label):
pytest's own traceback already pinpoints the failing line, so a manual per-step label adds
noise rather than clarity (see also base_logged_test.py's note on why ExceptionsHelper
wasn't ported).
"""
import time
from pathlib import Path

import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import forum_navigation_utilities as forum_nav
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.common.navigation_utilities import FindOption
from fullteaching_e2e.utils import click, element, keyboard, wait
from fullteaching_e2e.utils.parameter_loader import get_test_teachers
from fullteaching_e2e.utils.properties import load_properties

_PROPERTIES = load_properties(Path(__file__).resolve().parents[1] / "resources" / "inputs" / "test.properties")


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_teacher_course_main(user, mail, password, role):
    """Opens the first course and clicks through every tab.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READONLY,15)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)
    page = user.page

    await navigation_utilities.to_courses_home(page, user.app_url)
    await wait.not_too_much(page, c.FIRST_COURSE, visible=False)
    await click.element(page, c.FIRST_COURSE)
    await wait.not_too_much(page, c.TABS_DIV)

    for icon in (c.HOME_ICON, c.SESSION_ICON, c.FORUM_ICON, c.FILES_ICON, c.ATTENDERS_ICON):
        await course_nav.go2_tab(page, icon)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_teacher_create_and_delete_course(user, mail, password, role):
    """Creates a course, confirms it exists, deletes it, confirms it's gone.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(DYNAMIC,15)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)
    page = user.page

    course_title = f"Test Course_{int(time.time() * 1000)}"
    await course_nav.new_course(page, user.app_url, course_title)
    assert await course_nav.check_if_course_exists(page, course_title)

    await course_nav.delete_course(page, user.app_url, course_title)
    assert not await course_nav.check_if_course_exists(page, course_title)

    await page.goto(user.app_url)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_teacher_edit_course_values(user, mail, password, role):
    """Renames a course and back, rewrites its rich-text description, toggles its forum,
    and checks the current user shows up (highlighted) in its attenders list.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    course_name = _PROPERTIES["forum.test.course"]
    user_name = await base_logged_test.slow_login(user, mail, password)
    page = user.page

    await navigation_utilities.to_courses_home(page, user.app_url)

    course = await course_nav.get_course_by_name(page, course_name)
    title_el = await element.find_one(course, c.COURSE_TITLE)
    old_name = await element.get_text(page, title_el)

    edition_name = f"EDITION TEST_{int(time.time() * 1000)}"
    await course_nav.change_course_name(page, old_name, edition_name)
    assert await course_nav.check_if_course_exists_with_retries(page, edition_name, 3), (
        "The course title hasn't been found in the list ¿Have been created?")
    await course_nav.change_course_name(page, edition_name, old_name)
    assert await course_nav.check_if_course_exists_with_retries(page, old_name, 3), (
        "The course title hasn't been reset")

    course = await course_nav.get_course_by_name(page, course_name)
    title_el = await element.find_one(course, c.COURSE_LIST_COURSE_TITLE)
    await click.element(page, title_el)
    await wait.not_too_much(page, c.TABS_DIV)

    await _edit_home_description(page, user)

    await course_nav.go2_tab(page, c.SESSION_ICON)
    # new/delete session are covered by test_rest_operations.py's sessionRestOperations

    await _toggle_forum(page)

    await wait.not_too_much(page, c.ATTENDERS_ICON)
    await course_nav.go2_tab(page, c.ATTENDERS_ICON)
    await course_nav.get_tab_content(page, c.ATTENDERS_ICON)
    assert await course_nav.is_user_in_attenders_list(page, user_name), "User isn't in the attenders list"
    main_user = await course_nav.get_highlighted_attender(page)
    assert user_name == main_user, "Main user and active user doesn't match"

    # At the end of this test the header isn't reliably loaded; wait for it before finishing.
    await wait.not_too_much(page, c.MAIN_MENU_ARROW)


async def _edit_home_description(page, user):
    await course_nav.go2_tab(page, c.HOME_ICON)
    edit_description_button = await element.find_one(page, c.EDIT_DESCRIPTION_BUTTON)
    await click.element(page, edit_description_button)
    await wait.not_too_much(page, c.EDIT_DESCRIPTION_CONTENT_BOX)

    editor = await element.find_one(page, ".ql-editor")
    await editor.click()
    await keyboard.select_all(page)
    await keyboard.delete(page)

    header_selector = await element.find_one(page, ".ql-header")
    await click.element(page, header_selector)
    picker_options = await wait.not_too_much(page, ".ql-picker-options")
    options = await element.find_all(picker_options, ".ql-picker-item")
    option = await navigation_utilities.get_option(page, options, "Heading", FindOption.ATTRIBUTE, "data-label")
    assert option is not None, "Something went wrong while setting the Heading"
    await click.element(page, option)

    editor = await element.find_one(page, ".ql-editor")
    await page.evaluate(
        "(el) => { el.innerHTML = "
        "'<h1>New Title</h1><h2>New SubHeading</h2><p>This is the normal content</p>'; }",
        editor)
    save_row_button = await element.find_one(page, 'xpath=//*[@id="textEditorRowButtons"]/a[2]')
    await click.element(page, save_row_button)
    await user.wait_until(lambda: wait.not_too_much(page, ".ql-editor-custom"),
                           "Element that was waiting doesn't found")
    preview = await wait.not_too_much(page, ".ql-editor-custom")
    await _assert_description_rendered(page, preview, "preview")

    save_button = await element.find_one(page, c.EDIT_DESCRIPTION_SAVE_BUTTON)
    await click.element(page, save_button)
    saved = await wait.not_too_much(page, ".ql-editor-custom")
    await _assert_description_rendered(page, saved, "saved")


async def _assert_description_rendered(page, container, phase: str):
    h1 = await element.find_one(container, "h1")
    assert await element.get_text(page, h1) == "New Title", f"Heading {phase} not properly rendered"
    h2 = await element.find_one(container, "h2")
    assert await element.get_text(page, h2) == "New SubHeading", f"Subheading {phase} not properly rendered"
    p = await element.find_one(container, "p")
    assert await element.get_text(page, p) == "This is the normal content", (
        f"Normal {phase} content not properly rendered")


async def _toggle_forum(page):
    await course_nav.go2_tab(page, c.FORUM_ICON)
    forum_tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)

    if await forum_nav.is_forum_enabled(forum_tab_content):
        assert await element.find_one(forum_tab_content, c.FORUM_NEW_ENTRY_ICON) is not None, "Add Entry not found"
        assert await element.find_one(forum_tab_content, c.FORUM_EDIT_ENTRY_ICON) is not None, "Add Entry not found"
        await forum_nav.disable_forum(page)
        await forum_nav.enable_forum(page)
    else:
        await forum_nav.enable_forum(page)
        assert await element.find_one(forum_tab_content, c.FORUM_NEW_ENTRY_ICON) is not None, "Add Entry not found"
        assert await element.find_one(forum_tab_content, c.FORUM_EDIT_ENTRY_ICON) is not None, "Add Entry not found"
        await forum_nav.disable_forum(page)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_teacher_delete_course(user, mail, password, role):
    """Creates a dummy course and deletes it, checking the course count drops by exactly one.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)
    page = user.page
    course_name = f"Test Course_{int(time.time() * 1000)}"

    await navigation_utilities.to_courses_home(page, user.app_url)
    await wait.wait_for_page_loaded(page)
    await course_nav.new_course(page, user.app_url, course_name)

    all_courses_prior_deleting = await element.find_all(page, ".course-list-item")
    await course_nav.delete_course(page, user.app_url, course_name)
    all_courses = await element.find_all(page, ".course-list-item")
    assert len(all_courses_prior_deleting) - 1 == len(all_courses)
