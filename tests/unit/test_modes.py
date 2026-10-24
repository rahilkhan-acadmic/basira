from core.modes import Mode, current_mode, live_gate_open


def test_default_mode_is_paper() -> None:
    assert current_mode({}) is Mode.PAPER


def test_unknown_mode_falls_back_to_paper() -> None:
    assert current_mode({"TRADING_MODE": "mock"}) is Mode.PAPER


def test_mode_strings_are_exact() -> None:
    assert {m.value for m in Mode} == {"replay", "paper", "live_calibration", "live"}


def test_live_gate_requires_every_condition() -> None:
    assert live_gate_open(Mode.LIVE, True, True, True)
    assert not live_gate_open(Mode.LIVE, False, True, True)
    assert not live_gate_open(Mode.LIVE, True, False, True)
    assert not live_gate_open(Mode.LIVE, True, True, False)
    assert not live_gate_open(Mode.PAPER, True, True, True)
