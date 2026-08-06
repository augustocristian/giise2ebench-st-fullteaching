# -*- coding: utf-8 -*-
"""A browser + page pair for one simulated end user, ported from common/BrowserUser.java
and common/ChromeUser.java.

Puppeteer (and therefore pyppeteer) only automates Chromium, so unlike the Java suite
there is no ChromeUser/FirefoxUser/EdgeUser split - BrowserUser always launches Chromium.
"""
import logging
import os

from pyppeteer import launch

logger = logging.getLogger(__name__)

CHROME = "chrome"
FIREFOX = "firefox"
EDGE = "edge"

_CHROMIUM_ARGS = [
    "--start-maximized",
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--ignore-certificate-errors",
]

# Injected once per page so tests can probe "is a <video> actually playing" via JS,
# mirrors the GLOBAL_JS_FUNCTION literal duplicated in BaseLoggedTest.setup()/setupBrowser().
_VIDEO_PLAYING_PROBE_JS = (
    "window.MY_FUNC = function(containerQuerySelector) {"
    "var elem = document.createElement('div');"
    "elem.id = 'video-playing-div';"
    "elem.innerText = 'VIDEO PLAYING';"
    "document.body.appendChild(elem);"
    "console.log('Video check function successfully added to DOM by Puppeteer')};"
)


class BrowserUser:
    """Wraps one Chromium browser + page, mirroring common/BrowserUser.java's role."""

    def __init__(self, client_data: str, timeout_seconds: int, test_name: str):
        self.client_data = client_data
        self.timeout_ms = timeout_seconds * 1000
        self.test_name = test_name
        self.is_on_session = False
        self.browser = None
        self.page = None
        self.app_url = None

    async def _configure(self, headless: bool):
        logger.info("Starting the configuration of the Chromium browser for %s", self.client_data)
        self.browser = await launch(
            headless=headless,
            args=_CHROMIUM_ARGS,
            ignoreHTTPSErrors=True,
            executablePath=os.environ.get("PYPPETEER_EXECUTABLE_PATH"),
        )
        self.page = await self.browser.newPage()
        logger.info("Driver successfully configured for %s", self.client_data)

    async def run_javascript(self, script: str, *args):
        return await self.page.evaluate(script, *args)

    async def wait_until(self, awaitable_factory, error_message: str):
        """Awaits `awaitable_factory()`, mirrors BrowserUser.waitUntil(condition, errorMessage)."""
        try:
            return await awaitable_factory()
        except TimeoutError as timeout:
            logger.error(error_message)
            raise TimeoutError(f'"{error_message}" (checked with condition) > {timeout}') from timeout

    async def dispose(self):
        if self.browser is not None:
            await self.browser.close()


async def _resolve_browser_key(browser: str) -> str:
    if browser not in (CHROME, FIREFOX, EDGE):
        logger.warning("Unknown browser key '%s', defaulting to Chromium", browser)
    elif browser != CHROME:
        logger.warning("pyppeteer only automates Chromium; ignoring requested browser '%s'", browser)
    return CHROME


async def setup_browser(app_url: str, test_name: str, user_identifier: str, seconds_of_wait: int,
                         browser: str = CHROME, headless: bool = True) -> BrowserUser:
    """Creates a BrowserUser, navigates it to app_url and injects the video-playing probe.

    Mirrors BaseLoggedTest.setupBrowser(browser, testName, userIdentifier, secondsOfWait).
    """
    await _resolve_browser_key(browser)
    user = BrowserUser(user_identifier, seconds_of_wait, test_name)
    await user._configure(headless=headless)
    user.app_url = app_url
    logger.info("Navigating to %s", app_url)
    await user.page.goto(app_url)
    await user.run_javascript(_VIDEO_PLAYING_PROBE_JS)
    return user
