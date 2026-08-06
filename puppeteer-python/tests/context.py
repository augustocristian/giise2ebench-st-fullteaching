# -*- coding: utf-8 -*-
"""Mirrors example/tests/context.py: makes the project root importable without an install.

pyproject.toml's `pythonpath = ["."]` already does this for `pytest`, so importing this
module is optional; kept for parity with the reference template and for ad-hoc scripts
run outside pytest.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
