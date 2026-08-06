"""Helpers for lists of elements: a ``Locator`` is lazy, so a list is a locator plus indexes."""
from fullteaching_e2e.browser import Locator


async def all_of(locator: Locator) -> list[Locator]:
    """One locator per element the given one matches right now (each pinned with ``nth``)."""
    return [locator.nth(index) for index in range(await locator.count())]


async def texts(locator: Locator) -> list[str]:
    """Stripped text of every element the locator matches right now, in DOM order."""
    return [(await item.text()).strip() for item in await all_of(locator)]


async def find_row_by_child_text(rows: Locator, child_selector: str, text: str) -> Locator | None:
    """The row whose first ``child_selector`` descendant has exactly ``text``, or ``None``.

    Rows without such a descendant are skipped. Looks at the DOM as it is now: wrap it in
    ``wait.poll_until`` when the list may still be rendering.
    """
    for row in await all_of(rows):
        child = row.within(child_selector).first()
        if await child.count() and (await child.text()).strip() == text:
            return row
    return None
