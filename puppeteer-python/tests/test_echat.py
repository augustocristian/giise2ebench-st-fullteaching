# -*- coding: utf-8 -*-
"""Ported from functional/test/media/FullTeachingEndToEndEChatTests.java."""
import pytest

from fullteaching_e2e.common import base_logged_test
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.utils import click, element, wait
from fullteaching_e2e.utils.parameter_loader import get_test_teachers

STUDENT_MAIL = "student1@gmail.com"
STUDENT_PASS = "pass"

_FIRST_COURSE_TITLE = "ul.collection li.collection-item:first-child div.course-title"
_SESSIONS_TAB = "#md-tab-label-0-1"
_FIRST_SESSION_READY = "ul div:first-child li.session-data div.session-ready"


async def _enter_first_session(browser_user):
    page = browser_user.page
    await browser_user.wait_until(lambda: wait.not_too_much(page, _FIRST_COURSE_TITLE, visible=False),
                                   "First course not present")
    await click.element(page, _FIRST_COURSE_TITLE)

    await browser_user.wait_until(lambda: wait.not_too_much(page, _SESSIONS_TAB, visible=False),
                                   "'Sessions' tab not present")
    await click.element(page, _SESSIONS_TAB)

    await click.element(page, _FIRST_SESSION_READY)
    await browser_user.wait_until(lambda: wait.not_too_much(page, "#fixed-icon"), "Element fixed-icon not clickable")
    await click.element(page, "#fixed-icon")


async def _get_number_messages(browser_user) -> int:
    return len(await element.find_all(browser_user.page, "app-chat-line"))


async def _check_system_message(browser_user, message: str, message_number: int):
    page = browser_user.page

    async def _has_messages():
        messages = await element.find_all(page, "app-chat-line")
        if not messages:
            raise TimeoutError("no chat messages yet")
        return messages

    messages = await wait.poll_until(_has_messages)
    last_message = messages[message_number] if 0 <= message_number < len(messages) else messages[-1]
    content = await element.find_one(last_message, ".system-msg")

    async def _content_matches():
        if await element.get_text(page, content) != message:
            raise TimeoutError("system message content mismatch")

    await browser_user.wait_until(lambda: wait.poll_until(_content_matches), f"system message '{message}' not shown")


async def _check_own_message(browser_user, message: str, sender: str, number_prior_messages: int):
    page = browser_user.page

    async def _more_messages():
        messages = await element.find_all(page, "app-chat-line")
        if len(messages) <= number_prior_messages:
            raise TimeoutError("own message not attached yet")
        return messages

    messages = await wait.poll_until(_more_messages)
    last_message = messages[-1]
    msg_user = await element.find_one(last_message, ".own-msg .message-header .user-name")
    msg_content = await element.find_one(last_message, ".own-msg .message-content .user-message")

    async def _matches():
        if await element.get_text(page, msg_user) != sender or await element.get_text(page, msg_content) != message:
            raise TimeoutError("own message not yet rendered")

    await browser_user.wait_until(lambda: wait.poll_until(_matches), f"own message '{message}' from {sender}")


async def _check_stranger_message(browser_user, message: str, sender: str, number_prior_messages: int):
    page = browser_user.page

    async def _more_messages():
        messages = await element.find_all(page, "app-chat-line")
        if len(messages) <= number_prior_messages:
            raise TimeoutError("stranger message not attached yet")
        return messages

    messages = await wait.poll_until(_more_messages)
    last_message = messages[-1]
    msg_user = await element.find_one(last_message, ".stranger-msg .message-header .user-name")
    msg_content = await element.find_one(last_message, ".stranger-msg .message-content .user-message")

    async def _matches():
        if await element.get_text(page, msg_user) != sender or await element.get_text(page, msg_content) != message:
            raise TimeoutError("stranger message not yet rendered")

    await browser_user.wait_until(lambda: wait.poll_until(_matches), f"stranger message '{message}' from {sender}")


@pytest.mark.parametrize("mail,password,role", get_test_teachers())
async def test_one_to_one_chat_in_session(user, browser_factory, app_config, mail, password, role):
    """Teacher and student join the same video session and exchange chat messages.

    Resources: loginservice(READONLY,10) openvidu(READWRITE,10) configuration(READONLY,1)
    executor/webbrowser/webserver(READWRITE,1).
    """
    # TEACHER
    await base_logged_test.slow_login(user, mail, password)
    await _enter_first_session(user)
    await _check_system_message(user, "Connected", 100)

    # STUDENT
    student = await browser_factory("STUDENT", browser=app_config.student_browser, seconds_of_wait=5)
    await base_logged_test.slow_login(student, STUDENT_MAIL, STUDENT_PASS)
    await _enter_first_session(student)
    await _check_system_message(student, "Connected", 0)

    await _check_system_message(user, f"{c.STUDENT_NAME} has connected", 100)
    await _check_system_message(student, f"{c.TEACHER_NAME} has connected", 100)

    # Chat exchange
    teacher_message = "TEACHER CHAT MESSAGE"
    student_message = "STUDENT CHAT MESSAGE"

    number_prior_messages = await _get_number_messages(user)
    chat_input_teacher = await element.find_one(user.page, "#message")
    await chat_input_teacher.type(teacher_message)
    await user.wait_until(lambda: wait.not_too_much(user.page, "#send-btn"), "Send button not clickable")
    await click.element(user.page, "#send-btn")

    await _check_own_message(user, teacher_message, c.TEACHER_NAME, number_prior_messages)
    await _check_stranger_message(student, teacher_message, c.TEACHER_NAME, number_prior_messages)

    number_prior_messages = await _get_number_messages(student)
    chat_input_student = await element.find_one(student.page, "#message")
    await chat_input_student.type(student_message)
    await student.wait_until(lambda: wait.not_too_much(student.page, "#send-btn"), "Send button not clickable")
    await click.element(student.page, "#send-btn")

    await _check_stranger_message(user, student_message, c.STUDENT_NAME, number_prior_messages)
    await _check_own_message(student, student_message, c.STUDENT_NAME, number_prior_messages)
