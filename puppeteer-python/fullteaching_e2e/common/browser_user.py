"""One simulated end user: an isolated browser context plus its page.

Ported from ``common/BrowserUser.java`` and ``ChromeUser.java``. Selenium needs one driver
process per user; here every user is a context (own cookies and storage) of ONE shared Chrome,
which is what lets a test drive a teacher and several students at the same time. Puppeteer only
automates Chromium, so there is no per-browser user class.
"""
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from fullteaching_e2e.browser import Browser, BrowserContext, ElementTimeoutError, Locator, Page
from fullteaching_e2e.common import config
from fullteaching_e2e.common.constants import WAIT_SECONDS

logger = logging.getLogger(__name__)

# Fake camera/microphone without permission prompts (video sessions) and the SUT's self-signed certificate.
CHROMIUM_ARGS = (
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--ignore-certificate-errors",
)

# Lets tests probe "is a <video> actually playing" through JS (``window.MY_FUNC``), like the Java suite.
_VIDEO_PLAYING_PROBE_JS = """() => {
    window.MY_FUNC = function (containerQuerySelector) {
        const elem = document.createElement('div');
        elem.id = 'video-playing-div';
        elem.innerText = 'VIDEO PLAYING';
        document.body.appendChild(elem);
        console.log('Video check function successfully added to DOM by Puppeteer');
    };
}"""


async def launch_browser() -> Browser:
    """Starts the shared Chrome (headless unless ``HEADED``), with the flags the suite needs."""
    return await Browser.launch(
        headless=not config.is_headed(),
        executable_path=config.browser_executable_path(),
        args=[*CHROMIUM_ARGS, *config.browser_args()],
    )


@dataclass
class BrowserUser:
    """A simulated user: ``client_data`` names it in logs (TEACHER, STUDENT...)."""

    client_data: str
    browser: Browser
    context: BrowserContext
    page: Page
    app_url: str
    timeout_ms: int
    test_name: str
    is_on_session: bool = False
    _disposed: bool = field(default=False, init=False, repr=False)

    def locator(self, selector: str, timeout_ms: int | None = None) -> Locator:
        """Lazy CSS locator on this user's page, auto-waiting up to the user's timeout by default."""
        return self.page.locator(selector, timeout_ms=timeout_ms or self.timeout_ms)

    async def run_javascript(self, script: str, *args: Any) -> Any:
        """Evaluates a JS function expression (``"(a) => a + 1"``) in this user's page."""
        return await self.page.evaluate(script, *args)

    async def wait_until[T](self, action: Callable[[], Awaitable[T]], error_message: str) -> T:
        """Awaits ``action()``; a timeout is re-raised naming this user and ``error_message``."""
        try:
            return await action()
        except ElementTimeoutError as timeout:
            logger.error("[%s] %s", self.client_data, error_message)
            raise ElementTimeoutError(
                f'[{self.client_data}] "{error_message}" (checked with condition) > {timeout}') from timeout

    async def dispose(self) -> None:
        """Closes the page and its context. Idempotent."""
        if self._disposed:
            return
        self._disposed = True
        try:
            await self.page.close()
        finally:
            await self.context.close()


async def setup_browser(browser: Browser, app_url: str, test_name: str, user_identifier: str,
                        seconds_of_wait: int = WAIT_SECONDS) -> BrowserUser:
    """Creates a user in a fresh context of ``browser``, opens ``app_url`` and injects the video probe.

    Mirrors ``BaseLoggedTest.setupBrowser(browser, testName, userIdentifier, secondsOfWait)``.
    """
    logger.info("Starting the configuration of the browser context for %s", user_identifier)
    context = await browser.new_context()
    try:
        page = await context.new_page()
        user = BrowserUser(user_identifier, browser, context, page, app_url, seconds_of_wait * 1000, test_name)
        logger.info("Navigating to %s", app_url)
        await page.goto(app_url)
        await page.evaluate(_VIDEO_PLAYING_PROBE_JS)
    except BaseException:
        await context.close()  # do not leak the context when the app is unreachable
        raise
    return user
