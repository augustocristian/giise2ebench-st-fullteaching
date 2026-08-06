# -*- coding: utf-8 -*-
"""Forum navigation helpers, ported from common/ForumNavigationUtilities.java."""
import logging
from typing import List

from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common.exceptions import ElementNotFoundException
from fullteaching_e2e.utils import click, element, wait

logger = logging.getLogger(__name__)

_ENTRY_TITLE_ROW = ".entry-title"


async def is_forum_enabled(forum_tab_content) -> bool:
    logger.info("Checking if the forum is enabled")
    found = await element.find_one(forum_tab_content, c.FORUM_NEW_ENTRY_ICON)
    if found is not None:
        logger.info("Forum enabled, looking for NEW ENTRY ICON")
        return True
    logger.info("Forum Disabled")
    return False


async def get_full_entry_list(page) -> List[str]:
    await wait.not_too_much(page, c.FORUM_ICON)
    tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)
    entries = await element.find_all(tab_content, _ENTRY_TITLE_ROW)
    titles = []
    for entry in entries:
        title_el = await element.find_one(entry, c.FORUM_ENTRY_LIST_ENTRY_TITLE)
        titles.append(await element.get_text(page, title_el))
    return titles


async def get_user_entries(page, user_name: str) -> List[str]:
    tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)
    entries = await element.find_all(tab_content, _ENTRY_TITLE_ROW)
    titles = []
    for entry in entries:
        entry_text = await element.get_text(page, entry)
        if user_name in entry_text:
            title_el = await element.find_one(entry, c.FORUM_ENTRY_LIST_ENTRY_TITLE)
            titles.append(await element.get_text(page, title_el))
    return titles


async def get_entry(page, entry_name: str):
    logger.info("Getting the entry with title %s", entry_name)

    await wait.not_too_much(page, c.FORUM_ICON)
    tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)
    entries = await element.find_all(tab_content, _ENTRY_TITLE_ROW)
    for entry in entries:
        title = await element.find_one(entry, c.FORUM_ENTRY_LIST_ENTRY_TITLE)
        if title is None:
            continue
        title_text = await element.get_text(page, title)
        if not title_text:
            title_text = await element.get_attribute(page, title, "innerHTML")
        if entry_name == title_text:
            return entry
        logger.info("Entry not found, the current title is %s", title_text)
    raise ElementNotFoundException(
        f'[getEntry] The entry with title "{entry_name}" the entry doesn\'t exist, '
        f'the number of entries was {len(entries)}')


async def get_comments(page) -> List:
    logger.info("Getting entry comments")

    async def _more_than_zero():
        comments = await element.find_all(page, c.FORUM_COMMENT_LIST_COMMENT)
        if not comments:
            raise TimeoutError("no comments yet")
        return comments

    return await wait.poll_until(_more_than_zero)


async def get_user_comments(page, user_name: str) -> List:
    user_comments = []
    await get_comments(page)
    all_comments = await element.find_all(page, c.FORUM_COMMENT_LIST_COMMENT)
    logger.info("Getting the comments of the user: %s ", user_name)
    for comment in all_comments:
        author = await element.find_one(comment, c.FORUM_COMMENT_LIST_COMMENT_USER)
        comment_username = await element.get_text(page, author)
        if user_name == comment_username:
            user_comments.append(comment)
    return user_comments


async def get_high_lighted_comments(page, user_name: str) -> List:
    user_comments = []
    all_comments = await element.find_all(page, c.FORUM_COMMENT_LIST_COMMENT)
    for comment in all_comments:
        author = await element.find_one(comment, c.FORUM_COMMENT_LIST_COMMENT_USER)
        comment_username = await element.get_text(page, author)
        if user_name == comment_username:
            user_comments.append(comment)
    return user_comments


async def new_entry(page, new_entry_title: str, new_entry_content: str):
    logger.info("Creating a new entry")
    await course_nav.go2_tab(page, c.FORUM_ICON)
    tab_content = await course_nav.get_tab_content(page, c.FORUM_ICON)
    assert await is_forum_enabled(tab_content), "Forum not activated"
    await click.element(page, c.FORUM_NEW_ENTRY_ICON)
    await wait.not_too_much(page, c.FORUM_NEW_ENTRY_MODAL)

    title = await wait.a_little(page, c.FORUM_NEW_ENTRY_MODAL_TITLE)
    logger.info("Setting the title: %s", title)
    await title.type(new_entry_title)
    comment = await wait.a_little(page, c.FORUM_NEW_ENTRY_MODAL_CONTENT)
    logger.info("Setting the title: %s", new_entry_content)
    await comment.type(new_entry_content)

    logger.info("Click the publish button")
    await click.element(page, c.FORUM_NEW_ENTRY_MODAL_POST_BUTTON)

    await wait.not_too_much(page, c.FORUM_ENTRY_LIST_ENTRIES_UL)
    await wait.wait_for_page_loaded(page)
    await get_entry(page, new_entry_title)
    return page


async def get_replies(page, comment) -> List:
    logger.info("Get all the replies of the selected comment")
    await wait.not_too_much(page, c.FORUM_COMMENT_LIST_COMMENT_DIV)
    nested_comments = await element.find_all(comment, c.FORUM_COMMENT_LIST_COMMENT_DIV)
    # ignore first, it is the original comment
    return nested_comments[1:]


async def enable_forum(page):
    logger.info("Checking that the forum is enable, click into the edit button")
    edit_button = await wait.not_too_much(page, c.FORUM_EDIT_ENTRY_ICON)
    await click.element(page, edit_button)
    edit_modal = await wait.not_too_much(page, c.ENABLE_FORUM_MODAL)

    logger.info("Click the enable button")
    await wait.wait_for_page_loaded(page)
    enable_button = await element.find_one(edit_modal, c.ENABLE_FORUM_BUTTON)
    await wait.wait_for_page_loaded(page)
    await click.element(page, enable_button)
    await wait.wait_for_page_loaded(page)
    save_button = await element.find_one(edit_modal, c.ENABLE_FORUM_MODAL_SAVE_BUTTON)
    await wait.wait_for_page_loaded(page)
    logger.info("Click save button")
    await click.element(page, save_button)
    await wait.not_too_much(page, c.ENABLE_FORUM_MODAL, visible=False, hidden=True)
    forum_tab_content = await course_nav.wait4_tab_content(page, c.FORUM_ICON)
    await wait.wait_for_page_loaded(page)
    logger.info("Checking that the forum es enabled")
    assert await is_forum_enabled(forum_tab_content), "The forum is not disabled"
    return page


async def disable_forum(page):
    logger.info("Checking that the forum is disabled, click into the edit button")
    edit_button = await wait.not_too_much(page, c.FORUM_EDIT_ENTRY_ICON)
    await click.element(page, edit_button)
    edit_modal = await wait.not_too_much(page, c.ENABLE_FORUM_MODAL)

    logger.info("Click into the disable button")
    disable_button = await element.find_one(edit_modal, c.DISABLE_FORUM_BUTTON)
    await click.element(page, disable_button)
    save_button = await element.find_one(edit_modal, c.ENABLE_FORUM_MODAL_SAVE_BUTTON)
    logger.info("Click into the save button")
    await click.element(page, save_button)
    await wait.not_too_much(page, c.ENABLE_FORUM_MODAL, visible=False, hidden=True)
    forum_tab_content = await course_nav.wait4_tab_content(page, c.FORUM_ICON)
    await wait.wait_for_page_loaded(page)
    logger.info("Finally checks that the Forum is enabled")
    assert not await is_forum_enabled(forum_tab_content), "The forum is not disabled"
    return page
