# -*- coding: utf-8 -*-
"""pytest fixtures, ported from the @BeforeAll/@BeforeEach/@AfterEach lifecycle of
common/BaseLoggedTest.java.

Java models one long-lived test class holding shared driver/user state; pytest's idiom
is fixtures. `app_config` mirrors BaseLoggedTest.setupAll() (env var resolution done once
per session), `user` mirrors the per-test primary BrowserUser created in setup()/torn down
in tearDown(), and `browser_factory` generalizes setupBrowser() (used for the `student`
BrowserUser and studentBrowserUserList) into a factory so any test can spin up as many
extra simulated users as it needs, all auto-disposed at teardown.

The browser layer is `fullteaching_e2e.browser` (a Python client of a Node bridge running the
current Puppeteer). `browser` is one Chrome shared by the whole session and `page` gives a
test its own isolated page (own cookies, storage and camera/microphone permission). Several
`page`s, or `browser.new_page(...)` calls, can be open at once for the teacher and students
of a video session.

Environment variables: SUT_URL, tjob_name, TEACHER_BROWSER, STUDENT_BROWSER (as in
selenium-java), HEADED=1 to show Chrome, PUPPETEER_EXECUTABLE_PATH, BROWSER_ARGS (extra Chrome
flags, space separated); see fullteaching_e2e/common/config.py.
"""
import logging
import re
from pathlib import Path

import pytest
import pytest_asyncio

from fullteaching_e2e.browser import Browser, Page
from fullteaching_e2e.common.base_logged_test import UserFactory
from fullteaching_e2e.common.browser_user import launch_browser
from fullteaching_e2e.common.config import AppConfig, load_app_config

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "reports" / "screenshots"

# Test file name fragment -> area marker declared in pyproject.toml.
_AREA_MARKERS = {
    "echat": "echat",
    "video_session": "video",
    "forum": "forum",
    "course": "course",
    "links": "links",
    "rest": "rest",
    "test_user": "user",
}


def pytest_runtest_setup(item):
    logger.info("##### Start test: %s", item.name)


def pytest_runtest_teardown(item):
    logger.info("##### Finish test: %s", item.name)


def pytest_collection_modifyitems(items):
    """Tags tests with `bridge` (tests/bridge) or `e2e` (everything else) plus an area marker
    from the file name, so `pytest -m e2e`, `-m bridge`, `-m video`... work without decorating."""
    for item in items:
        path = Path(str(item.fspath))
        if path.parent.name == "bridge":
            item.add_marker("bridge")
            continue
        item.add_marker("e2e")
        for fragment, marker in _AREA_MARKERS.items():
            if fragment in path.name:
                item.add_marker(marker)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    # Exposes each phase's report so fixtures can react to a failed test.
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report


@pytest.fixture(scope="session")
def app_config() -> AppConfig:
    """Mirrors BaseLoggedTest.setupAll()'s SUT_URL/tjob_name/{TEACHER,STUDENT}_BROWSER resolution."""
    config = load_app_config()
    logger.info("Using URL %s TJOB: %s", config.app_url, config.tjob_name)
    return config


@pytest.fixture(scope="session")
def sut_url(app_config: AppConfig) -> str:
    """Base URL of the FullTeaching SUT (SUT_URL, default https://localhost:5000)."""
    return app_config.app_url


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def browser():
    """One Chrome (fake camera and microphone, certificate errors ignored) for the whole session."""
    instance = await launch_browser()
    yield instance
    await instance.close()


@pytest_asyncio.fixture(loop_scope="session")
async def page(request, browser: Browser, app_config: AppConfig):
    """A page in its own isolated context, with camera and microphone granted for the SUT origin."""
    current: Page = await browser.new_page(media_origin=app_config.app_url)
    yield current
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        await _save_failure_artifacts(request.node.name, current)
    await current.close()


async def _save_failure_artifacts(test_name: str, current: Page) -> None:
    safe_name = re.sub(r"[^\w.-]+", "_", test_name)
    try:
        path = await current.screenshot(SCREENSHOT_DIR / f"{safe_name}.png")
        logger.error("Screenshot of the failed test saved to %s", path)
        for entry in await current.diagnostics():
            logger.error("Browser diagnostic: %s", entry)
    except Exception as error:  # diagnostics must never mask the real failure
        logger.warning("Could not capture failure artifacts: %s", error)


@pytest_asyncio.fixture(loop_scope="session")
async def user_factory(request, browser: Browser, app_config: AppConfig):
    """Per-test user lifecycle: every user created through it is logged out (if still on a session)
    and disposed at teardown, with a screenshot first when the test failed. Mirrors
    BaseLoggedTest.setup()/tearDown()."""
    factory = UserFactory(browser, app_config, request.node.name)
    yield factory
    report = getattr(request.node, "rep_call", None)
    failed = report is not None and report.failed
    await factory.close_all(SCREENSHOT_DIR if failed else None)


@pytest_asyncio.fixture(loop_scope="session")
async def user(request, user_factory: UserFactory):
    """The primary (teacher-slot) BrowserUser."""
    return await user_factory.create(request.node.name)


@pytest_asyncio.fixture(loop_scope="session")
async def browser_factory(user_factory: UserFactory):
    """The factory for extra users: ``await browser_factory("STUDENT", seconds_of_wait)``."""
    return user_factory.create
