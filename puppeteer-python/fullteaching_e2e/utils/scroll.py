# -*- coding: utf-8 -*-
"""Scroll-into-view helper, ported from utils/Scroll.java."""

_SCROLL_INTO_VIEW = "(el) => el.scrollIntoView({block: 'center', inline: 'center'})"


async def to_element(page, element):
    """Scrolls the element into the center of the viewport, mirrors Scroll.toElement."""
    await page.evaluate(_SCROLL_INTO_VIEW, element)
