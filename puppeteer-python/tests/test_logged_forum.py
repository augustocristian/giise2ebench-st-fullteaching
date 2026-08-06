# -*- coding: utf-8 -*-
"""Ported from functional/test/LoggedForumTest.java."""
from datetime import datetime

import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import forum_navigation_utilities as forum_nav
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.utils import click, dom_manager, element, wait
from fullteaching_e2e.utils.parameter_loader import get_test_users

COURSE_NAME = "Pseudoscientific course for treating the evil eye"


@pytest.mark.parametrize("mail,password,role", get_test_users())
async def test_forum_load_entries(user, mail, password, role):
    """Logs in, walks every course's forum (if enabled) and its entries/comments.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READONLY,10)
    executor/webbrowser/webserver(READWRITE,1).
    """
    user_name = await base_logged_test.slow_login(user, mail, password)
    page = user.page

    courses = await course_nav.get_courses_list(page, user.app_url)
    assert courses, "No courses in the list"

    activated_forum_on_some_test = False
    has_comments = False
    for course_name in courses:
        course = await course_nav.get_course_by_name(page, course_name)
        title_el = await element.find_one(course, c.COURSE_LIST_COURSE_TITLE)
        await click.element(page, title_el)
        await wait.not_too_much(page, c.TABS_DIV)

        await course_nav.go2_tab(page, c.FORUM_ICON)
        tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)
        if await forum_nav.is_forum_enabled(tab_content):
            activated_forum_on_some_test = True
            entries_list = await forum_nav.get_full_entry_list(page)
            for entry_name in entries_list:
                entry = await forum_nav.get_entry(page, entry_name)
                entry_title = await element.find_one(entry, c.FORUM_ENTRY_LIST_ENTRY_TITLE)
                await click.element(page, entry_title)

                await wait.not_too_much(page, c.FORUM_COMMENT_LIST)
                comments = await forum_nav.get_comments(page)
                if comments:
                    has_comments = True
                    await forum_nav.get_user_comments(page, user_name)
                # else go to next entry

                back_icon = await element.find_one(page, c.BACK_TO_ENTRIES_LIST_ICON)
                parent = await dom_manager.get_parent(page, back_icon)
                await click.element(page, parent)
            # else if no entries go to next course
        # else if forum not active go to next course

        await click.element(page, c.BACK_TO_DASHBOARD)

    assert activated_forum_on_some_test and has_comments, (
        "There isn't any forum that can be used to test this "
        "[Or not activated or no entry lists or not comments]")


@pytest.mark.parametrize("mail,password,role", get_test_users())
async def test_forum_new_entry(user, mail, password, role):
    """Creates a new forum entry and checks it appears with the right author/title/content.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    user_name = await base_logged_test.slow_login(user, mail, password)
    page = user.page

    now = datetime.now()
    new_entry_title = f"New Entry Test {now.day}{now.month}{now.year}{now.hour}{now.minute}{now.second}"
    new_entry_content = (
        f"This is the content written on the {now.day} of {now.strftime('%B')}, "
        f"{now.hour}:{now.minute},{now.second}")

    await navigation_utilities.to_courses_home(page, user.app_url)
    course = await course_nav.get_course_by_name(page, COURSE_NAME)
    title_el = await element.find_one(course, c.COURSE_LIST_COURSE_TITLE)
    await click.element(page, title_el)

    await wait.not_too_much(page, c.TABS_DIV)
    await course_nav.go2_tab(page, c.FORUM_ICON)
    tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)
    assert await forum_nav.is_forum_enabled(tab_content), "Forum not activated"
    await wait.wait_for_page_loaded(page)
    await forum_nav.new_entry(page, new_entry_title, new_entry_content)
    await wait.wait_for_page_loaded(page)

    new_entry = await forum_nav.get_entry(page, new_entry_title)
    await wait.wait_for_page_loaded(page)
    author_el = await element.find_one(new_entry, c.FORUM_ENTRY_LIST_ENTRY_USER)
    assert await element.get_text(page, author_el) == user_name, "Incorrect user"

    entry_title_el = await element.find_one(new_entry, c.FORUM_ENTRY_LIST_ENTRY_TITLE)
    await click.element(page, entry_title_el)
    await wait.not_too_much(page, c.FORUM_COMMENT_LIST)

    entry_title_row = await element.find_one(page, c.FORUM_COMMENT_LIST_ENTRY_TITLE)
    row_text = await element.get_text(page, entry_title_row)
    assert row_text.split("\n")[0] == new_entry_title, "Incorrect Entry Title"
    row_author = await element.find_one(entry_title_row, c.FORUM_COMMENT_LIST_ENTRY_USER)
    assert await element.get_text(page, row_author) == user_name, "Incorrect User for Entry"

    await wait.wait_for_page_loaded(page)
    comments = await forum_nav.get_comments(page)
    assert comments, "No comments on the entry"
    await wait.not_too_much(page, c.FORUM_COMMENT_LIST)
    await wait.wait_for_page_loaded(page)

    new_comment = comments[0]
    content_el = await element.find_one(new_comment, c.FORUM_COMMENT_LIST_COMMENT_CONTENT)
    assert await element.get_text(page, content_el) == new_entry_content, "Bad content of comment"
    await wait.wait_for_page_loaded(page)
    comment_author_el = await element.find_one(new_comment, c.FORUM_COMMENT_LIST_COMMENT_USER)
    assert await element.get_text(page, comment_author_el) == user_name, "Bad user in comment"

    # Navigate to the main page first to avoid a flaky logout
    await page.goto(user.app_url)


@pytest.mark.parametrize("mail,password,role", get_test_users())
async def test_forum_new_comment(user, mail, password, role):
    """Adds a comment to the course forum's first entry (creating one first if none exist).

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    user_name = await base_logged_test.slow_login(user, mail, password)
    page = user.page
    now = datetime.now()

    await navigation_utilities.to_courses_home(page, user.app_url)
    course = await course_nav.get_course_by_name(page, COURSE_NAME)
    title_el = await element.find_one(course, c.COURSE_LIST_COURSE_TITLE)
    await click.element(page, title_el)
    await wait.not_too_much(page, c.TABS_DIV)
    await course_nav.go2_tab(page, c.FORUM_ICON)
    tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)
    assert await forum_nav.is_forum_enabled(tab_content), "Forum not activated"

    entries_list = await forum_nav.get_full_entry_list(page)
    if not entries_list:
        new_entry_title = f"New Comment Test {now.day}{now.month}{now.year}{now.hour}{now.minute}{now.second}"
        new_entry_content = (
            f"This is the content written on the {now.day} of {now.strftime('%B')}, "
            f"{now.hour}:{now.minute},{now.second}")
        await forum_nav.new_entry(page, new_entry_title, new_entry_content)
        entry = await forum_nav.get_entry(page, new_entry_title)
    else:
        entry = await forum_nav.get_entry(page, entries_list[0])

    entry_title_el = await element.find_one(entry, c.FORUM_ENTRY_LIST_ENTRY_TITLE)
    await click.element(page, entry_title_el)
    comment_list = await wait.not_too_much(page, c.FORUM_COMMENT_LIST)

    number_comments_old = len(await forum_nav.get_comments(page))

    new_comment_icon = await element.find_one(comment_list, c.FORUM_COMMENT_LIST_NEW_COMMENT_ICON)
    await click.element(page, new_comment_icon)
    await wait.a_little(page, c.FORUM_NEW_COMMENT_MODAL)

    new_comment_content = (
        f"COMMENT TEST{now.day}{now.month}{now.year}{now.hour}{now.minute}{now.second}. "
        f"This is the comment written on the {now.day} of {now.strftime('%B')}, "
        f"{now.hour}:{now.minute},{now.second}")
    comment_field = await element.find_one(page, c.FORUM_NEW_COMMENT_MODAL_TEXT_FIELD)
    await comment_field.type(new_comment_content)
    await click.element(page, c.FORUM_NEW_COMMENT_MODAL_POST_BUTTON)

    await wait.not_too_much(page, c.FORUM_COMMENT_LIST)
    await wait.wait_for_page_loaded(page)
    await user.wait_until(lambda: wait.not_too_much(page, c.FORUM_COMMENT_LIST_COMMENT),
                           "The comment list are not visible")

    async def _comment_count_increased():
        count = len(await forum_nav.get_comments(page))
        if count <= number_comments_old:
            raise TimeoutError("comment not attached yet")
        return count

    await user.wait_until(lambda: wait.poll_until(_comment_count_increased), "Comment not attached")

    comments = await forum_nav.get_comments(page)
    assert len(comments) > number_comments_old, "Comment list empty or only original comment"
    await user.wait_until(lambda: wait.not_too_much(page, c.FORUM_COMMENT_LIST_COMMENT),
                           "The comment list are not visible")

    comment_found = False
    for comment in comments:
        content_el = await element.find_one(comment, c.FORUM_COMMENT_LIST_COMMENT_CONTENT)
        text = await element.get_text(page, content_el)
        if text == new_comment_content:
            comment_found = True
            author_el = await element.find_one(comment, c.FORUM_COMMENT_LIST_COMMENT_USER)
            assert await element.get_text(page, author_el) == user_name, "Bad user in comment"
    assert comment_found, "Comment not found"


@pytest.mark.parametrize("mail,password,role", get_test_users())
async def test_forum_new_reply_to_comment(user, mail, password, role):
    """Replies to the first comment of the course forum's first entry.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    user_name = await base_logged_test.slow_login(user, mail, password)
    page = user.page
    now = datetime.now()

    await navigation_utilities.to_courses_home(page, user.app_url)
    course = await course_nav.get_course_by_name(page, COURSE_NAME)
    title_el = await element.find_one(course, c.COURSE_LIST_COURSE_TITLE)
    await click.element(page, title_el)
    await wait.not_too_much(page, c.TABS_DIV)
    await course_nav.go2_tab(page, c.FORUM_ICON)
    tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)
    assert await forum_nav.is_forum_enabled(tab_content), "Forum not activated"

    entries_list = await forum_nav.get_full_entry_list(page)
    if not entries_list:
        new_entry_title = f"New Comment Test {now.day}{now.month}{now.year}{now.hour}{now.minute}{now.second}"
        new_entry_content = (
            f"This is the content written on the {now.day} of {now.strftime('%B')}, "
            f"{now.hour}:{now.minute},{now.second}")
        await forum_nav.new_entry(page, new_entry_title, new_entry_content)
        entry = await forum_nav.get_entry(page, new_entry_title)
    else:
        entry = await forum_nav.get_entry(page, entries_list[0])

    entry_title_el = await element.find_one(entry, c.FORUM_ENTRY_LIST_ENTRY_TITLE)
    await click.element(page, entry_title_el)
    await wait.not_too_much(page, c.FORUM_COMMENT_LIST)
    comments = await forum_nav.get_comments(page)

    comment = comments[0]
    reply_icon = await element.find_one(comment, c.FORUM_COMMENT_LIST_COMMENT_REPLY_ICON)
    await click.element(page, reply_icon)

    new_reply_content = (
        f"This is the reply written on the {now.day} of {now.strftime('%B')}, "
        f"{now.hour}:{now.minute},{now.second}")
    await wait.not_too_much(page, c.FORUM_COMMENT_LIST_MODAL_NEW_REPLY)
    text_field = await element.find_one(page, c.FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD)
    await text_field.type(new_reply_content)
    await click.element(page, c.FORUM_NEW_COMMENT_MODAL_POST_BUTTON)

    await user.wait_until(lambda: wait.not_too_much(page, c.FORUM_COMMENT_LIST_MODAL_NEW_REPLY,
                                                      visible=False, hidden=True),
                           "The model is still visible")
    await user.wait_until(lambda: wait.not_too_much(page, c.FORUM_COMMENT_LIST), "The comments are not visible")
    await user.wait_until(lambda: wait.not_too_much(page, c.FORUM_COMMENT_LIST_COMMENT),
                           "The comment list are not visible")

    comments = await forum_nav.get_comments(page)
    replies = await forum_nav.get_replies(page, comments[0])
    new_reply = None
    for reply in replies:
        text = await element.get_text(page, reply)
        if new_reply_content in text:
            new_reply = reply

    assert new_reply is not None, "Reply not found"
    author_el = await element.find_one(new_reply, c.FORUM_COMMENT_LIST_COMMENT_USER)
    assert await element.get_text(page, author_el) == user_name, "Bad user in comment"
