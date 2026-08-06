# -*- coding: utf-8 -*-
"""Key-chord helpers, ported from the SELECT_ALL/DELETE Keys.chord() constants in Constants.java.

pyppeteer's Page.keyboard has no chord() helper, so a chord is a down/press/up sequence.
"""


async def select_all(page):
    await page.keyboard.down("Control")
    await page.keyboard.press("KeyA")
    await page.keyboard.up("Control")


async def delete(page):
    await page.keyboard.press("Backspace")


async def clear(page, field):
    """Selects all + deletes an input's content, mirrors Selenium's WebElement.clear()
    (which, unlike setting .value via JS, fires the native input events Angular listens for).
    """
    await field.click()
    await select_all(page)
    await delete(page)
