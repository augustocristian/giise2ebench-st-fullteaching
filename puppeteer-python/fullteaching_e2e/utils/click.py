"""Click through the DOM instead of the mouse."""
import json

from fullteaching_e2e.browser import Page
from fullteaching_e2e.common.exceptions import ElementNotFoundException


async def by_js(page: Page, selector: str) -> None:
    """Dispatches a DOM ``click()`` on the first match of a CSS selector.

    Unlike ``Locator.click`` it needs neither a visible nor an unobstructed element, so it is the
    way out when an overlay intercepts the real mouse click (e.g. the video-session exit icon).
    """
    clicked = await page.evaluate(f"() => {{ const el = document.querySelector({json.dumps(selector)}); "
                                  "if (el) el.click(); return el !== null; }")
    if not clicked:
        raise ElementNotFoundException(f"click.by_js: no element matches '{selector}'")
