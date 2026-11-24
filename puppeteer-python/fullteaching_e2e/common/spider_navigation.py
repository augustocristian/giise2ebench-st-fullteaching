"""Link crawler used by the spider tests, ported from ``common/SpiderNavigation.java``.

Traditional spider navigation (collect all links, then confirm them) does not work for this
kind of SPA, so this is a specialised depth-first spider for FullTeaching. Links are identified
by their ``href`` attribute. ``addNonExistentLink``/``discardExplored`` of the Java class are not
ported: nothing calls them.
"""
import json
import logging

from fullteaching_e2e.browser import BrowserError, Page
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common.config import load_app_config
from fullteaching_e2e.common.navigation_utilities import get_url_and_wait_footer

logger = logging.getLogger(__name__)

# Status recorded in the ``explored`` map of :func:`explore_links` for each followed link.
OK_LINK = "OK"
BROKEN_LINK = "KO"

# Links that are not visible (e.g. the collapsed navbar's) must fail fast, not after the default wait.
_CLICK_TIMEOUT_MS = 5_000

# href attribute of every anchor whose resolved URL belongs to the host and has no fragment.
_FOLLOWABLE_HREFS_JS = """(host) => [...document.querySelectorAll('a')]
    .filter((a) => a.getAttribute('href') && a.getAttribute('href').trim() !== ''
        && !a.getAttribute('href').includes('#') && a.href.includes(host))
    .map((a) => a.getAttribute('href'))"""


async def get_page_links(page: Page, host: str | None = None) -> list[str]:
    """The ``href`` of every followable anchor of the page (same host, no fragment).

    ``host`` defaults to the application URL (``SUT_URL``).
    """
    return await page.evaluate(_FOLLOWABLE_HREFS_JS, host or load_app_config().app_url)


async def get_unexplored_page_links(page: Page, explored: dict[str, str], host: str | None = None) -> list[str]:
    """The followable links of the page that are not yet keys of ``explored``."""
    return [href for href in await get_page_links(page, host) if href not in explored]


async def explore_links(page: Page, page_links: list[str], explored: dict[str, str], depth: int,
                        host: str | None = None) -> dict[str, str]:
    """Depth-first: clicks every link of ``page_links`` and recurses into the new links of each target.

    Records ``OK_LINK`` in ``explored`` when the target renders the footer and ``BROKEN_LINK`` otherwise, then
    returns to the starting page. Stops at ``depth`` 0.
    """
    if depth <= 0:
        return explored
    remaining = list(page_links)
    while remaining:
        href = remaining[0]
        current_url = await page.url()
        explore = True
        try:
            anchor = page.locator(f"a[href={json.dumps(href, ensure_ascii=False)}]", timeout_ms=_CLICK_TIMEOUT_MS).first()
            await anchor.click()
            await page.locator(c.FOOTER).wait_for("visible")
            explored[href] = OK_LINK
        except BrowserError as error:
            logger.info("Link %s is KO: %s", href, error)
            explored[href] = BROKEN_LINK
            explore = False

        if explore:
            new_links = await get_unexplored_page_links(page, explored, host)
            explored = await explore_links(page, new_links, explored, depth - 1, host)

        await get_url_and_wait_footer(page, current_url)
        remaining = await get_unexplored_page_links(page, explored, host)
    return explored


async def find_broken_links(page: Page, host: str | None = None, depth: int = c.SPIDER_DEPTH) -> list[str]:
    """Crawls every followable link reachable from the home page of ``host`` and returns the broken ones.

    ``host`` defaults to the application URL (``SUT_URL``). The crawl starts from the page's
    current session, so call it after logging in to crawl as a logged user.
    """
    start_url = host or load_app_config().app_url
    await get_url_and_wait_footer(page, start_url)
    page_links = await get_page_links(page, host)
    explored = await explore_links(page, page_links, {}, depth, host)
    return [href for href, status in explored.items() if status == BROKEN_LINK]
