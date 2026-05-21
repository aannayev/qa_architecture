from __future__ import annotations

import importlib

import pytest


@pytest.fixture(autouse=True)
def _reset_in_memory_state():
    """Reset per-process state between tests so rate-limit counters and
    conversation history don't bleed across cases.
    """
    from app import main as ai_main

    importlib.reload(ai_main)
    yield
