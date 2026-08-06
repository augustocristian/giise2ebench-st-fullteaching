# -*- coding: utf-8 -*-
"""Shared login/logout/dialog helpers, ported from the protected methods of common/BaseLoggedTest.java.

Java models these as instance methods inherited by every test class; the pytest idiom
is plain functions taking the BrowserUser (or page) they operate on, called from
tests/conftest.py fixtures and from the test modules themselves.
"""
import logging

from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.common.exceptions import NotLoggedException
from fullteaching_e2e.common.navigation_utilities import am_i_not_here
from fullteaching_e2e.utils import click, element, wait

logger = logging.getLogger(__name__)


async def slow_login(user: BrowserUser, user_email: str, user_pass: str) -> str:
    logger.info("Slow login")
    return await _login(user, user_email, user_pass, slow=True)


async def quick_login(user: BrowserUser, user_email: str, user_pass: str) -> str:
    logger.info("Quick login")
    return await _login(user, user_email, user_pass, slow=False)


async def _login(user: BrowserUser, user_email: str, user_pass: str, slow: bool) -> str:
    page = user.page
    user.is_on_session = True
    logger.info("Logging in user %s with mail '%s'", user.client_data, user_email)
    await wait.wait_for_page_loaded(page)

    await user.wait_until(lambda: wait.not_too_much(page, c.DOWNLOAD_BUTTON),
                           "The button searched by CSS #download-button is not clickable")
    await open_dialog(user, c.DOWNLOAD_BUTTON)
    await wait.wait_for_page_loaded(page)
    await user.wait_until(lambda: wait.not_too_much(page, c.LOGIN_USER_FIELD, visible=False),
                           "The email field is not present")
    user_name_field = await element.find_one(page, c.LOGIN_USER_FIELD)

    await user.wait_until(lambda: wait.not_too_much(page, c.LOGIN_PASSWORD_FIELD, visible=False),
                           "The password field is not present")
    user_pass_field = await element.find_one(page, c.LOGIN_PASSWORD_FIELD)

    await user_name_field.type(user_email)
    await user_pass_field.type(user_pass)

    if slow:
        # Wait for the login button to be clickable (Angular validates the form) rather than sleeping
        await user.wait_until(lambda: wait.not_too_much(page, c.LOGIN_BUTTON),
                               "Login button not enabled after filling credentials")

    # Ensure fields contain what has been entered
    assert await element.get_dom_property(page, user_name_field, "value") == user_email
    assert await element.get_dom_property(page, user_pass_field, "value") == user_pass
    await click.element(page, c.LOGIN_BUTTON)

    await user.wait_until(lambda: wait.not_too_much(page, c.COURSE_LIST, visible=False),
                           "The Course list is not present")
    await user.wait_until(lambda: wait.not_too_much(page, c.COURSE_LIST_ID),
                           "Course list is not clickable")

    user_name = await get_user_name(user, go_back=True)
    logger.info("Logging in successful for user %s", user.client_data)
    return user_name


async def logout(user: BrowserUser):
    page = user.page
    logger.info("Logging out %s", user.client_data)

    if await element.find_one(page, "#fixed-icon") is not None:
        # Get out of video session page - ensure side menu is open so exit-icon is visible
        try:
            await wait.a_little(page, c.SESSION_EXIT_ICON)
        except TimeoutError:
            await click.element(page, "#fixed-icon")
        await wait.not_too_much(page, c.SESSION_EXIT_ICON, visible=False)
        # JS click bypasses any overlay that would intercept a native click
        exit_icon = await element.find_one(page, c.SESSION_EXIT_ICON)
        await click.by_js(page, exit_icon)

    try:
        # Up bar menu - scroll to top so the navbar is in viewport, then use JS
        # click to bypass any overlay that would intercept a native click.
        await page.evaluate("window.scrollTo(0, 0);")
        await wait.not_too_much(page, c.MAIN_MENU_ARROW, visible=False)
        arrow = await element.find_one(page, c.MAIN_MENU_ARROW)
        await click.by_js(page, arrow)

        await wait.not_too_much(page, c.LOGOUT_BUTTON)
        await click.element(page, c.LOGOUT_BUTTON)
    except TimeoutError:
        # Shrunk menu
        await wait.not_too_much(page, "a.button-collapse")
        await click.element(page, "a.button-collapse")

        collapse_logout = "xpath=//ul[@id='nav-mobile']//a[text() = 'Logout']"
        await wait.not_too_much(page, collapse_logout)
        await click.element(page, collapse_logout)

    user.is_on_session = False
    logger.info("Logging out successful for %s", user.client_data)


async def open_dialog(user: BrowserUser, target):
    """target is a selector string or an ElementHandle, mirrors the two openDialog() overloads."""
    page = user.page
    if isinstance(target, str):
        await wait.wait_for_page_loaded(page)
        logger.info("User %s opening dialog by clicking CSS '%s'", user.client_data, target)
        await wait.wait_for_page_loaded(page)
        await user.wait_until(lambda: wait.not_too_much(page, target), "Button for opening the dialog not clickable")
        await click.element(page, target)
    else:
        logger.info("User %s opening dialog by web element", user.client_data)
        await click.element(page, target)

    await wait.wait_for_page_loaded(page)
    await user.wait_until(lambda: wait.not_too_much(page, c.MODAL_OVERLAY_OPENING), "Dialog not opened")
    logger.info("Dialog opened for user %s", user.client_data)


async def wait_for_dialog_closed(user: BrowserUser, dialog_id: str, error_message: str):
    page = user.page
    logger.info("User %s waiting for dialog with id '%s' to be closed", user.client_data, dialog_id)
    await user.wait_until(lambda: wait.not_too_much(page, c.modal_closed_xpath(dialog_id)),
                           f"Dialog not closed. Reason: {error_message}")
    await user.wait_until(lambda: wait.not_too_much(page, c.MODAL_OPEN, visible=False, hidden=True),
                           f"Dialog not closed. Reason: {error_message}")

    async def _no_overlays_left():
        overlays = await element.find_all(page, c.MODAL_OVERLAY)
        if overlays:
            raise TimeoutError("modal overlay still present")
        return True

    await wait.poll_until(_no_overlays_left)
    logger.info("Dialog closed for user %s", user.client_data)


async def get_user_name(user: BrowserUser, go_back: bool = True) -> str:
    """Mirrors BaseLoggedTest.getUserName(user, goBack, host), reading host from user.app_url."""
    logger.info("[INI]getUserName")
    page = user.page
    try:
        # pyppeteer has no separate "clickable" wait; visible is as close as it gets to
        # Java's visibilityOfElementLocated(...) + elementToBeClickable(...) pair.
        settings_button = await wait.not_too_much(page, c.SETTINGS_BUTTON)

        if am_i_not_here(page.url, f"{user.app_url}/settings"):
            await click.element(page, settings_button)
        else:
            go_back = False
    except TimeoutError as toe:
        raise NotLoggedException(str(toe))

    name_placeholder = await wait.not_too_much(page, c.USERNAME_XPATH, visible=False)
    user_name_tag = (await element.get_text(page, name_placeholder)).strip()

    if go_back:
        await page.goBack()

    logger.info("[END] getUserName")
    return user_name_tag
