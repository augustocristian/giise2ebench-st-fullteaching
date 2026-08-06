"""Session navigation helpers, ported from ``common/SessionNavigationUtilities.java``."""
from fullteaching_e2e.browser import Locator
from fullteaching_e2e.common import constants as c
from fullteaching_e2e.common import course_navigation_utilities as course_nav
from fullteaching_e2e.common.browser_user import BrowserUser
from fullteaching_e2e.common.exceptions import ElementNotFoundException
from fullteaching_e2e.utils import element


async def _session_rows(user: BrowserUser) -> Locator:
    tab_content = await course_nav.get_tab_content(user, c.SESSION_ICON)
    return tab_content.within(c.SESSION_LIST_SESSION_ROW)


async def get_full_session_list(user: BrowserUser) -> list[str]:
    """Titles of every session of the open course, in order."""
    rows = await _session_rows(user)
    return await element.texts(rows.within(c.SESSION_LIST_SESSION_NAME))


async def get_session(user: BrowserUser, session_name: str) -> Locator:
    """The row of the session with this exact title.

    Raises:
        ElementNotFoundException: no session has that title.
    """
    rows = await _session_rows(user)
    session = await element.find_row_by_child_text(rows, c.SESSION_LIST_SESSION_NAME, session_name)
    if session is None:
        raise ElementNotFoundException(
            f"[{user.client_data}] get_session: the session \"{session_name}\" doesn't exist; "
            f"listed sessions: {await element.texts(rows.within(c.SESSION_LIST_SESSION_NAME))}")
    return session
