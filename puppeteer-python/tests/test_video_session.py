# -*- coding: utf-8 -*-
"""Ported from functional/test/media/FullTeachingTestEndToEndVideoSessionTests.java.

A teacher and a student are two real, simultaneous users: each one drives its own browser context, and every
assertion on what the *other* user did waits for it to show up (see ``REALTIME_WAIT_MS``).
"""
import pytest

from fullteaching_e2e.browser import Locator
from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.utils.parameter_loader import get_test_teachers
from tests.support import (
    MEDIA_WAIT_MS,
    REALTIME_WAIT_MS,
    STUDENT_IDENTIFIER,
    STUDENT_MAIL,
    STUDENT_PASSWORD,
    UserCreator,
    open_first_session,
)

pytestmark = pytest.mark.e2e

# Video session page. The student's "raise hand" button is the second floating button of the header column
# (the first one toggles full screen); the teacher's grant/revoke button is the one carrying the usr-btn class.
MAIN_VIDEO_CONTAINER = "div.participant"
SMALL_VIDEO_CONTAINER = "div.participant-small"
RAISE_HAND_BUTTON = "#div-header-buttons > .col:nth-child(2) .btn-floating"
INTERVENTION_BUTTON = "#div-header-buttons .usr-btn"

# True once the first <video> of a container has an active srcObject (mirrors checkVideoPlaying()). Full
# readyState=4 is deliberately not checked: the CI media server cannot always relay media over DTLS to headless
# Chromium, so data never actually flows even though the session and stream objects are correctly initialized -
# the same caveat the Java version documents.
VIDEO_HAS_ACTIVE_STREAM_JS = """(containerSelector) => {
    const video = document.querySelector(containerSelector)?.getElementsByTagName('video')[0];
    return !!video && video.srcObject != null && video.srcObject.active === true;
}"""


def _small_video(user: BrowserUser) -> Locator:
    return user.locator(f"{SMALL_VIDEO_CONTAINER} video", REALTIME_WAIT_MS)


async def _expect_video_playing(user: BrowserUser, container: str) -> None:
    """Waits for the container's <video> to exist and to be fed by an active media stream."""
    await user.locator(f"{container} video", MEDIA_WAIT_MS).wait_for("attached")
    await user.page.wait_for_function(VIDEO_HAS_ACTIVE_STREAM_JS, container, timeout_ms=MEDIA_WAIT_MS)


async def _expect_small_and_main_videos_playing(user: BrowserUser) -> None:
    await _expect_video_playing(user, SMALL_VIDEO_CONTAINER)
    await _expect_video_playing(user, MAIN_VIDEO_CONTAINER)


async def _join_first_session_and_check_video(user: BrowserUser) -> None:
    """From the dashboard: enters the first ready session and waits for its main video."""
    await open_first_session(user)
    await _expect_video_playing(user, MAIN_VIDEO_CONTAINER)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_one_to_one_video_audio_session(user: BrowserUser, browser_factory: UserCreator, mail: str,
                                              password: str, role: str) -> None:
    """Teacher and student join a session; the student requests to intervene, the teacher
    grants and then revokes it, and both sides' videos are checked at each step.

    Resources: loginservice(READONLY,10) openvidu(READWRITE,10) session(READWRITE,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    teacher = user
    await base_logged_test.slow_login(teacher, mail, password)
    await _join_first_session_and_check_video(teacher)

    student = await browser_factory(STUDENT_IDENTIFIER, seconds_of_wait=c.MEDIA_WAIT_SECONDS)
    await base_logged_test.slow_login(student, STUDENT_MAIL, STUDENT_PASSWORD)
    await _join_first_session_and_check_video(student)

    # The student asks for the floor and the teacher grants it: both users now see both streams.
    await student.locator(RAISE_HAND_BUTTON, REALTIME_WAIT_MS).click()
    await teacher.locator(INTERVENTION_BUTTON, REALTIME_WAIT_MS).click()

    await _expect_small_and_main_videos_playing(student)
    await _expect_small_and_main_videos_playing(teacher)

    # The teacher takes the floor back: only the main video is left on each side.
    await teacher.locator(INTERVENTION_BUTTON, REALTIME_WAIT_MS).click()

    await _small_video(teacher).wait_for("detached")
    await _small_video(student).wait_for("detached")
