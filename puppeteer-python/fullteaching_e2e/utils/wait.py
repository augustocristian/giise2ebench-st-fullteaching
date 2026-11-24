"""Polling for conditions the bridge cannot wait for natively.

Locators already wait for elements (``wait_for``, ``click``, ``text``...), so use them whenever
the condition is about one selector; ``poll_until`` is for computed conditions such as "the list
of titles contains X" or "the comment count grew".
"""
import asyncio
import time
from collections.abc import Awaitable, Callable

from fullteaching_e2e.browser import ElementTimeoutError

DEFAULT_TIMEOUT_S = 20.0
POLL_INTERVAL_S = 0.2


async def poll_until[T](
    factory: Callable[[], Awaitable[T]],
    description: str = "condition",
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> T:
    """Calls ``factory`` until it returns a value other than ``False``/``None`` without raising.

    Any exception raised by the factory means "not yet" and is retried, so a factory can simply
    assert or look an element up. Returns the accepted value.

    Raises:
        ElementTimeoutError: the condition did not hold within ``timeout_s``; carries the last error.
    """
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while True:
        try:
            value = await factory()
            if value is not False and value is not None:
                return value
            last_error = None
        except Exception as error:  # any failure of the condition means "not yet"
            last_error = error
        if time.monotonic() >= deadline:
            break
        await asyncio.sleep(POLL_INTERVAL_S)
    message = f"Timed out after {timeout_s:g}s waiting for: {description}"
    if last_error is not None:
        message += f" (last error: {last_error})"
    raise ElementTimeoutError(message) from last_error
