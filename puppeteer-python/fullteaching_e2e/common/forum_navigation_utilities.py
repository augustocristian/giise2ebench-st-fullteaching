"""Forum navigation helpers, ported from ``common/ForumNavigationUtilities.java``."""
import logging

from fullteaching_e2e.browser import ElementTimeoutError, Locator
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.common.exceptions import ElementNotFoundException
from fullteaching_e2e.utils import element, wait

logger = logging.getLogger(__name__)


async def is_forum_enabled(forum_tab_content: Locator) -> bool:
    """Whether the forum tab shows the "new entry" icon, i.e. the forum is enabled. One-shot."""
    return await forum_tab_content.within(c.FORUM_NEW_ENTRY_ICON).count() > 0


async def _entry_rows(user: BrowserUser) -> Locator:
    tab_content = await course_nav.get_tab_content(user, c.FORUM_ICON)
    return tab_content.within(c.FORUM_ENTRY_ROW)


async def get_full_entry_list(user: BrowserUser) -> list[str]:
    """Titles of every entry of the open forum, in order."""
    await user.locator(c.FORUM_ICON).wait_for("visible")
    rows = await _entry_rows(user)
    return await element.texts(rows.within(c.FORUM_ENTRY_LIST_ENTRY_TITLE))


async def get_user_entries(user: BrowserUser, user_name: str) -> list[str]:
    """Titles of the entries whose row mentions ``user_name``."""
    rows = await _entry_rows(user)
    titles = []
    for row in await element.all_of(rows):
        if user_name in await row.text():
            titles.append((await row.within(c.FORUM_ENTRY_LIST_ENTRY_TITLE).first().text()).strip())
    return titles


async def get_entry(user: BrowserUser, entry_name: str) -> Locator:
    """The row of the entry with this exact title, waiting for a freshly posted one to be listed.

    Raises:
        ElementNotFoundException: no entry has that title.
    """
    logger.info("Getting the entry with title %s", entry_name)
    await user.locator(c.FORUM_ICON).wait_for("visible")
    rows = await _entry_rows(user)

    async def _find() -> Locator | None:
        return await element.find_row_by_child_text(rows, c.FORUM_ENTRY_LIST_ENTRY_TITLE, entry_name)

    try:
        return await wait.poll_until(_find, f"forum entry '{entry_name}' to be listed")
    except ElementTimeoutError as timeout:
        raise ElementNotFoundException(
            f"[{user.client_data}] get_entry: the entry \"{entry_name}\" doesn't exist; "
            f"the number of entries was {await rows.count()}") from timeout


async def get_comments(user: BrowserUser) -> list[Locator]:
    """Waits for the first comment, then returns every comment of the open forum entry."""
    logger.info("Getting entry comments")
    comments = user.locator(c.FORUM_COMMENT_LIST_COMMENT)
    await comments.first().wait_for("visible")
    return await element.all_of(comments)


async def get_user_comments(user: BrowserUser, user_name: str) -> list[Locator]:
    """The comments of the open entry written by ``user_name``."""
    logger.info("Getting the comments of the user: %s", user_name)
    user_comments = []
    for comment in await get_comments(user):
        author = await comment.within(c.FORUM_COMMENT_LIST_COMMENT_USER).first().text()
        if author.strip() == user_name:
            user_comments.append(comment)
    return user_comments


async def new_entry(user: BrowserUser, new_entry_title: str, new_entry_content: str) -> None:
    """Posts a new forum entry in the open course and waits until it is listed.

    Raises:
        AssertionError: the forum is not enabled.
    """
    logger.info("Creating a new entry")
    await course_nav.go2_tab(user, c.FORUM_ICON)
    tab_content = await course_nav.get_tab_content(user, c.FORUM_ICON)
    if not await is_forum_enabled(tab_content):
        raise AssertionError("Forum not activated")

    await user.locator(c.FORUM_NEW_ENTRY_ICON).click()
    await user.locator(c.FORUM_NEW_ENTRY_MODAL).wait_for("visible")
    await user.locator(c.FORUM_NEW_ENTRY_MODAL_TITLE).fill(new_entry_title)
    await user.locator(c.FORUM_NEW_ENTRY_MODAL_CONTENT).fill(new_entry_content)
    logger.info("Click the publish button")
    await user.locator(c.FORUM_NEW_ENTRY_MODAL_POST_BUTTON).click()

    await user.locator(c.FORUM_ENTRY_LIST_ENTRIES_UL).wait_for("visible")
    await get_entry(user, new_entry_title)


async def get_replies(comment: Locator) -> list[Locator]:
    """The replies nested in a comment (its first ``.comment-div`` is the comment itself)."""
    logger.info("Get all the replies of the selected comment")
    nested = await element.all_of(comment.within(c.FORUM_COMMENT_LIST_COMMENT_DIV))
    return nested[1:]


async def enable_forum(user: BrowserUser) -> None:
    """Enables the forum of the open course through its edit modal and checks it is active."""
    await _set_forum_enabled(user, c.ENABLE_FORUM_BUTTON, expect_enabled=True)


async def disable_forum(user: BrowserUser) -> None:
    """Disables the forum of the open course through its edit modal and checks it is inactive."""
    await _set_forum_enabled(user, c.DISABLE_FORUM_BUTTON, expect_enabled=False)


async def _set_forum_enabled(user: BrowserUser, toggle_selector: str, expect_enabled: bool) -> None:
    logger.info("Setting the forum %s", "enabled" if expect_enabled else "disabled")
    await user.locator(c.FORUM_EDIT_ENTRY_ICON).click()
    modal = user.locator(c.ENABLE_FORUM_MODAL)
    await modal.wait_for("visible")

    await modal.within(toggle_selector).click()
    await modal.within(c.ENABLE_FORUM_MODAL_SAVE_BUTTON).click()
    await modal.wait_for("hidden")

    # The new state arrives with the server's answer, so wait for the "new entry" icon to follow it.
    tab_content = await course_nav.wait4_tab_content(user, c.FORUM_ICON)
    try:
        await tab_content.within(c.FORUM_NEW_ENTRY_ICON).wait_for("visible" if expect_enabled else "detached")
    except ElementTimeoutError as timeout:
        raise AssertionError(f"The forum is not {'enabled' if expect_enabled else 'disabled'}") from timeout
