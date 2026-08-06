# -*- coding: utf-8 -*-
"""Course/tab navigation helpers, ported from common/CourseNavigationUtilities.java."""
import asyncio
import logging
from typing import List, Optional

from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import navigation_utilities
from fullteaching_e2e.common.exceptions import ElementNotFoundException
from fullteaching_e2e.utils import click, dom_manager, element, keyboard, wait

logger = logging.getLogger(__name__)


async def new_course(page, host: str, course_name: str) -> str:
    await navigation_utilities.to_courses_home(page, host)

    logger.debug("Checking existing courses...")
    await wait.a_little(page, ".course-list-item", visible=False)
    new_course_button = await wait.not_too_much(page, c.NEW_COURSE_BUTTON, visible=False)
    await click.by_js(page, new_course_button)
    await wait.not_too_much(page, c.NEW_COURSE_MODAL)

    logger.debug("Introducing Course Name: %s", course_name)
    name_field = await wait.a_little(page, c.NEW_COURSE_MODAL_NAME_FIELD)
    await name_field.type(course_name)
    await click.element(page, c.NEW_COURSE_MODAL_SAVE)

    await check_if_course_exists(page, course_name)

    return course_name


async def check_if_course_exists(page, course_title: str) -> bool:
    course_list = await wait.not_too_much(page, c.COURSE_LIST)
    courses = await element.find_all(course_list, "li")

    for course in courses:
        title_text = "No courses"
        try:
            title_element = await element.find_one(course, c.COURSE_TITLE)
            if title_element is None:
                continue
            title_text = await element.get_text(page, title_element)
            if course_title == title_text:
                logger.info("The course with title %s exists!", course_title)
                return True
        except Exception:
            logger.debug("The current course is:%s and the course that we are searching is %s",
                         course_title, title_text)
    return False


async def check_if_course_exists_with_retries(page, course_title: str, retries: int) -> bool:
    for _ in range(retries):
        if await check_if_course_exists(page, course_title):
            return True
        await asyncio.sleep(1)
    return False


async def _open_edit_course_modal(page, course_element):
    edit_name_button = await element.find_one(course_element, c.EDIT_COURSE_BUTTON)
    await click.element(page, edit_name_button)
    await wait.not_too_much(page, c.EDIT_DELETE_MODAL)


async def _save_changes(page):
    logger.debug("Click save button, saving changes...")
    await click.element(page, c.EDIT_COURSE_MODAL_SAVE)


async def change_course_name(page, old_name: str, new_name: str):
    logger.info("[INI] changeCourseName(%s=>%s)", old_name, new_name)
    try:
        await wait.not_too_much(page, c.COURSE_LIST)
        logger.info("Looking for the course")
        course_selected = await get_course_by_name(page, old_name)

        await _open_edit_course_modal(page, course_selected)

        logger.info("Changing the course Name")
        name_field = await wait.a_little(page, c.EDIT_COURSE_MODAL_NAME_FIELD)
        # Select-all + type so Angular's ngModel detects the change (JS-set value doesn't fire input events)
        await name_field.click()
        await keyboard.select_all(page)
        await name_field.type(new_name)

        await _save_changes(page)
        await wait.not_too_much(page, c.EDIT_DELETE_MODAL, visible=False, hidden=True)
    except ElementNotFoundException:
        logger.info("[END] changeCourseName KO: Course \"%s\" probably doesn't exist", old_name)
        raise ElementNotFoundException(f"changeCourseName - Course {old_name} probably doesn't exist")

    logger.info("[END] changeCourseName OK")
    return page


async def delete_course(page, host: str, course_name: str):
    logger.info("[INI] deleteCourse(%s)", course_name)

    await navigation_utilities.to_courses_home(page, host)
    courses_list = await wait.not_too_much(page, c.COURSE_LIST)
    num_courses_initial = len(await element.find_all(courses_list, "li"))
    try:
        course_element = await get_course_by_name(page, course_name)
        await _open_edit_course_modal(page, course_element)

        logger.info("Enabling delete course")
        delete_check = await wait.a_little(page, c.EDIT_COURSE_DELETE_CHECK)
        await click.element(page, delete_check)

        logger.info("Click delete Course")
        delete_button = await wait.a_little(page, c.EDIT_COURSE_DELETE_BUTTON)
        await click.element(page, delete_button)

        await _save_changes(page)
    except ElementNotFoundException:
        logger.error("[END] deleteCourse KO: Course \"%s\" probably doesn't exist", course_name)
        raise ElementNotFoundException(f"deleteCourse - Course {course_name} probably doesn't exist")

    logger.debug("Checking that after removing the course, the number of courses is %d minus one",
                 num_courses_initial)

    async def _course_count_decreased():
        list_courses = await element.find_one(page, c.COURSE_LIST)
        current = len(await element.find_all(list_courses, "li"))
        if current != num_courses_initial - 1:
            raise TimeoutError(f"course count is {current}, expected {num_courses_initial - 1}")
        return current

    await wait.poll_until(_course_count_decreased)

    logger.info("[END] deleteCourse OK: Course \"%s\"", course_name)


async def get_courses_list(page, host: str) -> List[str]:
    courses_names = []
    await navigation_utilities.to_courses_home(page, host)
    courses_list = await wait.not_too_much(page, c.COURSE_LIST)
    courses = await element.find_all(courses_list, "li")
    for course in courses:
        title = await element.find_one(course, c.COURSE_TITLE)
        if title is not None:
            courses_names.append(await element.get_text(page, title))
    return courses_names


async def get_course_by_name(page, name: str):
    logger.info("Finding the newly created course")
    courses_list = await wait.not_too_much(page, c.COURSE_LIST)
    courses = await element.find_all(courses_list, "li")
    logger.info("Iterating over the course lists")

    for course in courses:
        title = await element.find_one(course, c.COURSE_TITLE)
        if title is None:
            continue
        title_text = await element.get_text(page, title)
        if name == title_text:
            logger.info("Course with title %s found!", title_text)
            return course
        logger.info("Course not found looking, for the next item")
    raise ElementNotFoundException("getCourseElement - the course doesn't exist")


async def get_tab_element_from_icon(page, icon_selector: str):
    course_tabs = await element.find_one(page, c.COURSE_TABS)
    icon_element = await element.find_one(course_tabs, icon_selector)
    parent1 = await dom_manager.get_parent(page, icon_element)
    parent2 = await dom_manager.get_parent(page, parent1)
    return parent2


async def go2_tab(page, icon_selector: str):
    tab = await get_tab_element_from_icon(page, icon_selector)
    tab_id = await element.get_attribute(page, tab, "id")
    logger.info("Navigating to tab with id: %s", tab_id)
    await click.element(page, tab)
    content_id = tab_id.replace("label", "content")
    await wait.a_little(page, f"#{content_id}")
    return page


async def get_tab_id(page, icon_selector: str) -> str:
    tab = await get_tab_element_from_icon(page, icon_selector)
    return await element.get_attribute(page, tab, "id")


async def get_tab_content(page, icon_selector: str):
    logger.info("Get Tab content")
    tab_id = await get_tab_id(page, icon_selector)
    return await element.find_one(page, f"#{tab_id.replace('label', 'content')}")


async def wait4_tab_content(page, icon_selector: str):
    logger.info("Waiting for tab content")
    tab_id = await get_tab_id(page, icon_selector)
    return await wait.not_too_much(page, f"#{tab_id.replace('label', 'content')}")


async def is_user_in_attenders_list(page, user_name: str) -> bool:
    logger.info("[INI] isUserInAttendersList")
    await wait.not_too_much(page, c.ATTENDERS_ICON)
    await get_tab_content(page, c.ATTENDERS_ICON)
    await wait.not_too_much(page, c.ATTENDERS_LIST_ROWS)
    attenders = await element.find_all(page, c.ATTENDERS_LIST_ROWS)
    if not attenders:
        logger.info("[END] isUserInAttendersList KO: attenders list is empty")
        raise ElementNotFoundException("isUserInAttendersList - attenders list is empty")
    for row in attenders:
        row_text = await element.get_text(page, row)
        if user_name.strip().casefold() == row_text.strip().casefold():
            logger.info("[END] isUserInAttendersList OK")
            return True
    logger.info("[END] isUserInAttendersList KO: user not found")
    return False


async def get_highlighted_attender(page) -> Optional[str]:
    logger.info("[INI] getHighlightedAttender")
    attenders_content = await get_tab_content(page, c.ATTENDERS_ICON)
    highlighted = await element.find_all(attenders_content, c.ATTENDERS_LIST_HIGHLIGHTED_ROW)
    if not highlighted:
        logger.info("[END] getHighlightedAttender KO: no highlighted user")
        raise ElementNotFoundException("getHighlightedAttender - no highlighted user")
    return await element.get_text(page, highlighted[0])
