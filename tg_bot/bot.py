"""Compatibility runner for existing IDE configurations.

Prefer ``python main.py`` or ``python -m tg_bot`` for new configurations.
"""

# ruff: noqa: I001 -- this compatibility runner bootstraps the package path.

import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tg_bot.application import run_bot


if __name__ == "__main__":
    asyncio.run(run_bot())
