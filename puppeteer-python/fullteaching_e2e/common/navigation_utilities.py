"""Generic page navigation helpers, ported from ``common/NavigationUtilities.java``."""
import logging
from enum import Enum, auto

from fullteaching_e2e.browser import Locator, Page
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils import wait

logger = logging.getLogger(__name__)


class FindOption(Enum):
    """Which property of an element :func:`get_option` compares."""

    CLASS = auto()
    TEXT = auto()
    VALUE = auto()
    ATTRIBUTE = auto()


def am_i_not_here(current_url: str, url: str) -> bool:
    """Whether ``current_url`` differs from ``url``, tolerating a trailing slash."""
    current_url = current_url.strip()
    compare_url = url.strip()
    if current_url.endswith("/") and not compare_url.endswith("/"):
        compare_url += "/"
    elif not current_url.endswith("/") and compare_url.endswith("/"):
        compare_url = compare_url[:-1]
    return current_url != compare_url


async def get_url_and_wait_footer(page: Page, url: str) -> None:
    """Navigates to ``url`` and waits for the page footer to be visible."""
    await page.goto(url)
    await page.locator(c.FOOTER).wait_for("visible")


async def go_back(page: Page) -> None:
    """Browser "back" (the bridge has no history API), returning once the URL has changed."""
    before = await page.url()
    await page.evaluate("() => history.back()")

    async def _url_changed() -> bool:
        return await page.url() != before

    await wait.poll_until(_url_changed, f"navigation back from {before}")


async def to_courses_home(user: BrowserUser) -> None:
    """Goes to the courses dashboard through the navbar, unless the user is already there."""
    courses_url = user.app_url.rstrip("/") + c.COURSES_PATH
    if am_i_not_here(await user.page.url(), courses_url):
        await user.locator(c.COURSES_BUTTON).click()
        await user.locator(c.COURSES_DASHBOARD_TITLE).wait_for("visible")


async def get_option(options: list[Locator], find: str, find_type: FindOption, attribute: str = "") -> Locator | None:
    """The first option whose class, text, value or ``attribute`` equals ``find``, or ``None``."""
    logger.info("Getting the option %s (%s)", find, find_type.name)
    for option in options:
        match find_type:
            case FindOption.CLASS:
                candidate = await option.attribute("class")
            case FindOption.TEXT:
                candidate = (await option.text()).strip()
            case FindOption.VALUE:
                candidate = await option.attribute("value")
            case FindOption.ATTRIBUTE:
                candidate = await option.attribute(attribute)
        if candidate == find:
            return option
    return None
