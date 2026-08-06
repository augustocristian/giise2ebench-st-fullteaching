# -*- coding: utf-8 -*-
"""Timeout helpers, ported from utils/Wait.java."""
import asyncio
import logging

from fullteaching_e2e.common.constants import FOOTER

logger = logging.getLogger(__name__)

NOT_TOO_MUCH_TIMEOUT_MS = 20_000
A_LITTLE_TIMEOUT_MS = 4_000
PAGE_LOAD_TIMEOUT_MS = 30_000


async def _wait_for(page, selector, timeout, visible, hidden):
    if selector.startswith("xpath="):
        return await page.waitForXPath(selector[len("xpath="):],
                                        {"visible": visible, "hidden": hidden, "timeout": timeout})
    return await page.waitForSelector(selector, {"visible": visible, "hidden": hidden, "timeout": timeout})


async def not_too_much(page, selector, visible=True, hidden=False):
    """Waits up to 20s for the selector, mirrors Wait.notTooMuch(wd)."""
    return await _wait_for(page, selector, NOT_TOO_MUCH_TIMEOUT_MS, visible, hidden)


async def a_little(page, selector, visible=True, hidden=False):
    """Waits up to 4s for the selector, mirrors Wait.aLittle(wd)."""
    return await _wait_for(page, selector, A_LITTLE_TIMEOUT_MS, visible, hidden)


async def footer(page):
    await not_too_much(page, FOOTER)


async def wait_for_page_loaded(page, timeout_ms=PAGE_LOAD_TIMEOUT_MS):
    await page.waitForFunction("document.readyState === 'complete'", {"timeout": timeout_ms})


async def poll_until(factory, timeout_ms=NOT_TOO_MUCH_TIMEOUT_MS, interval=0.2):
    """Retries an async factory() until it stops raising, or timeout_ms elapses.

    Used where pyppeteer has no built-in "expected condition" (element count, custom
    predicate...), mirroring the lambda-based `ExpectedCondition`s used throughout the
    Java suite (e.g. WebDriverWait.until(driver -> ...)).
    """
    deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
    last_error = None
    while asyncio.get_event_loop().time() < deadline:
        try:
            return await factory()
        except Exception as e:  # noqa: BLE001 - genuinely retrying any failure until timeout
            last_error = e
            await asyncio.sleep(interval)
    raise TimeoutError(str(last_error))
