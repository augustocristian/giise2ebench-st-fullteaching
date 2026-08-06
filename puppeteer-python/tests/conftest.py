# -*- coding: utf-8 -*-
"""pytest fixtures, ported from the @BeforeAll/@BeforeEach/@AfterEach lifecycle of
common/BaseLoggedTest.java.

Java models one long-lived test class holding shared driver/user state; pytest's idiom
is fixtures. `app_config` mirrors BaseLoggedTest.setupAll() (env var resolution done once
per session), `user` mirrors the per-test primary BrowserUser created in setup()/torn down
in tearDown(), and `browser_factory` generalizes setupBrowser() (used for the `student`
BrowserUser and studentBrowserUserList) into a factory so any test can spin up as many
extra simulated users as it needs, all auto-disposed at teardown.
"""
import logging
import os
from dataclasses import dataclass

import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common.browser_user import CHROME, setup_browser
from fullteaching_e2e.common.constants import LOCALHOST, WAIT_SECONDS

logger = logging.getLogger(__name__)


def pytest_runtest_setup(item):
    logger.info("##### Start test: %s", item.name)


def pytest_runtest_teardown(item):
    logger.info("##### Finish test: %s", item.name)


@dataclass(frozen=True)
class AppConfig:
    app_url: str
    tjob_name: str
    teacher_browser: str
    student_browser: str


@pytest.fixture(scope="session")
def app_config() -> AppConfig:
    """Mirrors BaseLoggedTest.setupAll()'s SUT_URL/tjob_name/{TEACHER,STUDENT}_BROWSER resolution."""
    env_url = os.environ.get("SUT_URL")
    env_tjob_name = os.environ.get("tjob_name")
    if env_url:
        app_url = env_url
        tjob_name = env_tjob_name or "TJobDef"
    else:
        app_url = os.environ.get("app.url", LOCALHOST)
        tjob_name = "TJobDef"
    logger.info("Using URL %s TJOB: %s", app_url, tjob_name)

    def _browser(env_var: str) -> str:
        value = os.environ.get(env_var)
        return value if value else CHROME

    return AppConfig(
        app_url=app_url,
        tjob_name=tjob_name,
        teacher_browser=_browser("TEACHER_BROWSER"),
        student_browser=_browser("STUDENT_BROWSER"),
    )


@pytest.fixture
async def browser_factory(request, app_config: AppConfig):
    """Yields a factory for extra BrowserUsers; every user it creates is auto-disposed
    (logging out first if still on-session), mirroring BaseLoggedTest.tearDown()'s handling
    of `student` and `studentBrowserUserList`.
    """
    created = []

    async def _create(user_identifier: str, browser: str = None, seconds_of_wait: int = WAIT_SECONDS):
        test_name = f"{app_config.tjob_name}-{request.node.name}"
        u = await setup_browser(app_config.app_url, test_name, user_identifier, seconds_of_wait,
                                 browser=browser or app_config.student_browser)
        created.append(u)
        return u

    yield _create

    for u in created:
        logger.info("##### Finish test: %s - Driver %s", request.node.name, u.client_data)
        if u.is_on_session:
            await base_logged_test.logout(u)
        await u.dispose()


@pytest.fixture
async def user(request, app_config: AppConfig):
    """The primary (teacher-slot) BrowserUser, mirrors BaseLoggedTest.user + setup()/tearDown()."""
    test_name = f"{app_config.tjob_name}-{request.node.name}"
    u = await setup_browser(app_config.app_url, test_name, request.node.name, WAIT_SECONDS,
                             browser=app_config.teacher_browser)
    yield u

    logger.info("##### Finish test: %s - Driver %s", request.node.name, u.client_data)
    if u.is_on_session:
        await base_logged_test.logout(u)
    await u.dispose()
