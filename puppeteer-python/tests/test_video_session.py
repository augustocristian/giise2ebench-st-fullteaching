# -*- coding: utf-8 -*-
"""Ported from functional/test/media/FullTeachingTestEndToEndVideoSessionTests.java."""
import pytest

from fullteaching_e2e.utils import click, element, wait
from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.utils.parameter_loader import get_test_teachers

STUDENT_MAIL = "student1@gmail.com"
STUDENT_PASS = "pass"

_FIRST_COURSE_TITLE = "ul.collection li.collection-item:first-child div.course-title"
_SESSIONS_TAB = "#md-tab-label-0-1"
_FIRST_SESSION_READY = "ul div:first-child li.session-data div.session-ready"
_RECORD_VOICE_OVER_ICON = "xpath=//div[@id='div-header-buttons']//i[text() = 'record_voice_over']"
_INTERVENTION_BUTTON = "xpath=//a[contains(@class, 'usr-btn')]"


async def _enter_first_session_and_check_video(browser_user):
    page = browser_user.page
    await browser_user.wait_until(lambda: wait.not_too_much(page, _FIRST_COURSE_TITLE, visible=False),
                                   "First course not present")
    await click.element(page, _FIRST_COURSE_TITLE)

    await browser_user.wait_until(lambda: wait.not_too_much(page, _SESSIONS_TAB, visible=False),
                                   "'Sessions' tab not present")
    await click.element(page, _SESSIONS_TAB)

    await click.element(page, _FIRST_SESSION_READY)
    await browser_user.wait_until(lambda: wait.not_too_much(page, "div.participant video", visible=False),
                                   "Participant video not present")
    await _check_video_playing(browser_user, "div.participant")


async def _check_video_playing(browser_user, container_query_selector: str):
    """Confirms the <video> element has an active srcObject, mirrors checkVideoPlaying().

    Full readyState=4 is not checked because the CI media server cannot always relay media
    over DTLS to headless Chromium, so data never actually flows even though the session
    and stream objects are correctly initialized - same caveat the Java version documents.
    """
    probe = (
        f"var v = document.querySelector('{container_query_selector}').getElementsByTagName('video')[0];"
        "return v && v.srcObject != null && v.srcObject.active;"
    )

    async def _active():
        if not await browser_user.run_javascript(probe):
            raise TimeoutError(f"video in '{container_query_selector}' not playing yet")

    await wait.poll_until(_active)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_one_to_one_video_audio_session(user, browser_factory, app_config, mail, password, role):
    """Teacher and student join a session; the student requests to intervene, the teacher
    grants and then revokes it, and both sides' videos are checked at each step.

    Resources: loginservice(READONLY,10) openvidu(READWRITE,10) session(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    # TEACHER
    await base_logged_test.slow_login(user, mail, password)
    await _enter_first_session_and_check_video(user)

    # STUDENT
    student = await browser_factory("STUDENT", browser=app_config.student_browser, seconds_of_wait=5)
    await base_logged_test.slow_login(student, STUDENT_MAIL, STUDENT_PASS)
    await _enter_first_session_and_check_video(student)

    # Student asks for intervention
    await student.wait_until(lambda: wait.not_too_much(student.page, _RECORD_VOICE_OVER_ICON),
                              "Intervention request icon not clickable")
    await click.element(student.page, _RECORD_VOICE_OVER_ICON)

    # Teacher accepts intervention
    await user.wait_until(lambda: wait.not_too_much(user.page, _INTERVENTION_BUTTON),
                           "Intervention accept button not clickable")
    await click.element(user.page, _INTERVENTION_BUTTON)

    # Check both videos for both users
    await student.wait_until(lambda: wait.not_too_much(student.page, "div.participant-small video", visible=False),
                              "Student small video not present")
    await _check_video_playing(student, "div.participant-small")
    await _check_video_playing(student, "div.participant")

    await user.wait_until(lambda: wait.not_too_much(user.page, "div.participant-small video", visible=False),
                           "Teacher small video not present")
    await _check_video_playing(user, "div.participant-small")
    await _check_video_playing(user, "div.participant")

    # Teacher stops student intervention
    await user.wait_until(lambda: wait.not_too_much(user.page, _INTERVENTION_BUTTON),
                           "Intervention cancel button not clickable")
    await click.element(user.page, _INTERVENTION_BUTTON)

    # Wait until only one video is left on each side
    async def _no_small_video(page):
        if await element.find_one(page, "div.participant-small video") is not None:
            raise TimeoutError("small video still present")

    await user.wait_until(lambda: wait.poll_until(lambda: _no_small_video(user.page)), "small video still present")
    await student.wait_until(lambda: wait.poll_until(lambda: _no_small_video(student.page)),
                              "small video still present")
