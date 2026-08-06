# -*- coding: utf-8 -*-
"""Ported from functional/test/UserTest.java."""
import pytest

from fullteaching_e2e.common import base_logged_test, user_utilities
from fullteaching_e2e.utils.parameter_loader import get_test_users


@pytest.mark.parametrize("mail,password,role", get_test_users())
async def test_login(user, mail, password, role):
    """A simple login acknowledgement: log in, confirm it worked, log out, confirm that too.

    Resources (RETORCH @AccessMode in the Java suite, informational only here):
    loginservice(READONLY,10) openvidu(NOACCESS,10) executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)
    await user_utilities.check_login(user.page, mail)

    await base_logged_test.logout(user)
    await user_utilities.check_log_out(user.page)
