# -*- coding: utf-8 -*-
"""User session E2E tests, ported from functional/test/UserTest.java."""
import pytest

from fullteaching_e2e.common import base_logged_test, user_utilities
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils.parameter_loader import get_test_users

# One test case per configured user; the id keeps credentials out of the test names.
USERS = [pytest.param(mail, password, id=f"{role.lower()}-{mail}") for mail, password, role in get_test_users()]


@pytest.mark.parametrize("mail,password", USERS)
async def test_login(user: BrowserUser, mail: str, password: str) -> None:
    """A user can log in (settings show their e-mail) and log out (login menu is shown again).

    Resources (RETORCH @AccessMode in the Java suite, informational only here):
    loginservice(READONLY,10) openvidu(NOACCESS,10) executor/webbrowser/webserver(READWRITE,1).
    """
    # Act: log in and open the settings page
    await base_logged_test.slow_login(user, mail, password)
    await user_utilities.check_login(user, mail)

    # Assert: the settings page belongs to the user that has just logged in
    await user.locator(c.SETTINGS_USER_EMAIL).wait_for_text(mail, exact=True)

    # Act + assert: after logging out the navbar offers the login link again
    await base_logged_test.logout(user)
    await user_utilities.check_log_out(user)
