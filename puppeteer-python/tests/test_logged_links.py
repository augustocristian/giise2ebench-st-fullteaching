# -*- coding: utf-8 -*-
"""Spider test with a session, ported from functional/test/LoggedLinksTests.java."""
import pytest

from fullteaching_e2e.common import base_logged_test, spider_navigation
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils.parameter_loader import get_test_users

# One test case per configured user; the id keeps credentials out of the test names.
USERS = [pytest.param(mail, password, id=f"{role.lower()}-{mail}") for mail, password, role in get_test_users()]


@pytest.mark.parametrize("mail,password", USERS)
async def test_spider_logged(user: BrowserUser, mail: str, password: str) -> None:
    """After logging in, every same-origin link reachable from the home page can be followed.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)

    broken_links = await spider_navigation.find_broken_links(user.page, user.app_url)

    assert not broken_links, "Broken links:\n" + "\n".join(broken_links)
