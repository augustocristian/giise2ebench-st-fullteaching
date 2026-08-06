"""Login/logout assertions, ported from ``common/UserUtilities.java``."""
import logging

from fullteaching_e2e.browser import ElementTimeoutError
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.common.exceptions import BadUserException, ElementNotFoundException, NotLoggedException

logger = logging.getLogger(__name__)


async def check_login(user: BrowserUser, user_email: str) -> None:
    """Opens the settings page and checks the logged-in user's e-mail is ``user_email``.

    Raises:
        NotLoggedException: there is no settings button, i.e. nobody is logged in.
        BadUserException: a different user is logged in.
    """
    try:
        await user.locator(c.SETTINGS_BUTTON).click()
    except ElementTimeoutError as timeout:
        raise NotLoggedException(f"[{user.client_data}] the settings button is not available: {timeout}") from timeout

    settings_email = (await user.locator(c.SETTINGS_USER_EMAIL).text()).strip()
    if settings_email != user_email.strip():
        raise BadUserException(
            f"Expected user '{user_email.strip()}' to be logged in but the settings page shows '{settings_email}'")


async def check_log_out(user: BrowserUser) -> None:
    """Checks the logged-out navbar (with its "Log in" link) is showing.

    Raises:
        ElementNotFoundException: the user is still logged in.
    """
    try:
        await user.locator(c.LOGIN_MENU).wait_for("visible")
    except ElementTimeoutError as timeout:
        raise ElementNotFoundException(
            f"[{user.client_data}] Not logged out, the login link is missing: {timeout}") from timeout
