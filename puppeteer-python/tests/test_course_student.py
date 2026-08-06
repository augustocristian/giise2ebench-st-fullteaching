# -*- coding: utf-8 -*-
"""Ported from functional/test/student/CourseStudentTest.java."""
import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.utils import click, element, wait
from fullteaching_e2e.utils.parameter_loader import get_test_students


@pytest.mark.parametrize("mail,password,role", get_test_students())
async def test_student_course_main(user, mail, password, role):
    """Logs in as a student, opens the first course and checks every tab loads.

    Resources: course(READONLY,15) loginservice(READONLY,10) openvidumock(NOACCESS,10)
    executor/webbrowser/webserver(READWRITE,1).
    """
    await base_logged_test.slow_login(user, mail, password)
    page = user.page

    await navigation_utilities.to_courses_home(page, user.app_url)
    course_list = await course_nav.get_courses_list(page, user.app_url)
    if not course_list:
        pytest.fail("No courses available for test user")

    course = await course_nav.get_course_by_name(page, course_list[0])
    course_button = await element.find_one(course, c.COURSE_TITLE)
    await click.element(page, course_button)
    await wait.not_too_much(page, c.COURSE_TABS)

    await course_nav.go2_tab(page, c.HOME_ICON)
    await course_nav.go2_tab(page, c.SESSION_ICON)
    await course_nav.go2_tab(page, c.FORUM_ICON)
    await course_nav.go2_tab(page, c.FILES_ICON)
    await course_nav.go2_tab(page, c.ATTENDERS_ICON)
