# -*- coding: utf-8 -*-
"""Ported from functional/test/media/FullTeachingEndToEndEChatTests.java.

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
    REALTIME_WAIT_MS,
    STUDENT_IDENTIFIER,
    STUDENT_MAIL,
    STUDENT_PASSWORD,
    UserCreator,
    open_first_session,
)

pytestmark = pytest.mark.e2e

# Chat
CHAT_LINE = "app-chat-line"
SYSTEM_MESSAGE = ".system-msg"
OWN_MESSAGE = ".own-msg"
STRANGER_MESSAGE = ".stranger-msg"
MESSAGE_SENDER = ".message-header .user-name"
MESSAGE_TEXT = ".message-content .user-message"
MESSAGE_INPUT = "#message"
SEND_BUTTON = "#send-btn"

CONNECTED_NOTICE = "Connected"
TEACHER_MESSAGE = "TEACHER CHAT MESSAGE"
STUDENT_MESSAGE = "STUDENT CHAT MESSAGE"


def _chat_lines(user: BrowserUser) -> Locator:
    return user.locator(CHAT_LINE, REALTIME_WAIT_MS)


async def _enter_session_chat(user: BrowserUser) -> None:
    """From the dashboard: enters the first ready session and opens its side menu (the chat)."""
    await open_first_session(user)
    await user.locator(c.SESSION_FIXED_ICON, REALTIME_WAIT_MS).click()


async def _send_message(user: BrowserUser, message: str) -> None:
    await user.locator(MESSAGE_INPUT).fill(message)
    await user.locator(SEND_BUTTON).click()


async def _expect_system_message(chat_line: Locator, text: str) -> None:
    await chat_line.within(SYSTEM_MESSAGE).wait_for_text(text)


async def _expect_last_message(user: BrowserUser, kind: str, sender: str, text: str) -> None:
    """Waits for the newest chat line to be a message of the given kind (own or from the other user)."""
    message = _chat_lines(user).last().within(kind)
    await message.within(MESSAGE_SENDER).wait_for_text(sender)
    await message.within(MESSAGE_TEXT).wait_for_text(text)


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_one_to_one_chat_in_session(user: BrowserUser, browser_factory: UserCreator, mail: str,
                                          password: str, role: str) -> None:
    """Teacher and student join the same video session and exchange chat messages.

    Resources: loginservice(READONLY,10) openvidu(READWRITE,10) configuration(READONLY,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    teacher = user
    await base_logged_test.slow_login(teacher, mail, password)
    await _enter_session_chat(teacher)
    await _expect_system_message(_chat_lines(teacher).last(), CONNECTED_NOTICE)

    student = await browser_factory(STUDENT_IDENTIFIER, seconds_of_wait=c.MEDIA_WAIT_SECONDS)
    await base_logged_test.slow_login(student, STUDENT_MAIL, STUDENT_PASSWORD)
    await _enter_session_chat(student)
    await _expect_system_message(_chat_lines(student).first(), CONNECTED_NOTICE)

    await _expect_system_message(_chat_lines(teacher).last(), f"{c.STUDENT_NAME} has connected")
    await _expect_system_message(_chat_lines(student).last(), f"{c.TEACHER_NAME} has connected")

    await _send_message(teacher, TEACHER_MESSAGE)
    await _expect_last_message(teacher, OWN_MESSAGE, c.TEACHER_NAME, TEACHER_MESSAGE)
    await _expect_last_message(student, STRANGER_MESSAGE, c.TEACHER_NAME, TEACHER_MESSAGE)

    await _send_message(student, STUDENT_MESSAGE)
    await _expect_last_message(teacher, STRANGER_MESSAGE, c.STUDENT_NAME, STUDENT_MESSAGE)
    await _expect_last_message(student, OWN_MESSAGE, c.STUDENT_NAME, STUDENT_MESSAGE)
