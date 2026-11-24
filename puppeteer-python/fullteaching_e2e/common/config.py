"""Run configuration, read from environment variables.

``SUT_URL`` and ``tjob_name`` keep the names used by the Selenium suite; the browser is
controlled only by ``HEADED``, ``PUPPETEER_EXECUTABLE_PATH`` and ``BROWSER_ARGS``.
"""
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from fullteaching_e2e.common.constants import LOCALHOST

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
RESOURCES_DIR = ROOT_DIR / "resources"
INPUTS_DIR = RESOURCES_DIR / "inputs"

DEFAULT_TJOB_NAME = "TJobDef"
CHROME = "chrome"


@dataclass(frozen=True)
class AppConfig:
    """Where the application lives and which TJob is running."""

    app_url: str
    tjob_name: str
    # Informational only: Puppeteer drives Chromium, so any other value falls back to it.
    teacher_browser: str = CHROME
    student_browser: str = CHROME


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _browser_name(variable: str) -> str:
    value = os.environ.get(variable) or CHROME
    if value != CHROME:
        logger.warning("%s=%s ignored: only Chromium is automated", variable, value)
    return CHROME


def load_app_config() -> AppConfig:
    """Resolves ``SUT_URL``/``tjob_name`` like ``BaseLoggedTest.setupAll()``.

    ``tjob_name`` is honoured only together with ``SUT_URL``; without it the URL falls back
    to ``app.url`` and then to :data:`LOCALHOST`.
    """
    sut_url = os.environ.get("SUT_URL")
    if sut_url:
        app_url, tjob_name = sut_url, os.environ.get("tjob_name") or DEFAULT_TJOB_NAME
    else:
        app_url, tjob_name = os.environ.get("app.url") or LOCALHOST, DEFAULT_TJOB_NAME
    logger.debug("Using URL %s TJOB: %s", app_url, tjob_name)
    return AppConfig(app_url, tjob_name, _browser_name("TEACHER_BROWSER"), _browser_name("STUDENT_BROWSER"))


def is_headed() -> bool:
    """Chrome is headless unless ``HEADED`` is 1/true/yes."""
    return _flag("HEADED")


def browser_executable_path() -> str | None:
    """Explicit Chrome binary; by default the bridge uses the system Chrome."""
    return os.environ.get("PUPPETEER_EXECUTABLE_PATH") or None


def browser_args() -> list[str]:
    """Extra Chrome flags from ``BROWSER_ARGS`` (space separated)."""
    return os.environ.get("BROWSER_ARGS", "").split()
