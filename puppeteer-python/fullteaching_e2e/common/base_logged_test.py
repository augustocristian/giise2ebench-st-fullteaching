"""Login/logout/dialog helpers and the per-test user lifecycle, from ``common/BaseLoggedTest.java``.

Java models these as instance methods inherited by every test class. Here they are plain
coroutines taking the :class:`BrowserUser` they act on, plus :class:`UserFactory`, which creates
the users of a test (any number, all in the same Chrome) and tears them all down afterwards.
Puppeteer locators auto-wait, so most of Wait.java's expected conditions disappear.
"""
import logging
import re
from pathlib import Path

from fullteaching_e2e.browser import Browser, ElementTimeoutError, Locator
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.common.browser_user import BrowserUser, setup_browser
from fullteaching_e2e.common.config import AppConfig
from fullteaching_e2e.common.exceptions import NotLoggedException
from fullteaching_e2e.utils import click, wait

logger = logging.getLogger(__name__)

_SHORT_TIMEOUT_MS = 4_000


async def slow_login(user: BrowserUser, user_email: str, user_pass: str) -> str:
    """Logs in, waiting for the login button to be enabled first. Returns the user's display name."""
    logger.info("Slow login")
    return await _login(user, user_email, user_pass, slow=True)


async def quick_login(user: BrowserUser, user_email: str, user_pass: str) -> str:
    """Logs in without the explicit wait for the login button. Returns the user's display name."""
    logger.info("Quick login")
    return await _login(user, user_email, user_pass, slow=False)


async def _login(user: BrowserUser, user_email: str, user_pass: str, slow: bool) -> str:
    logger.info("Logging in user %s with mail '%s'", user.client_data, user_email)
    await user.wait_until(lambda: user.locator(c.DOWNLOAD_BUTTON, _SHORT_TIMEOUT_MS).wait_for("visible"),
                          "The button searched by CSS #download-button is not clickable")
    await open_dialog(user, c.DOWNLOAD_BUTTON)

    email_field = user.locator(c.LOGIN_USER_FIELD)
    password_field = user.locator(c.LOGIN_PASSWORD_FIELD)
    login_button = user.locator(c.LOGIN_BUTTON)
    await email_field.fill(user_email)
    await password_field.fill(user_pass)

    if slow:
        # Angular validates the form before enabling the button
        await user.wait_until(lambda: wait.poll_until(login_button.is_enabled, "login button enabled"),
                              "Login button not enabled after filling credentials")

    # Ensure fields contain what has been entered
    assert await email_field.input_value() == user_email
    assert await password_field.input_value() == user_pass
    await login_button.click()

    await user.wait_until(lambda: user.locator(c.COURSE_LIST).wait_for("visible"), "The Course list is not present")

    # Only now is there a session to log out of
    user.is_on_session = True
    user_name = await get_user_name(user, go_back=True)
    logger.info("Logging in successful for user %s", user.client_data)
    return user_name


async def logout(user: BrowserUser) -> None:
    """Logs the user out, leaving a video-session page first and using the collapsed navbar if needed."""
    logger.info("Logging out %s", user.client_data)

    if await user.locator(c.SESSION_FIXED_ICON).count() > 0:
        # Get out of video session page - the side menu must be open for the exit icon to show
        if await user.locator(c.SESSION_EXIT_ICON).count() == 0:
            await user.locator(c.SESSION_FIXED_ICON).click()
        await user.locator(c.SESSION_EXIT_ICON).wait_for("visible")
        await click.by_js(user.page, c.SESSION_EXIT_ICON)  # bypasses any overlay over the icon

    try:
        await user.locator(c.MAIN_MENU_ARROW, _SHORT_TIMEOUT_MS).click()
        await user.locator(c.LOGOUT_BUTTON).click()
    except ElementTimeoutError:
        # Shrunk menu
        await user.locator(c.MOBILE_MENU_BUTTON).click()
        await user.locator(c.MOBILE_LOGOUT_BUTTON).click()

    user.is_on_session = False
    logger.info("Logging out successful for %s", user.client_data)


async def open_dialog(user: BrowserUser, target: str | Locator) -> None:
    """Clicks ``target`` (a CSS selector or a locator) and waits for the dialog to open."""
    opener = user.locator(target) if isinstance(target, str) else target
    logger.info("User %s opening dialog by clicking %s", user.client_data, opener)
    await user.wait_until(opener.click, "Button for opening the dialog not clickable")
    await user.wait_until(lambda: user.locator(c.MODAL_OPEN).wait_for("visible"), "Dialog not opened")
    logger.info("Dialog opened for user %s", user.client_data)


async def wait_for_dialog_closed(user: BrowserUser, dialog_id: str, error_message: str) -> None:
    """Waits until the dialog with id ``dialog_id`` is closed (or gone from the DOM)."""
    logger.info("User %s waiting for dialog with id '%s' to be closed", user.client_data, dialog_id)
    await user.wait_until(lambda: user.locator(c.modal_open_selector(dialog_id)).wait_for("hidden"),
                          f"Dialog not closed. Reason: {error_message}")
    logger.info("Dialog closed for user %s", user.client_data)


async def get_user_name(user: BrowserUser, go_back: bool = True) -> str:
    """Reads the display name from the settings page, going there first if needed.

    With ``go_back`` the browser returns to the previous page afterwards.

    Raises:
        NotLoggedException: the settings button is not available, i.e. nobody is logged in.
    """
    logger.info("[INI] getUserName")
    try:
        settings_button = user.locator(c.SETTINGS_BUTTON)
        await settings_button.wait_for("visible")
        if navigation_utilities.am_i_not_here(await user.page.url(), f"{user.app_url.rstrip('/')}/settings"):
            await settings_button.click()
        else:
            go_back = False
    except ElementTimeoutError as timeout:
        raise NotLoggedException(f"[{user.client_data}] the settings button is not available: {timeout}") from timeout

    user_name = (await user.locator(c.SETTINGS_USER_NAME).text()).strip()
    if go_back:
        await navigation_utilities.go_back(user.page)
    logger.info("[END] getUserName")
    return user_name


class UserFactory:
    """Creates the :class:`BrowserUser` s of one test in a shared Chrome and tears them all down.

    Replaces the ``@BeforeEach``/``@AfterEach`` of ``BaseLoggedTest.java``: the first user it
    creates is the primary (teacher) one, and ``create`` generalises ``student`` and
    ``studentBrowserUserList`` to any number of users.
    """

    def __init__(self, browser: Browser, config: AppConfig, test_name: str) -> None:
        self._browser = browser
        self._config = config
        self._test_name = f"{config.tjob_name}-{test_name}"
        self._users: list[BrowserUser] = []

    @property
    def users(self) -> list[BrowserUser]:
        """The users created so far, in creation order."""
        return list(self._users)

    async def create(self, user_identifier: str, seconds_of_wait: int = c.WAIT_SECONDS) -> BrowserUser:
        """A new user in its own context, already on the app's home page."""
        user = await setup_browser(self._browser, self._config.app_url, self._test_name,
                                   user_identifier, seconds_of_wait)
        self._users.append(user)
        return user

    async def close_all(self, screenshots_dir: Path | None = None) -> None:
        """Logs out every user still on session and disposes all of them, even if some fail.

        Args:
            screenshots_dir: when given, a screenshot of each user is saved there first
                (use it for failed tests, before the logout navigates away).

        Raises:
            ExceptionGroup: one or more users could not be closed cleanly.
        """
        errors: list[Exception] = []
        users, self._users = self._users, []
        for user in users:
            try:
                if screenshots_dir is not None:
                    await _screenshot(user, screenshots_dir)
                if user.is_on_session:
                    await logout(user)
            except Exception as error:
                errors.append(error)
            try:
                await user.dispose()
            except Exception as error:
                errors.append(error)
        if errors:
            raise ExceptionGroup(f"{len(errors)} error(s) closing the users of {self._test_name}", errors)


async def _screenshot(user: BrowserUser, directory: Path) -> None:
    """Best-effort failure evidence (screenshot + browser console/network errors); never raises, so it
    cannot mask the original failure."""
    try:
        safe_name = re.sub(r"[^\w.-]+", "_", f"{user.test_name}-{user.client_data}")[:120]
        path = await user.page.screenshot(directory / f"{safe_name}.png")
        logger.error("Screenshot of %s saved to %s", user.client_data, path)
        for entry in await user.page.diagnostics(clear=False):
            if entry.get("kind") != "console.log":
                logger.error("[%s] browser %s: %s", user.client_data, entry.get("kind"), entry.get("text"))
    except Exception as error:
        logger.warning("[%s] could not save the failure evidence: %s", user.client_data, error)
