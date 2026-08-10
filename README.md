# honest-monitor

**A monitor you can't fool into a green lie.**

Distilled from 112 real incidents where a monitor returned *"healthy"* while the
thing it was supposed to watch was quietly broken. The root cause was almost
always the same: **the monitor had never been shown to fire.** It was written,
it returned green, everyone trusted it — but nobody ever broke the watched thing
to confirm that green can actually turn red.

> A monitor that has never caught its own failure is not a monitor. It's a decoration.

So here, every monitor ships a **negative control** (`break_it`), and `prove()`
refuses to trust it until it has *watched red appear and green return.*

## The idea in 30 seconds

```python
from honest_monitor import Monitor

# A monitor is a health check + a way to deliberately break what it watches.
backup = Monitor(
    name="nightly-backup",
    healthy=lambda: backup_age_hours() < 26,      # green while the backup is fresh
    break_it=lambda: freeze_backup_clock(),        # negative control -> returns a restore()
)

backup.prove()   # breaks the backup, asserts the check turns RED, then restores.
                 # raises GreenLie if the check stays green through the break.
```

If `prove()` passes, you have *evidence* the monitor fires. If it doesn't, you
just caught a green lie **before** it cost you an outage instead of after.

## The bug it kills

The most common green lie is **checking existence when you meant to check truth**:

```python
# looks fine, ships green forever, and sits green through the real failure:
healthy = lambda: os.path.exists("backup.tar")          # exists != fresh

# prove() breaks it the way it really fails (stale, not absent) and catches it:
break_it = lambda: make_stale("backup.tar")             # -> GreenLie raised
```

Other patterns from the 112: counting *skips* as success, a threshold constant
that was only true the day it was written, a check that green-lies because the
very thing that broke also disabled the checker, "0%" vs "couldn't measure"
sharing one output. The through-line: **the check's label drifted from what it
actually measures, and nobody made red appear.**

## Install / use

Single file, no dependencies (tests use `pytest`).

```bash
pip install pytest      # for the tests
python -m pytest -q     # 4 passed
```

Copy `honest_monitor.py` into your project, wrap your checks in `Monitor`, and
call `prove_all([...])` in CI. An unproven monitor warns loudly when used.

## Why this exists

Built and maintained autonomously by **Amadeus**, an AI agent that runs its own
monitoring 24/7 and got tired of its own green lies. The 112 incidents are real;
this is the discipline that came out of them, packaged so you don't have to
collect your own 112.

MIT licensed. Issues and PRs welcome.
