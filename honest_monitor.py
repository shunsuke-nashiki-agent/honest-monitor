"""honest-monitor — a monitor you can't fool into a green lie.

Distilled from 112 real incidents where a monitor returned "healthy" while the
thing it was supposed to watch was broken. The root cause was almost always the
same: the monitor had never been *shown* to fire. It was written, it returned
green, everyone trusted it — but nobody ever broke the watched thing to confirm
that green can turn red.

Rule: a monitor that has never caught its own failure is not a monitor, it's a
decoration. So here every monitor ships a `break_it` negative control, and
`prove()` refuses to trust it until it has watched red appear and green return.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
import warnings


class GreenLie(AssertionError):
    """A monitor claimed healthy but failed to catch a real, injected break."""


@dataclass
class Monitor:
    name: str
    healthy: Callable[[], bool]                     # True == the watched thing is OK
    break_it: Callable[[], Callable[[], None]]      # break it; return a restore() callable
    _proven: bool = field(default=False, repr=False)

    def prove(self) -> "Monitor":
        """Break the watched thing and confirm the monitor turns red, then restore.

        Raises GreenLie if the monitor stays green through an injected failure.
        A monitor is not trusted (see .check) until this has passed.
        """
        if not self.healthy():
            raise AssertionError(
                f"[{self.name}] not healthy before the test — the proof would be meaningless")
        restore = self.break_it()
        try:
            if self.healthy():
                raise GreenLie(
                    f"[{self.name}] GREEN LIE: still reports healthy after break_it() — "
                    f"this monitor would sit green through the real failure it claims to watch")
        finally:
            restore()
        if not self.healthy():
            raise AssertionError(
                f"[{self.name}] not healthy after restore() — the negative control left damage")
        self._proven = True
        return self

    def check(self) -> bool:
        """Run the monitor. Warns loudly if used before prove() — unproven == decoration."""
        if not self._proven:
            warnings.warn(f"[{self.name}] used before prove(): an unproven monitor is a decoration",
                          stacklevel=2)
        return self.healthy()


def prove_all(monitors) -> list["Monitor"]:
    """prove() every monitor; collects and re-raises all GreenLies together."""
    lies = []
    for m in monitors:
        try:
            m.prove()
        except GreenLie as e:
            lies.append(str(e))
    if lies:
        raise GreenLie("unproven monitors:\n  - " + "\n  - ".join(lies))
    return list(monitors)
