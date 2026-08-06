# -*- coding: utf-8 -*-
"""Ported from functional/test/media/FullTeachingEndToEndRESTTests.java.

Covers course/session/forum/file/attenders CRUD through the UI. Selectors here are inline
strings rather than named Constants, matching how the Java source keeps them local to this
test class rather than in common/Constants.java.
"""
import datetime
from pathlib import Path

import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.utils import click, element, keyboard, wait
from fullteaching_e2e.utils.parameter_loader import get_test_teachers

COURSE_NAME = "TEST_COURSE"
EDITED = " EDITED"
TEST_COURSE_INFO = "TEST_COURSE_INFO"
_TEST_FILE = Path(__file__).resolve().parents[1] / "resources" / "testFile.txt"


async def _login_and_create_new_course(user, mail: str, password: str):
    await base_logged_test.slow_login(user, mail, password)
    await course_nav.new_course(user.page, user.app_url, COURSE_NAME)


async def _edit_course(user):
    page = user.page
    edited_course_name = COURSE_NAME + EDITED
    edit_icons = await element.find_all(page, c.EDIT_COURSE_BUTTON)
    await base_logged_test.open_dialog(user, edit_icons[-1])
    await user.wait_until(lambda: wait.not_too_much(page, c.EDIT_COURSE_MODAL_NAME_FIELD),
                           "Input for course name not clickable")
    course_name_input = await element.find_one(page, c.EDIT_COURSE_MODAL_NAME_FIELD)
    await keyboard.clear(page, course_name_input)
    await course_name_input.type(edited_course_name)
    await click.element(page, c.EDIT_COURSE_MODAL_SAVE)
    await base_logged_test.wait_for_dialog_closed(user, "put-delete-course-modal", "Edition of course failed")

    async def _course_name_updated():
        last_title = await element.find_one(page, "#course-list .course-list-item:last-child div.course-title span")
        if await element.get_text(page, last_title) != edited_course_name:
            raise TimeoutError("course name not yet updated")

    await user.wait_until(lambda: wait.poll_until(_course_name_updated), "Unexpected course name")


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_course_rest_operations(user, mail, password, role):
    """Create -> edit -> delete a course through the REST-backed UI forms.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) configuration(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await _login_and_create_new_course(user, mail, password)
    await _edit_course(user)
    await course_nav.delete_course(user.page, user.app_url, COURSE_NAME + EDITED)


async def _enter_course_and_navigate_tab(user, course_name: str, tab_id: str):
    page = user.page
    # These tests always create a new course, so wait for 3 courses in the main page (more than 2)
    await user.wait_until(
        lambda: wait.poll_until(lambda: _more_than_n_courses(page, 2)),
        "The number of courses should be 3")
    all_courses = await element.find_all(page, "#course-list .course-list-item div.course-title span")
    course_span = None
    for span in all_courses:
        if await element.get_text(page, span) == course_name:
            course_span = span
            break
    assert course_span is not None, (
        f"The course with the name '{course_name}' could not be found. "
        f"Total courses available: {len(all_courses)}")
    await click.element(page, course_span)
    await user.wait_until(lambda: _title_is(page, course_name), "Unexpected course title")
    await click.element(page, f"#{tab_id}")


async def _more_than_n_courses(page, n: int):
    spans = await element.find_all(page, "#course-list .course-list-item div.course-title span")
    if len(spans) <= n:
        raise TimeoutError(f"only {len(spans)} courses so far")
    return spans


async def _title_is(page, expected: str):
    title = await element.find_one(page, "#main-course-title")
    if await element.get_text(page, title) != expected:
        raise TimeoutError("course title not updated yet")


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_course_info_rest_operations(user, mail, password, role):
    """Edits a course's Home-tab description and checks it renders back.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) information(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    page = user.page
    await _login_and_create_new_course(user, mail, password)
    await _enter_course_and_navigate_tab(user, COURSE_NAME, "info-tab-icon")

    await user.wait_until(
        lambda: wait.not_too_much(page, ".md-tab-body.md-tab-active .card-panel.warning"),
        "Course info wasn't empty")

    edit_button = await element.find_one(page, "#edit-course-info")
    await click.element(page, edit_button)
    editor = await element.find_one(page, ".ql-editor")
    await editor.type(TEST_COURSE_INFO)
    await click.element(page, "#send-info-btn")

    async def _info_saved():
        p = await element.find_one(page, ".ql-editor p")
        if await element.get_text(page, p) != TEST_COURSE_INFO:
            raise TimeoutError("course info not saved yet")

    await user.wait_until(lambda: wait.poll_until(_info_saved), "Unexpected course info")
    await course_nav.delete_course(page, user.app_url, COURSE_NAME)


# pyppeteer only ever drives Chromium, so unlike Java's BROWSER_NAME-conditional formatting
# this is always the "chrome" branch: MM/dd/yyyy dates, zero-padded 12-hour + AM/PM times.
_DATE_FORMAT = "%m/%d/%Y"
_TIME_FORMAT = "%I:%M%p"


async def _fill_session_form(page, title: str, comment: str, date, hour, edit: bool):
    title_field = await element.find_one(page, "#input-put-title" if edit else "#input-post-title")
    comment_field = await element.find_one(page, "#input-put-comment" if edit else "#input-post-comment")
    date_field = await element.find_one(page, "#input-put-date" if edit else "#input-post-date")
    time_field = await element.find_one(page, "#input-put-time" if edit else "#input-post-time")
    if edit:
        await keyboard.clear(page, title_field)
        await keyboard.clear(page, comment_field)
    await title_field.type(title)
    await comment_field.type(comment)
    await date_field.type(date.strftime(_DATE_FORMAT))
    await time_field.type(hour.strftime(_TIME_FORMAT))
    await click.element(page, "#put-modal-btn" if edit else "#post-modal-btn")


async def _verify_session_details(user, expected_title: str, expected_comment: str, *expected_date_times: str):
    page = user.page
    await user.wait_until(lambda: wait.not_too_much(page, "li.session-data .session-title"),
                           "Unexpected session title")
    title = await element.find_one(page, "li.session-data .session-title")
    assert await element.get_text(page, title) == expected_title

    await user.wait_until(lambda: wait.not_too_much(page, "li.session-data .session-description"),
                           "The element located by css li.session-data .session-description is not visible")
    comment = await element.find_one(page, "li.session-data .session-description")
    assert await element.get_text(page, comment) == expected_comment

    await user.wait_until(lambda: wait.not_too_much(page, "li.session-data .session-datetime"),
                           "The element located by css li.session-data .session-datetime is not visible")
    date_time = await element.find_one(page, "li.session-data .session-datetime")
    actual = await element.get_text(page, date_time)
    assert actual in expected_date_times


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_session_rest_operations(user, mail, password, role):
    """Create -> edit -> delete a video session through the REST-backed UI forms.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) session(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    page = user.page
    await _login_and_create_new_course(user, mail, password)

    await _enter_course_and_navigate_tab(user, COURSE_NAME, "sessions-tab-icon")
    await base_logged_test.open_dialog(user, "#add-session-icon")
    await _fill_session_form(page, "TEST LESSON NAME", "TEST LESSON COMMENT",
                              datetime.date(2018, 3, 1), datetime.time(15, 10), edit=False)
    await base_logged_test.wait_for_dialog_closed(user, "course-details-modal", "Addition of session failed")
    await _verify_session_details(user, "TEST LESSON NAME", "TEST LESSON COMMENT",
                                   "Jan 3, 2018 - 03:10", "Mar 1, 2018 - 15:10")

    await base_logged_test.open_dialog(user, ".edit-session-icon")
    await _fill_session_form(page, "TEST LESSON NAME EDITED", "TEST LESSON COMMENT EDITED",
                              datetime.date(2019, 4, 2), datetime.time(5, 10), edit=True)
    await base_logged_test.wait_for_dialog_closed(user, "put-delete-modal", "Edition of session failed")
    await _verify_session_details(user, "TEST LESSON NAME EDITED", "TEST LESSON COMMENT EDITED",
                                   "Feb 4, 2019 - 05:10", "Apr 2, 2019 - 05:10")

    await base_logged_test.open_dialog(user, ".edit-session-icon")
    await user.wait_until(lambda: wait.not_too_much(page, "#label-delete-checkbox"),
                           "Checkbox for session deletion not clickable")
    await click.element(page, "#label-delete-checkbox")
    await user.wait_until(lambda: wait.not_too_much(page, "#delete-session-btn"),
                           "Button for session deletion not clickable")
    await click.element(page, "#delete-session-btn")
    await base_logged_test.wait_for_dialog_closed(user, "put-delete-modal", "Deletion of session failed")

    async def _no_sessions_left():
        sessions = await element.find_all(page, "li.session-data")
        if sessions:
            raise TimeoutError("session still present")

    await user.wait_until(lambda: wait.poll_until(_no_sessions_left), "Unexpected number of sessions")

    await course_nav.delete_course(page, user.app_url, COURSE_NAME)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_forum_rest_operations(user, mail, password, role):
    """Add a forum entry, comment on it, reply to that comment, then deactivate the forum.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    page = user.page
    await _login_and_create_new_course(user, mail, password)
    await _enter_course_and_navigate_tab(user, COURSE_NAME, "forum-tab-icon")

    await base_logged_test.open_dialog(user, "#add-entry-icon")
    title_field = await element.find_one(page, "#input-post-title")
    comment_field = await element.find_one(page, "#input-post-comment")
    title = "TEST FORUM ENTRY"
    comment = "TEST FORUM COMMENT"
    entry_date = "a few seconds ago"
    await title_field.type(title)
    await comment_field.type(comment)
    await click.element(page, "#post-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "course-details-modal", "Addition of entry failed")

    entry_el = await element.find_one(page, "li.entry-title")
    await user.wait_until(lambda: _text_is(page, "li.entry-title .forum-entry-title", title),
                           "Unexpected entry title in the forum")
    await user.wait_until(lambda: _text_is(page, "li.entry-title .forum-entry-author", c.TEACHER_NAME),
                           "Unexpected entry author in the forum")
    await user.wait_until(lambda: _text_is(page, "li.entry-title .forum-entry-date", entry_date),
                           "Unexpected entry date in the forum")

    await click.element(page, entry_el)
    await user.wait_until(
        lambda: _text_is(page, ".comment-block > app-comment:first-child > div.comment-div .message-itself",
                          comment),
        "Unexpected entry title in the entry details view")
    await user.wait_until(
        lambda: _text_is(page, ".comment-block > app-comment:first-child > div.comment-div .forum-comment-author",
                          c.TEACHER_NAME),
        "Unexpected entry author in the entry details view")

    reply = "TEST FORUM REPLY"
    await base_logged_test.open_dialog(user, ".replay-icon")
    comment_field = await element.find_one(page, "#input-post-comment")
    await comment_field.type(reply)
    await click.element(page, "#post-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "course-details-modal", "Addition of entry reply failed")
    await user.wait_until(
        lambda: _text_is(
            page, ".comment-block > app-comment:first-child > div.comment-div div.comment-div .message-itself",
            reply),
        "Unexpected reply message in the entry details view")
    await user.wait_until(
        lambda: _text_is(
            page,
            ".comment-block > app-comment:first-child > div.comment-div div.comment-div .forum-comment-author",
            c.TEACHER_NAME),
        "Unexpected reply author in the entry details view")

    await click.element(page, "#entries-sml-btn")
    await base_logged_test.open_dialog(user, "#edit-forum-icon")
    await user.wait_until(lambda: wait.not_too_much(page, "#label-forum-checkbox"),
                           "Checkbox for forum deactivation not clickable")
    await click.element(page, "#label-forum-checkbox")
    await user.wait_until(lambda: wait.not_too_much(page, "#put-modal-btn"),
                           "Button for forum deactivation not clickable")
    await click.element(page, "#put-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "put-delete-modal", "Deactivation of forum failed")
    await user.wait_until(lambda: wait.not_too_much(page, "app-error-message .card-panel.warning"),
                           "Warning card (forum deactivated) missing")

    await course_nav.delete_course(page, user.app_url, COURSE_NAME)


async def _text_is(page, selector: str, expected: str):
    el = await element.find_one(page, selector)
    if el is None or await element.get_text(page, el) != expected:
        raise TimeoutError(f"'{selector}' text not yet '{expected}'")


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_files_rest_operations(user, mail, password, role):
    """Add a file group, a sub-group and a file to it, edit their names, then delete the group.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) files(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    page = user.page
    await _login_and_create_new_course(user, mail, password)
    await _enter_course_and_navigate_tab(user, COURSE_NAME, "files-tab-icon")

    await user.wait_until(lambda: wait.not_too_much(page, "app-error-message .card-panel.warning"),
                           "Warning card (course with no files) missing")

    file_group = "TEST FILE GROUP"
    await base_logged_test.open_dialog(user, "#add-files-icon")
    title_field = await element.find_one(page, "#input-post-title")
    await title_field.type(file_group)
    await click.element(page, "#post-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "course-details-modal", "Addition of file group failed")
    await user.wait_until(lambda: _text_is(page, ".file-group-title h5", file_group), "Unexpected file group name")

    await base_logged_test.open_dialog(user, "#edit-filegroup-icon")
    title_field = await element.find_one(page, "#input-file-title")
    await keyboard.clear(page, title_field)
    await title_field.type(file_group + EDITED)
    await click.element(page, "#put-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "put-delete-modal", "Edition of file group failed")
    await user.wait_until(lambda: _text_is(page, "app-file-group .file-group-title h5", file_group + EDITED),
                           "Unexpected file group name")

    file_subgroup = "TEST FILE SUBGROUP"
    await base_logged_test.open_dialog(user, ".add-subgroup-btn")
    title_field = await element.find_one(page, "#input-post-title")
    await title_field.type(file_subgroup)
    await click.element(page, "#post-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "course-details-modal", "Addition of file sub-group failed")
    await user.wait_until(
        lambda: _text_is(page, "app-file-group app-file-group .file-group-title h5", file_subgroup),
        "Unexpected file sub-group name")

    await base_logged_test.open_dialog(user, "app-file-group app-file-group .add-file-btn")
    file_uploader = await element.find_one(page, ".input-file-uploader")
    file_name = _TEST_FILE.name
    await page.evaluate("(el) => el.setAttribute('style', 'display:block')", file_uploader)
    await user.wait_until(
        lambda: wait.not_too_much(page, 'xpath=//input[contains(@class, "input-file-uploader") '
                                         'and contains(@style, "display:block")]'),
        "Waiting for the input file to be displayed")
    await file_uploader.uploadFile(str(_TEST_FILE))
    await click.element(page, "#upload-all-btn")
    await user.wait_until(
        lambda: wait.not_too_much(page, 'xpath=//div[contains(@class, "determinate") '
                                         'and contains(@style, "width: 100")]'),
        "Upload process not completed. Progress bar not filled")
    await user.wait_until(lambda: _text_is(page, 'xpath=//i[contains(@class, "icon-status-upload")]', "done"),
                           "Upload process failed")

    await click.element(page, "#close-upload-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "course-details-modal", "Upload of file failed")
    await user.wait_until(
        lambda: _text_is(page, "app-file-group app-file-group .chip .file-name-div", file_name),
        "Unexpected uploaded file name")

    await base_logged_test.open_dialog(user, "app-file-group app-file-group .edit-file-name-icon")
    title_field = await element.find_one(page, "#input-file-title")
    await keyboard.clear(page, title_field)
    edited_file_name = "testFileEDITED.txt"
    await title_field.type(edited_file_name)
    await click.element(page, "#put-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "put-delete-modal", "Edition of file failed")
    await user.wait_until(
        lambda: _text_is(page, "app-file-group app-file-group .chip .file-name-div", edited_file_name),
        "Unexpected uploaded file name")

    delete_icon = await element.find_one(page, "app-file-group .delete-filegroup-icon")
    await click.element(page, delete_icon)
    await user.wait_until(lambda: wait.not_too_much(page, "app-error-message .card-panel.warning"),
                           "Warning card (course with no files) missing")

    await course_nav.delete_course(page, user.app_url, COURSE_NAME)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_attenders_rest_operations(user, mail, password, role):
    """Fails to add an unregistered attender, adds a real one, then removes them.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) attenders(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    page = user.page
    await _login_and_create_new_course(user, mail, password)
    await _enter_course_and_navigate_tab(user, COURSE_NAME, "attenders-tab-icon")

    async def _attender_count_is(n: int):
        rows = await element.find_all(page, ".attender-row-div")
        if len(rows) != n:
            raise TimeoutError(f"expected {n} attenders, got {len(rows)}")

    await user.wait_until(lambda: wait.poll_until(lambda: _attender_count_is(1)),
                           "Unexpected number of attenders for the course")
    await user.wait_until(lambda: _text_is(page, ".attender-row-div .attender-name-p", c.TEACHER_NAME),
                           "Unexpected name for the attender")

    # Add attender fail
    await base_logged_test.open_dialog(user, "#add-attenders-icon")
    title_field = await element.find_one(page, "#input-attender-simple")
    await title_field.type("studentFail@gmail.com")
    await click.element(page, "#put-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "put-delete-modal", "Addition of attender fail")
    await user.wait_until(lambda: wait.not_too_much(page, "app-error-message .card-panel.fail"),
                           "Error card (attender not added to the course) missing")
    await user.wait_until(lambda: wait.poll_until(lambda: _attender_count_is(1)),
                           "Unexpected number of attenders for the course")
    dismiss_fail = await element.find_one(page, "app-error-message .card-panel.fail .material-icons")
    await click.element(page, dismiss_fail)

    # Add attender success
    await base_logged_test.open_dialog(user, "#add-attenders-icon")
    title_field = await element.find_one(page, "#input-attender-simple")
    await title_field.type("student1@gmail.com")
    await click.element(page, "#put-modal-btn")
    await base_logged_test.wait_for_dialog_closed(user, "put-delete-modal", "Addition of attender failed")
    await user.wait_until(lambda: wait.not_too_much(page, "app-error-message .card-panel.correct"),
                           "Success card (attender properly added to the course) missing")
    await user.wait_until(lambda: wait.poll_until(lambda: _attender_count_is(2)),
                           "Unexpected number of attenders for the course")
    dismiss_success = await element.find_one(page, "app-error-message .card-panel.correct .material-icons")
    await click.element(page, dismiss_success)

    # Remove attender
    await click.element(page, "#edit-attenders-icon")
    await user.wait_until(lambda: wait.not_too_much(page, ".del-attender-icon"),
                           "Button for attender deletion not clickable")
    await click.element(page, ".del-attender-icon")
    await user.wait_until(lambda: wait.poll_until(lambda: _attender_count_is(1)),
                           "Unexpected number of attenders for the course")

    await course_nav.delete_course(page, user.app_url, COURSE_NAME)
