# -*- coding: utf-8 -*-
"""DOM traversal helper, ported from utils/DOMManager.java."""

_GET_PARENT = "(el) => el.parentNode"


async def get_parent(page, element):
    """Returns the parentNode of an element as an ElementHandle, mirrors DOMManager.getParent."""
    handle = await page.evaluateHandle(_GET_PARENT, element)
    return handle.asElement()
