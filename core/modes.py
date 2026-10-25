"""Trading modes and the live-trading gate (spec Glossary, Safety Rule 1).

Exactly four mode strings exist: ``replay``, ``paper``, ``live_calibration``, ``live``.
The default is always ``paper``. Live modes need every gate in Safety Rule 1; this module
only implements the environment/config part of that check. The signed human approval
record and the live-account check are added in M5/M21.
"""

from __future__ import annotations

import os
from enum import StrEnum


class Mode(StrEnum):
    REPLAY = "replay"
    PAPER = "paper"
    LIVE_CALIBRATION = "live_calibration"
    LIVE = "live"

    @property
    def is_live(self) -> bool:
        return self in (Mode.LIVE_CALIBRATION, Mode.LIVE)


DEFAULT_MODE = Mode.PAPER


def current_mode(env: dict[str, str] | None = None) -> Mode:
    """Read ``TRADING_MODE``; unknown or missing values fall back to ``paper``."""
    source = os.environ if env is None else env
    raw = source.get("TRADING_MODE", "").strip().lower()
    try:
        return Mode(raw)
    except ValueError:
        return DEFAULT_MODE


def live_gate_open(
    mode: Mode, live_trading_enabled: bool, approval_record_valid: bool, in_live_account: bool
) -> bool:
    """All four conditions of Safety Rule 1 must hold for a live mode."""
    if not mode.is_live:
        return False
    return live_trading_enabled and approval_record_valid and in_live_account
