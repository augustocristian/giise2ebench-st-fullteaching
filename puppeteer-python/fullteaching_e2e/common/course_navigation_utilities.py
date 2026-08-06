"""Course and tab navigation helpers, ported from ``common/CourseNavigationUtilities.java``.

Everything takes the :class:`BrowserUser` it acts on. Elements are returned as lazy
:class:`Locator` s (never handles): they re-resolve on every action and auto-wait, so none of
Click.java's scroll/retry/JS-click fallbacks is needed.
"""
import logging

from fullteaching_e2e.browser import ElementTimeoutError, Locator
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.common.exceptions import ElementNotFoundException
from fullteaching_e2e.utils import element, wait

logger = logging.getLogger(__name__)


def _course_items(user: BrowserUser) -> Locator:
    return user.locator(c.COURSE_LIST_ITEM)


async def _course_titles(user: BrowserUser) -> list[str]:
    return await element.texts(_course_items(user).within(c.COURSE_TITLE))


async def new_course(user: BrowserUser, course_name: str) -> str:
    """Creates a course through the "new course" modal and waits for it to show up in the dashboard."""
    await navigation_utilities.to_courses_home(user)
    await user.locator(c.COURSE_LIST).wait_for("visible")

    await user.locator(c.NEW_COURSE_ICON).click()
    await user.locator(c.NEW_COURSE_MODAL).wait_for("visible")
    logger.debug("Introducing Course Name: %s", course_name)
    await user.locator(c.NEW_COURSE_MODAL_NAME_FIELD).fill(course_name)
    await user.locator(c.NEW_COURSE_MODAL_SAVE).click()

    await assert_course_exists(user, course_name)
    return course_name


async def check_if_course_exists(user: BrowserUser, course_title: str) -> bool:
    """One-shot check: is a course with exactly this title listed right now?"""
    return course_title in await _course_titles(user)


async def check_if_course_exists_with_retries(user: BrowserUser, course_title: str, retries: int) -> bool:
    """Like :func:`check_if_course_exists`, retrying for about one second per retry."""
    try:
        await wait.poll_until(lambda: check_if_course_exists(user, course_title),
                              f"course '{course_title}' to be listed", timeout_s=retries)
    except ElementTimeoutError:
        return False
    return True


async def assert_course_exists(user: BrowserUser, course_title: str, timeout_s: float = wait.DEFAULT_TIMEOUT_S) -> None:
    """Waits until a course with exactly this title is listed.

    Raises:
        ElementTimeoutError: it did not show up within ``timeout_s``.
    """
    await wait.poll_until(lambda: check_if_course_exists(user, course_title),
                          f"course '{course_title}' to be listed", timeout_s)


async def assert_course_not_exists(user: BrowserUser, course_title: str, timeout_s: float = wait.DEFAULT_TIMEOUT_S) -> None:
    """Waits until no course with exactly this title is listed.

    Raises:
        ElementTimeoutError: it was still listed after ``timeout_s``.
    """
    async def _gone() -> bool:
        return not await check_if_course_exists(user, course_title)

    await wait.poll_until(_gone, f"course '{course_title}' to disappear", timeout_s)


async def _open_edit_course_modal(user: BrowserUser, course_title: str) -> None:
    course = await get_course_by_name(user, course_title)
    await course.within(c.EDIT_COURSE_BUTTON).click()
    await user.locator(c.EDIT_DELETE_MODAL).wait_for("visible")


async def change_course_name(user: BrowserUser, old_name: str, new_name: str) -> None:
    """Renames a course through its edit modal.

    Raises:
        ElementNotFoundException: there is no course called ``old_name``.
    """
    logger.info("[INI] changeCourseName(%s=>%s)", old_name, new_name)
    await user.locator(c.COURSE_LIST).wait_for("visible")
    await _open_edit_course_modal(user, old_name)

    await user.locator(c.EDIT_COURSE_MODAL_NAME_FIELD).fill(new_name)
    await user.locator(c.EDIT_COURSE_MODAL_SAVE).click()
    await user.locator(c.EDIT_DELETE_MODAL).wait_for("hidden")
    logger.info("[END] changeCourseName OK")


async def delete_course(user: BrowserUser, course_name: str) -> None:
    """Deletes a course through its edit modal and waits for the dashboard to shrink by one.

    Raises:
        ElementNotFoundException: there is no course called ``course_name``.
    """
    logger.info("[INI] deleteCourse(%s)", course_name)
    await navigation_utilities.to_courses_home(user)
    await user.locator(c.COURSE_LIST).wait_for("visible")
    initial_count = await _course_items(user).count()

    await _open_edit_course_modal(user, course_name)
    await user.locator(c.EDIT_COURSE_DELETE_CHECK).click()
    await user.locator(c.EDIT_COURSE_DELETE_BUTTON).click()
    await user.locator(c.EDIT_COURSE_MODAL_SAVE).click()

    # The row that was last before the deletion is gone once the list has one course less.
    await _course_items(user).nth(initial_count - 1).wait_for("detached")
    logger.info("[END] deleteCourse OK: Course \"%s\"", course_name)


async def get_courses_list(user: BrowserUser) -> list[str]:
    """Titles of the courses of the dashboard, in order."""
    await navigation_utilities.to_courses_home(user)
    await user.locator(c.COURSE_LIST).wait_for("visible")
    return await _course_titles(user)


async def get_course_by_name(user: BrowserUser, name: str) -> Locator:
    """The dashboard row of the course with this exact title.

    Raises:
        ElementNotFoundException: no course has that title.
    """
    await user.locator(c.COURSE_LIST).wait_for("visible")
    items = _course_items(user)
    course = await element.find_row_by_child_text(items, c.COURSE_TITLE, name)
    if course is None:
        raise ElementNotFoundException(
            f"[{user.client_data}] get_course_by_name: the course \"{name}\" doesn't exist; "
            f"listed courses: {await _course_titles(user)}")
    return course


def get_tab_element_from_icon(user: BrowserUser, icon_selector: str) -> Locator:
    """The tab (``li.tab``) of a course tab, identified by the selector of its icon."""
    return user.locator(f"{c.COURSE_TABS} li.tab:has({icon_selector})")


async def get_tab_id(user: BrowserUser, icon_selector: str) -> str:
    """The id of a tab, e.g. ``md-tab-label-0-2``."""
    tab_id = await get_tab_element_from_icon(user, icon_selector).attribute("id")
    if tab_id is None:
        raise ElementNotFoundException(f"[{user.client_data}] the tab of icon '{icon_selector}' has no id")
    return tab_id


async def get_tab_content(user: BrowserUser, icon_selector: str) -> Locator:
    """The content container of a tab (its id is the tab's with ``label`` replaced by ``content``).

    Only the active tab has content in the DOM, so this is meaningful after :func:`go2_tab`.
    """
    tab_id = await get_tab_id(user, icon_selector)
    return user.locator("#" + tab_id.replace("label", "content"))


async def wait4_tab_content(user: BrowserUser, icon_selector: str) -> Locator:
    """Like :func:`get_tab_content`, but waits for the content to be visible first."""
    content = await get_tab_content(user, icon_selector)
    await content.wait_for("visible")
    return content


async def go2_tab(user: BrowserUser, icon_selector: str) -> None:
    """Clicks a course tab and waits for its content to render."""
    tab = get_tab_element_from_icon(user, icon_selector)
    logger.info("Navigating to tab with id: %s", await get_tab_id(user, icon_selector))
    await tab.click()
    await wait4_tab_content(user, icon_selector)


async def is_user_in_attenders_list(user: BrowserUser, user_name: str) -> bool:
    """Whether ``user_name`` (case-insensitive, trimmed) is a row of the open attenders tab.

    Raises:
        ElementNotFoundException: the attenders list is empty.
    """
    content = await get_tab_content(user, c.ATTENDERS_ICON)
    rows = content.within(c.ATTENDERS_LIST_ROWS)
    await rows.first().wait_for("visible")
    names = await element.texts(rows)
    if not names:
        raise ElementNotFoundException(f"[{user.client_data}] is_user_in_attenders_list: attenders list is empty")
    return user_name.strip().casefold() in (name.casefold() for name in names)


async def get_highlighted_attender(user: BrowserUser) -> str:
    """The name highlighted in the attenders tab (the user currently speaking).

    Raises:
        ElementNotFoundException: no attender is highlighted.
    """
    content = await get_tab_content(user, c.ATTENDERS_ICON)
    highlighted = content.within(c.ATTENDERS_LIST_HIGHLIGHTED_ROW)
    if await highlighted.count() == 0:
        raise ElementNotFoundException(f"[{user.client_data}] get_highlighted_attender: no highlighted user")
    return (await highlighted.first().text()).strip()
