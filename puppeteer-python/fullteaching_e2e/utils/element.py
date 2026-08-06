# -*- coding: utf-8 -*-
"""ElementHandle text/attribute readers.

pyppeteer's ElementHandle, unlike Selenium's WebElement, has no getText()/getAttribute();
both are plain JS evaluated against the element.
"""


async def get_text(page, element) -> str:
    if element is None:
        return ""
    text = await page.evaluate("(el) => el.textContent", element)
    return (text or "").strip()


async def get_attribute(page, element, name: str):
    return await page.evaluate("(el, attr) => el.getAttribute(attr)", element, name)


async def get_dom_property(page, element, name: str):
    return await page.evaluate("(el, prop) => el[prop]", element, name)


async def get_tag_name(page, element) -> str:
    return await page.evaluate("(el) => el.tagName.toLowerCase()", element)


async def find_one(container, selector: str):
    """container is a Page or ElementHandle; both expose querySelector."""
    return await container.querySelector(selector)


async def find_all(container, selector: str):
    """container is a Page or ElementHandle; both expose querySelectorAll."""
    return await container.querySelectorAll(selector)
