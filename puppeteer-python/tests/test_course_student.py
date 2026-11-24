# -*- coding: utf-8 -*-
"""Ported from functional/test/student/CourseStudentTest.java."""
import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils.parameter_loader import get_test_students
from tests.support import open_first_course_and_visit_every_tab

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("mail,password,role", get_test_students())
async def test_student_course_main(user: BrowserUser, mail: str, password: str, role: str) -> None:
    """Logs in as a student, opens the first course and checks every tab loads.

    Resources: course(READONLY,15) loginservice(READONLY,10) openvidumock(NOACCESS,10)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)

    await open_first_course_and_visit_every_tab(user)
