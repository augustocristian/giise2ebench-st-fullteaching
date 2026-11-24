# -*- coding: utf-8 -*-
"""Forum E2E tests, ported from functional/test/LoggedForumTest.java.

The FullTeaching UI offers no way to delete forum entries or comments, so the data created by
these tests (always inside FORUM_TEST_COURSE_NAME, with a unique timestamped title) cannot be
removed afterwards.
"""
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime

import pytest

from fullteaching_e2e.browser import BrowserError, ElementTimeoutError, Locator
from fullteaching_e2e.common import base_logged_test, navigation_utilities
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import forum_navigation_utilities as forum_nav
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils import element, wait
from fullteaching_e2e.utils.parameter_loader import get_test_users

logger = logging.getLogger(__name__)

NEW_ENTRY_TITLE = "New Entry Test"
NEW_COMMENT_TITLE = "New Comment Test"
NEW_REPLY_TITLE = "New Reply Test"
COMMENT_PREFIX = "COMMENT TEST"

# The icon sits inside the actual "back to the entries list" button.
_BACK_TO_ENTRIES_BUTTON = f"button:has({c.BACK_TO_ENTRIES_LIST_ICON})"
# Native <dialog> id of the "new entry / comment / reply" modal.
_POST_DIALOG_ID = c.FORUM_NEW_ENTRY_MODAL.removeprefix("#")

# One test case per configured user; the id keeps credentials out of the test names.
USERS = [pytest.param(mail, password, id=f"{role.lower()}-{mail}") for mail, password, role in get_test_users()]
with_each_user = pytest.mark.parametrize("mail,password", USERS)


@dataclass(frozen=True)
class LoggedInUser:
    """A browser user that has already logged in, with the display name the app shows for them."""

    user: BrowserUser
    name: str


@pytest.fixture
async def logged_in(user: BrowserUser, mail: str, password: str) -> AsyncIterator[LoggedInUser]:
    """Logs the parametrized user in; ``mail`` and ``password`` come from ``with_each_user``."""
    name = await base_logged_test.slow_login(user, mail, password)
    yield LoggedInUser(user, name)
    # The forum view may be covered by a modal: going home first keeps the logout from being flaky.
    try:
        await user.page.goto(user.app_url)
    except BrowserError as error:
        logger.warning("Could not return to the home page before logout: %s", error)


# ── Helpers ──────────────────────────────────────────────────────────────────────────────────

def _stamp() -> str:
    """Unique, sortable suffix for the titles and texts created by one test."""
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def _entry_content(stamp: str) -> str:
    return f"This is the content written by the test {stamp}"


async def _text(locator: Locator) -> str:
    """Text of the (first) element, stripped."""
    return (await locator.text()).strip()


async def _open_course(user: BrowserUser, course_name: str) -> None:
    """Opens a course of the dashboard by its title."""
    course = await course_nav.get_course_by_name(user, course_name)
    await course.within(c.COURSE_LIST_COURSE_TITLE).click()
    await user.locator(c.TABS_DIV).wait_for("visible")


async def _open_forum_tab(user: BrowserUser) -> bool:
    """Opens the Forum tab of the open course; returns whether the forum is activated."""
    await course_nav.go2_tab(user, c.FORUM_ICON)
    return await forum_nav.is_forum_enabled(await course_nav.get_tab_content(user, c.FORUM_ICON))


async def _open_forum_test_course(user: BrowserUser) -> None:
    """Opens the Forum tab of FORUM_TEST_COURSE_NAME and checks that its forum is activated."""
    await navigation_utilities.to_courses_home(user)
    await _open_course(user, c.FORUM_TEST_COURSE_NAME)
    assert await _open_forum_tab(user), "Forum not activated"


async def _open_entry(user: BrowserUser, entry_title: str) -> None:
    """Opens an entry of the forum list and waits for its comment list."""
    entry = await forum_nav.get_entry(user, entry_title)
    await entry.within(c.FORUM_ENTRY_LIST_ENTRY_TITLE).first().click()
    await user.locator(c.FORUM_COMMENT_LIST).wait_for("visible")


async def _post_from_modal(user: BrowserUser, opener: str, field: str, text: str, error_message: str) -> None:
    """Opens the post modal with ``opener``, writes ``text`` in ``field``, sends it and waits for the modal to close."""
    await base_logged_test.open_dialog(user, opener)
    await user.locator(field).fill(text)
    await user.locator(c.FORUM_NEW_COMMENT_MODAL_POST_BUTTON).click()
    await base_logged_test.wait_for_dialog_closed(user, _POST_DIALOG_ID, error_message)


async def _create_entry(user: BrowserUser, title: str, content: str) -> None:
    """Posts a new entry in the open forum and waits until it is listed and the modal is closed."""
    await forum_nav.new_entry(user, title, content)
    await base_logged_test.wait_for_dialog_closed(user, _POST_DIALOG_ID, "Addition of forum entry failed")


async def _first_entry_title(user: BrowserUser) -> str | None:
    """Title of the first entry of the open forum, or ``None`` when it has no entries."""
    entries = await forum_nav.get_full_entry_list(user)
    return entries[0] if entries else None


async def _open_first_entry_or_create(user: BrowserUser, title_prefix: str) -> None:
    """Opens the first entry of the open forum, creating one first when the forum is empty."""
    title = await _first_entry_title(user)
    if title is None:
        stamp = _stamp()
        title = f"{title_prefix} {stamp}"
        await _create_entry(user, title, _entry_content(stamp))
    await _open_entry(user, title)


async def _find_comment(user: BrowserUser, content: str) -> Locator:
    """Waits for the top-level comment whose own message is ``content`` and returns it."""
    comments = user.locator(c.FORUM_COMMENT_LIST_COMMENT)
    return await wait.poll_until(
        lambda: element.find_row_by_child_text(comments, c.FORUM_COMMENT_LIST_COMMENT_CONTENT, content),
        f"comment '{content}' to be listed")


async def _find_reply(comment: Locator, content: str) -> Locator:
    """Waits for the reply of ``comment`` whose message is ``content`` and returns it."""
    async def _reply() -> Locator | None:
        for reply in await forum_nav.get_replies(comment):
            if await _text(reply.within(c.FORUM_COMMENT_LIST_COMMENT_CONTENT).first()) == content:
                return reply
        return None

    return await wait.poll_until(_reply, f"reply '{content}' to be listed")


async def _browse_entry(user: BrowserUser, entry_title: str) -> bool:
    """Opens an entry, checks that all its comments have an author, and returns whether it has any."""
    await _open_entry(user, entry_title)
    try:
        comments = await forum_nav.get_comments(user)
    except ElementTimeoutError:
        comments = []  # an entry without comments: nothing to check
    for index, comment in enumerate(comments, start=1):
        author = await _text(comment.within(c.FORUM_COMMENT_LIST_COMMENT_USER).first())
        assert author, f"Comment #{index} of the entry '{entry_title}' has no author"
    await user.locator(_BACK_TO_ENTRIES_BUTTON).click()
    return bool(comments)


# ── Tests ────────────────────────────────────────────────────────────────────────────────────

@with_each_user
async def test_forum_load_entries(logged_in: LoggedInUser) -> None:
    """Every enabled course forum can be browsed entry by entry, and at least one entry has comments.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READONLY,10)
    executor/webbrowser/webserver(READWRITE,1).
    """
    # Arrange: the dashboard lists at least one course
    user = logged_in.user
    courses = await course_nav.get_courses_list(user)
    assert courses, "No courses in the list"

    # Act: browse every entry of every course whose forum is activated
    forum_enabled_somewhere = False
    some_entry_has_comments = False
    for course_name in courses:
        await _open_course(user, course_name)
        if await _open_forum_tab(user):
            forum_enabled_somewhere = True
            for entry_title in await forum_nav.get_full_entry_list(user):
                some_entry_has_comments |= await _browse_entry(user, entry_title)
        await user.locator(c.BACK_TO_DASHBOARD).click()

    # Assert
    assert forum_enabled_somewhere and some_entry_has_comments, (
        "There isn't any forum that can be used to test this "
        "[Or not activated or no entry lists or not comments]")


@with_each_user
async def test_forum_new_entry(logged_in: LoggedInUser) -> None:
    """A new forum entry is listed with its author and opens with its title and first comment.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    # Arrange
    user = logged_in.user
    stamp = _stamp()
    entry_title = f"{NEW_ENTRY_TITLE} {stamp}"
    entry_content = _entry_content(stamp)
    await _open_forum_test_course(user)

    # Act
    await _create_entry(user, entry_title, entry_content)

    # Assert: the list shows the entry with its author
    entry = await forum_nav.get_entry(user, entry_title)
    list_author = await _text(entry.within(c.FORUM_ENTRY_LIST_ENTRY_USER).first())
    assert list_author == logged_in.name, "Incorrect user for the entry in the list"

    # Assert: the entry view shows its title and author, and the entry text as first comment
    await _open_entry(user, entry_title)
    header = await _text(user.locator(c.FORUM_COMMENT_LIST_ENTRY_TITLE))
    assert header.startswith(entry_title), f"Incorrect entry title: '{header}'"
    header_author = await _text(user.locator(c.FORUM_COMMENT_LIST_ENTRY_USER))
    assert header_author == logged_in.name, "Incorrect user for the entry"

    first_comment = (await forum_nav.get_comments(user))[0]
    content = await _text(first_comment.within(c.FORUM_COMMENT_LIST_COMMENT_CONTENT).first())
    assert content == entry_content, "Bad content of comment"
    comment_author = await _text(first_comment.within(c.FORUM_COMMENT_LIST_COMMENT_USER).first())
    assert comment_author == logged_in.name, "Bad user in comment"


@with_each_user
async def test_forum_new_comment(logged_in: LoggedInUser) -> None:
    """A comment posted on a forum entry is appended to the entry with the right author.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    # Arrange: open the first entry of the forum (creating one if it is empty)
    user = logged_in.user
    await _open_forum_test_course(user)
    await _open_first_entry_or_create(user, NEW_COMMENT_TITLE)
    comments_before = len(await forum_nav.get_comments(user))

    # Act
    comment_content = f"{COMMENT_PREFIX}{_stamp()}. This is the comment written by the test"
    await _post_from_modal(user, c.FORUM_COMMENT_LIST_NEW_COMMENT_ICON, c.FORUM_NEW_COMMENT_MODAL_TEXT_FIELD,
                           comment_content, "Addition of comment failed")

    # Assert
    posted_comment = await _find_comment(user, comment_content)
    assert await user.locator(c.FORUM_COMMENT_LIST_COMMENT).count() > comments_before, \
        "Comment list empty or only original comment"
    author = await _text(posted_comment.within(c.FORUM_COMMENT_LIST_COMMENT_USER).first())
    assert author == logged_in.name, "Bad user in comment"


@with_each_user
async def test_forum_new_reply_to_comment(logged_in: LoggedInUser) -> None:
    """A reply posted on the first comment of an entry is nested under it with the right author.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) forum(READWRITE,1,exclusive)
    executor/webbrowser/webserver(READWRITE,1).
    """
    # Arrange: open the first entry of the forum (creating one if it is empty)
    user = logged_in.user
    await _open_forum_test_course(user)
    await _open_first_entry_or_create(user, NEW_REPLY_TITLE)
    first_comment = (await forum_nav.get_comments(user))[0]

    # Act: reply to the first comment (the reply icon selector is that of the text reply)
    reply_content = f"This is the reply written by the test {_stamp()}"
    await _post_from_modal(user, c.FORUM_COMMENT_LIST_COMMENT_REPLY_ICON,
                           c.FORUM_COMMENT_LIST_MODAL_NEW_REPLY_TEXT_FIELD, reply_content,
                           "Addition of reply failed")

    # Assert: the reply is nested in the comment and written by the user
    reply = await _find_reply(first_comment, reply_content)
    author = await _text(reply.within(c.FORUM_COMMENT_LIST_COMMENT_USER).first())
    assert author == logged_in.name, "Bad user in reply"
