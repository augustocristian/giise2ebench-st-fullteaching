# -*- coding: utf-8 -*-
"""Session navigation helpers, ported from common/SessionNavigationUtilities.java."""
import logging
from typing import List

from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common.exceptions import ElementNotFoundException
from fullteaching_e2e.utils import element

logger = logging.getLogger(__name__)


async def get_full_session_list(page) -> List[str]:
    tab_content = await course_nav.get_tab_content(page, c.SESSION_ICON)
    sessions = await element.find_all(tab_content, c.SESSION_LIST_SESSION_ROW)
    titles = []
    for session in sessions:
        name_el = await element.find_one(session, c.SESSION_LIST_SESSION_NAME)
        titles.append(await element.get_text(page, name_el))
    return titles


async def get_session(page, session_name: str):
    tab_content = await course_nav.get_tab_content(page, c.SESSION_ICON)
    sessions = await element.find_all(tab_content, c.SESSION_LIST_SESSION_ROW)
    for session in sessions:
        title = await element.find_one(session, c.SESSION_LIST_SESSION_NAME)
        if title is None:
            logger.info("Looking to the next session to check if the title match.")
            continue
        title_text = await element.get_text(page, title)
        if not title_text:
            title_text = await element.get_attribute(page, title, "innerHTML")
        if session_name == title_text:
            return session
    raise ElementNotFoundException("getSession-the session doesn't exist")
