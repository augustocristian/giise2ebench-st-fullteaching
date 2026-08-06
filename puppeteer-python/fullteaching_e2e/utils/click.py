# -*- coding: utf-8 -*-
"""Click helpers with JS-click fallback, ported from utils/Click.java."""
import logging

from fullteaching_e2e.common.exceptions import ElementNotFoundException
from fullteaching_e2e.utils import scroll, wait

logger = logging.getLogger(__name__)

_JS_CLICK = (
    "(el) => {"
    "var evt = document.createEvent('MouseEvents');"
    "evt.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);"
    "el.dispatchEvent(evt);"
    "}"
)


async def here(page, x, y):
    """Clicks at absolute page coordinates (x, y), mirrors Click.here(wd, x, y)."""
    await page.mouse.click(x, y)
    return page


async def by_js(page, element):
    """Dispatches a synthetic click event via JS, bypassing overlays. Mirrors Click.byJS."""
    await page.evaluate(_JS_CLICK, element)


async def _resolve(page, selector):
    if selector.startswith("xpath="):
        results = await page.Jx(selector[len("xpath="):])
        return results[0] if results else None
    return await page.J(selector)


async def element(page, target):
    """Scrolls to and clicks an ElementHandle or selector string, falling back to a JS click.

    Mirrors the two overloads of Click.element(wd, ele) / Click.element(wd, eleBy).
    """
    el = await _resolve(page, target) if isinstance(target, str) else target
    if el is None:
        raise ElementNotFoundException(f"Click.element - element not found for selector '{target}'")

    scrolled = True
    try:
        await scroll.to_element(page, el)
    except Exception:
        logger.error("Click.element: Scroll failed continuing...")
        scrolled = False

    # Only wait for clickability when scroll succeeded; if scroll failed the element
    # is likely off-screen or zero-size, so go straight to JS to avoid a needless wait.
    if scrolled:
        try:
            await el.click()
            logger.info("Click.element (click): ==>OK")
            return page
        except Exception as e:
            logger.error("Click.element (click): ==>KO %s:%s", type(e).__name__, e)

    try:
        await by_js(page, el)
        logger.info("Click.element (ByJs): ==>OK")
        return page
    except Exception as e:
        logger.error("Click.element (ByJs): ==>KO %s:%s", type(e).__name__, e)

    raise ElementNotFoundException("Click.element ERROR")


async def with_n_retries(page, selector, n, wait_for_selector):
    """Retries clicking a selector up to n times, falling back to JS click each attempt.

    Mirrors Click.withNRetries(wd, eleBy, n, waitFor).
    """
    el = await _resolve(page, selector)
    if el is None:
        raise ElementNotFoundException(f"Click.withNRetries - element not found for selector '{selector}'")

    try:
        await scroll.to_element(page, el)
    except Exception:
        logger.error("Click.withNRetries: Failed on scroll")

    for attempt in range(n):
        try:
            await el.click()
            await wait.not_too_much(page, wait_for_selector)
            logger.info("Click.withNRetries (click): ==>OK")
            return page
        except Exception as e:
            logger.error("Click.withNRetries n (click):%s %s:%s", attempt, type(e).__name__, e)
            try:
                await by_js(page, el)
                logger.info("Click.withNRetries element (ByJs): ==>OK")
                return page
            except Exception as ex:
                logger.error("Click.withNRetries n (ByJS):%s %s:%s", attempt, type(ex).__name__, ex)

    logger.error("Click.withNRetries: ==>KO")
    raise ElementNotFoundException("Click doesn't work properly")
