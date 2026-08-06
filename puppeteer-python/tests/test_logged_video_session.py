# -*- coding: utf-8 -*-
"""Ported from functional/test/media/FullTeachingLoggedVideoSessionTests.java.

`studentNameList`/`studentNamesList`/`studentPassList` from the Java class are not ported:
they're populated in initializeStudents() but never read anywhere afterwards (write-only
dead fields) - only the actual BrowserUser list matters, which browser_factory already
tracks for us.
"""
from datetime import datetime
from pathlib import Path
from typing import List

import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import session_navigation_utilities as session_nav
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils import click, element, wait
from fullteaching_e2e.utils.parameter_loader import get_test_teachers

COURSE_NAME = "Pseudoscientific course for treating the evil eye"
_STUDENTS_FILE = Path(__file__).resolve().parents[1] / "resources" / "inputs" / "default_user_LoggedVideoStudents.csv"


async def _initialize_students(browser_factory) -> List[BrowserUser]:
    raw = _STUDENTS_FILE.read_text(encoding="utf-8").strip()
    students = []
    for entry in raw.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        userid, password, browser = entry.split(":")
        student = await browser_factory(userid, browser=browser, seconds_of_wait=c.WAIT_SECONDS)
        await base_logged_test.slow_login(student, userid, password)
        students.append(student)
    return students


def _get_current_session_hour() -> str:
    now = datetime.now()
    return now.strftime("%I%M") + ("A" if now.strftime("%p") == "AM" else "P")


async def _date_field_value_is(page, date_field, expected: str):
    async def _check():
        actual = await element.get_dom_property(page, date_field, "value")
        if actual != expected:
            raise TimeoutError("date value not set yet")

    await wait.poll_until(_check)


async def _introduce_session_date(browser_user: BrowserUser, modal):
    page = browser_user.page
    expected_date = datetime.now().strftime("%Y-%m-%d")
    date_field = await element.find_one(modal, c.SESSION_LIST_NEW_SESSION_MODAL_DATE)
    # <input type=date>.value is always ISO 8601 regardless of display locale, so setting it
    # directly via JS (and firing input/change so Angular's ngModel updates) is simpler and
    # more reliable than typing a locale-formatted string - which is what the Java version
    # does, to work around Selenium/ChromeDriver-specific typing quirks that don't apply here.
    await page.evaluate(
        "(el, value) => { el.value = value; "
        "el.dispatchEvent(new Event('input', {bubbles: true})); "
        "el.dispatchEvent(new Event('change', {bubbles: true})); }",
        date_field, expected_date)
    await browser_user.wait_until(lambda: _date_field_value_is(page, date_field, expected_date),
                                   "Failed to set the session date")


async def _create_new_session(browser_user: BrowserUser, session_name: str):
    page = browser_user.page
    session_hour = _get_current_session_hour()
    session_description = "Wow today session will be amazing"

    await _navigate_to_course(browser_user, COURSE_NAME)
    await click.element(page, c.SESSION_LIST_NEW_SESSION_ICON)
    modal = await wait.not_too_much(page, c.SESSION_LIST_NEW_SESSION_MODAL)

    title_field = await element.find_one(modal, c.SESSION_LIST_NEW_SESSION_MODAL_TITLE)
    await title_field.type(session_name)
    content_field = await element.find_one(modal, c.SESSION_LIST_NEW_SESSION_MODAL_CONTENT)
    await content_field.type(session_description)
    await _introduce_session_date(browser_user, modal)
    time_field = await element.find_one(modal, c.SESSION_LIST_NEW_SESSION_MODAL_TIME)
    await time_field.type(session_hour)
    post_button = await element.find_one(modal, c.SESSION_LIST_NEW_SESSION_MODAL_POST_BUTTON)
    await click.element(page, post_button)
    await wait.wait_for_page_loaded(page)

    async def _more_than_3_sessions():
        rows = await element.find_all(page, c.SESSION_LIST_SESSION_ROW)
        if len(rows) <= 3:
            raise TimeoutError("not enough sessions yet")

    await browser_user.wait_until(lambda: wait.poll_until(_more_than_3_sessions),
                                   "Incorrect number of sessions (never more than 2)")
    session_titles = await session_nav.get_full_session_list(page)
    assert session_name in session_titles, "Session has not been created"


async def _join_session(browser_user: BrowserUser, session_name: str):
    page = browser_user.page
    session_titles = await session_nav.get_full_session_list(page)
    assert session_name in session_titles, "Session has not been created"
    session = await session_nav.get_session(page, session_name)
    access_button = await element.find_one(session, c.SESSION_LIST_SESSION_ACCESS)
    await click.element(page, access_button)


async def _navigate_to_course(browser_user: BrowserUser, course_name: str):
    page = browser_user.page
    courses = await course_nav.get_courses_list(page, browser_user.app_url)
    assert courses, "No courses in the list"
    course = await course_nav.get_course_by_name(page, course_name)
    title_el = await element.find_one(course, c.COURSE_LIST_COURSE_TITLE)
    await click.element(page, title_el)
    await wait.not_too_much(page, c.TABS_DIV)
    await course_nav.go2_tab(page, c.SESSION_ICON)


async def _leave_session(browser_user: BrowserUser):
    page = browser_user.page
    await click.element(page, c.SESSION_LEFT_MENU_BUTTON)
    exit_button = await element.find_one(page, c.SESSION_EXIT_ICON)
    await click.by_js(page, exit_button)
    await wait.wait_for_page_loaded(page)
    await wait.not_too_much(page, c.COURSE_TABS)


async def _delete_session(browser_user: BrowserUser, session_name: str):
    page = browser_user.page
    session = await session_nav.get_session(page, session_name)
    edit_icon = await element.find_one(session, c.SESSION_LIST_SESSION_EDIT_ICON)
    await click.element(page, edit_icon)
    modal = await wait.not_too_much(page, c.SESSION_LIST_EDIT_MODAL)
    delete_div = await element.find_one(modal, c.SESSION_LIST_EDIT_MODAL_DELETE_DIV)
    await click.element(page, await element.find_one(delete_div, "label"))
    await click.element(page, await element.find_one(delete_div, "a"))
    await wait.wait_for_page_loaded(page)
    session_titles = await session_nav.get_full_session_list(page)
    assert session_name not in session_titles, "Session has not been deleted"


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_session(user, browser_factory, mail, password, role):
    """Creates a video session, has the teacher and every student join it, then everyone
    leaves and the session is deleted.

    Resources: loginservice(READONLY,10) openvidu(READWRITE,10) session(READONLY,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    session_name = "Today's Session"
    await base_logged_test.slow_login(user, mail, password)
    students = await _initialize_students(browser_factory)

    await _create_new_session(user, session_name)
    await _join_session(user, session_name)
    for student in students:
        await _navigate_to_course(student, COURSE_NAME)
        await _join_session(student, session_name)

    for student in students:
        await _leave_session(student)
    await _leave_session(user)

    await _delete_session(user, session_name)
