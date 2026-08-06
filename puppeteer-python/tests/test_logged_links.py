# -*- coding: utf-8 -*-
"""Ported from functional/test/LoggedLinksTests.java."""
import pytest

from fullteaching_e2e.common import base_logged_test, navigation_utilities, spider_navigation
from fullteaching_e2e.common.constants import SPIDER_DEPTH
from fullteaching_e2e.utils.parameter_loader import get_test_users


@pytest.mark.parametrize("mail,password,role", get_test_users())
async def test_spider_logged(user, app_config, mail, password, role):
    """Logs in, then crawls every same-origin link and asserts none 404/error.

    Resources: loginservice(READONLY,10) openvidumock(NOACCESS,10) course(READWRITE,15)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)
    await navigation_utilities.get_url_and_wait_footer(user.page, app_config.app_url)
    page_links = await spider_navigation.get_page_links(user.page)
    explored = await spider_navigation.explore_links(user.page, page_links, {}, SPIDER_DEPTH)
    failed_links = [link for link, result in explored.items() if result == "KO"]
    assert not failed_links, "\n".join(failed_links)
