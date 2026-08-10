import warnings
import pytest
from honest_monitor import Monitor, GreenLie, prove_all


def _honest(name="honest"):
    """A monitor whose break_it genuinely flips it red."""
    s = {"ok": True}
    return Monitor(name,
                   healthy=lambda: s["ok"],
                   break_it=lambda: (s.__setitem__("ok", False) or (lambda: s.__setitem__("ok", True))))


def _liar(name="liar"):
    """A green-lie monitor: break_it does not affect what healthy() reads."""
    return Monitor(name, healthy=lambda: True, break_it=lambda: (lambda: None))


def test_good_monitor_passes_and_becomes_trusted():
    m = _honest("freshness")
    m.prove()                      # breaks it, sees red, restores
    assert m._proven
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert m.check() is True   # proven -> no warning


def test_green_lie_is_caught():
    # classic green lie: checks a file EXISTS when it should check it is FRESH.
    # break_it makes it STALE (not absent), so an existence check stays green.
    stale = {"age_s": 0}
    liar = Monitor("exists-not-fresh",
                   healthy=lambda: True,                       # only checks existence
                   break_it=lambda: (stale.__setitem__("age_s", 9999) or (lambda: None)))
    with pytest.raises(GreenLie):
        liar.prove()


def test_unproven_monitor_warns():
    m = _liar("x")
    with pytest.warns(UserWarning):
        m.check()


def test_prove_all_reports_every_liar():
    with pytest.raises(GreenLie):
        prove_all([_honest(), _liar("liar-a"), _liar("liar-b")])
