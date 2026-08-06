# -*- coding: utf-8 -*-
"""Generic page navigation helpers, ported from common/NavigationUtilities.java."""
import logging
from enum import Enum, auto
from typing import List, Optional

from fullteaching_e2e.common import constants as c
from fullteaching_e2e.utils import click, element, wait

logger = logging.getLogger(__name__)


class FindOption(Enum):
    CLASS = auto()
    TEXT = auto()
    VALUE = auto()
    ATTRIBUTE = auto()


def am_i_not_here(current_url: str, url: str) -> bool:
    """Mirrors NavigationUtilities.amINotHere(wd, url), comparing with trailing-slash tolerance."""
    logger.info("Checking if the browser is in the URL: %s", url)
    current_url = current_url.strip()
    compare_url = url.strip()

    if current_url.endswith("/") and not compare_url.endswith("/"):
        compare_url += "/"
    elif not current_url.endswith("/") and compare_url.endswith("/"):
        compare_url = compare_url[:-1]

    return current_url != compare_url


async def get_url(page, url: str):
    if am_i_not_here(page.url, url):
        logger.info("Navigating to: %s", url)
    await page.goto(url)


async def get_url_and_wait_footer(page, url: str):
    await get_url(page, url)
    logger.debug("Waiting for the page being loaded")
    await wait.wait_for_page_loaded(page)


async def to_courses_home(page, host: str):
    courses_url = c.COURSES_URL.replace("__HOST__", host)
    if am_i_not_here(page.url, courses_url):
        logger.debug("Waiting for the element COURSES BUTTON")
        await wait.a_little(page, c.COURSES_BUTTON, visible=False)
        logger.info("Click into the CoursesButton")
        await click.element(page, c.COURSES_BUTTON)
        await wait.not_too_much(page, c.COURSES_DASHBOARD_TITLE, visible=False)
        logger.debug("Waiting for the element COURSE_DASHBOARD_TITLE")
    else:
        logger.debug("The user was in the Course Tab")


async def get_option(page, options: List, find: str, find_type: FindOption, attribute: str) -> Optional[object]:
    """Mirrors NavigationUtilities.getOption(options, find, type, attribute)."""
    logger.info("Getting the option %s from attribute %s", find, attribute)
    for option in options:
        if find_type is FindOption.CLASS:
            if find == await element.get_attribute(page, option, "class"):
                return option
        elif find_type is FindOption.TEXT:
            if find == await element.get_text(page, option):
                return option
        elif find_type is FindOption.VALUE:
            if find == await element.get_attribute(page, option, "value"):
                return option
        else:
            if find == await element.get_attribute(page, option, attribute):
                return option
    return None
