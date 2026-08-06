# -*- coding: utf-8 -*-
"""Link crawler used by the spider tests, ported from common/SpiderNavigation.java.

Note: traditional spider navigation retrieving all links and then confirming them
doesn't work properly for this kind of SPA. This is a specialized spider for FullTeaching.

`addNonExistentLink`/`discardExplored` from the Java class are not ported: neither is
called from any test, in Java or here.
"""
import logging
import os
from typing import Dict, List

from fullteaching_e2e.common.constants import LOCALHOST
from fullteaching_e2e.common.navigation_utilities import get_url_and_wait_footer
from fullteaching_e2e.utils import element, wait

logger = logging.getLogger(__name__)


def _host() -> str:
    # Mirrors System.getProperty("fullTeachingUrl"): an override that nothing in this
    # suite actually sets, so this is normally just LOCALHOST regardless of APP_URL/SUT_URL.
    return os.environ.get("fullTeachingUrl", LOCALHOST)


def _is_followable(href) -> bool:
    return bool(href) and href.strip() != "" and "#" not in href


async def get_page_links(page) -> List:
    """Mirrors SpiderNavigation.getPageLinks(wd)."""
    host = _host()
    anchors = await element.find_all(page, "a")
    links = []
    for a in anchors:
        href = await element.get_attribute(page, a, "href")
        if _is_followable(href) and host in href:
            links.append(a)
    return links


async def get_unexplored_page_links(page, explored: Dict[str, str]) -> List:
    """Mirrors SpiderNavigation.getUnexploredPageLinks(wd, explored)."""
    host = _host()
    links = []
    for a in await get_page_links(page):
        href = await element.get_attribute(page, a, "href")
        if _is_followable(href) and href.strip() not in explored and host in href:
            links.append(a)
    return links


async def explore_links(page, page_links: List, explored: Dict[str, str], depth: int) -> Dict[str, str]:
    """Recursively follows page_links up to `depth` levels, mirrors SpiderNavigation.exploreLinks."""
    if depth <= 0:
        return explored
    while page_links:
        link = page_links[0]
        href = await element.get_attribute(page, link, "href")
        current_url = page.url
        explore = True
        try:
            await link.click()
            await wait.footer(page)
            explored[href] = "OK"
        except Exception:
            explored[href] = "KO"
            explore = False

        if explore:
            new_links = await get_unexplored_page_links(page, explored)
            explored = await explore_links(page, new_links, explored, depth - 1)

        await get_url_and_wait_footer(page, current_url)
        page_links = await get_unexplored_page_links(page, explored)
    return explored
