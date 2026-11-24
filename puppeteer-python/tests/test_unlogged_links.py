# -*- coding: utf-8 -*-
"""Spider test without a session, ported from functional/test/UnLoggedLinksTests.java."""
import pytest

from fullteaching_e2e.common import spider_navigation
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils.parameter_loader import get_test_teachers

# The Java source parametrizes over the teachers but never logs in: it just re-runs the same
# crawl once per teacher. That is kept so the number of executed tests stays the same.
TEACHERS = [mail for mail, _password, _role in get_test_teachers()]


@pytest.mark.parametrize("teacher", TEACHERS)
async def test_spider_unlogged(user: BrowserUser, teacher: str) -> None:
    """Without logging in, every same-origin link reachable from the home page can be followed.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    executor/webbrowser/webserver(READWRITE,1).
    """
    broken_links = await spider_navigation.find_broken_links(user.page, user.app_url)

    assert not broken_links, "Broken links:\n" + "\n".join(broken_links)
