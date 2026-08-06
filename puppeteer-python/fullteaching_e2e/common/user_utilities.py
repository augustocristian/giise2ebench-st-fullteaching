# -*- coding: utf-8 -*-
"""Login/logout assertions, ported from common/UserUtilities.java."""
import logging

from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common.exceptions import BadUserException, ElementNotFoundException, NotLoggedException
from fullteaching_e2e.utils import click, element, wait

logger = logging.getLogger(__name__)


async def check_login(page, user_email: str):
    logger.info("[INI]checkLogin")
    try:
        settings_button = await wait.not_too_much(page, c.SETTINGS_BUTTON)
        await click.element(page, settings_button)
    except TimeoutError as toe:
        raise NotLoggedException(str(toe))

    settings_page = await wait.not_too_much(page, c.SETTINGS_USER_EMAIL)
    settings_text = await element.get_text(page, settings_page)
    if settings_text.strip() != user_email.strip():
        raise BadUserException()
    logger.info("[END]checkLogin")
    return page


async def check_log_out(page):
    logger.info("[INI]checkLogOut")
    try:
        await wait.not_too_much(page, c.LOGIN_MENU)
    except TimeoutError as toe:
        raise ElementNotFoundException(f"Not Logged Out. Not in the home: {toe}")
    logger.info("[END]checkLogOut")
