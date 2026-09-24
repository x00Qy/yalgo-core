# SETUP — yalgo-core

Statistics helpers and transaction-cost models, shared between the published
[`forced-flows`](https://github.com/x00Qy/forced-flows-public) research and the options-research
repository this package was extracted from.

**This package is normally installed, not run.** It has no scripts and no data.

---

## Python version

**3.10 or newer.** `pyproject.toml` declares `requires-python = ">=3.10"`.
Verified on **CPython 3.13.6** (Windows), which is what every committed result was produced with.

## Install

From a clone of this repository:

```bash
pip install -e .
```

Or, from a consumer repository checked out beside it:

```bash
pip install -e ../yalgo-core
```

`-e` (editable, PEP 660) is deliberate: the consumers are sibling working copies, and an editable
install means a change here is visible to them without reinstalling.

That command resolves this package's dependencies from `pyproject.toml`. `requirements.txt` holds
the same set with exact pins and exists so the pinned versions are visible and so
`pip install -r requirements.txt` works standalone.

```bash
pip install -r requirements.txt   # numpy==2.4.6, scipy==1.18.0
```

**The pins are what the dependent repositories' committed results were produced with. They are not
the only versions that work, and that was tested rather than assumed.** A clean virtualenv
resolving **numpy 2.5.3 and scipy 1.18.1** — both newer than the pins — reproduced every committed
result in both consumer repositories byte-identically apart from the run timestamp
(verified 2026-09-22).
So the pins are known-good rather than load-bearing, and a resolver that picks something newer is
not on its own a reason to distrust a figure.

| package | pinned | also verified |
|---|---|---|
| numpy | 2.4.6 | 2.5.3 |
| scipy | 1.18.0 | 1.18.1 |
| pandas *(consumers only)* | 3.0.5 | 3.0.6 |

**Nothing depends on this repository sitting at any particular path.** The consumer repositories'
error messages name a path only because it is where it sat on the machine this was developed on;
install from wherever your clone actually is.

## Verify the install

```bash
python -c "from yalgo_core.stats_utils import welch_t_test; print('ok')"
python -c "from yalgo_core.equity_cost_model import round_trip_cost_bps; print('ok')"
```

Both should print `ok`. Each consumer repository wraps its import so that a missing install
raises with the fix rather than a bare `ModuleNotFoundError`.

## Data files

**None.** This package contains no data and reads no files. Everything it exports is either pure
arithmetic or a rate table written into the source with its provenance.

## What is in here

| module | what it is |
|---|---|
| `yalgo_core/stats_utils.py` | Welch t-test, one-sample t, two-proportion z, Wilson CI, exact binomial p, log-pmf. Moved from the options-research repository this package was extracted from, with its git history preserved, byte-identical. |
| `yalgo_core/equity_cost_model.py` | delivery-equity round-trip cost in bps and rupees, date-keyed across five statutory rate eras, plus CDSL/DP charges. |
| `yalgo_core/py.typed` | PEP 561 marker — this package ships type information. |

**Every rate era in `equity_cost_model.py` carries `verified=False` except where stated, and the
citation is a broker-published schedule rather than a statutory gazette.** `rate_on()` raises
rather than guessing for a date before the earliest sourced era. That is deliberate: a cost model
that silently extrapolates is how a cost floor becomes wrong by a factor of two, which is what
happened in the options-research repository this package was extracted from and is recorded in its
addendum chain.

## Type checking

```bash
pip install mypy scipy-stubs
mypy --strict yalgo_core
```

**`scipy-stubs` is required for a clean run, and this was got wrong first.** Without it,
`mypy --strict yalgo_core` reports one error — `Library stubs not installed for "scipy"` at
`stats_utils.py:24`. With it: `Success: no issues found in 3 source files`. Verified 2026-09-22.

The obvious alternative — adding `# type: ignore[import-untyped]` to the scipy import, as the
consumer repositories do — **is deliberately NOT taken here.** The repository this file was moved
from has a committed claim that it is *byte-identical* to the version it replaced, and editing it
would make that claim false. The stub package is the fix that keeps it true.

This package ships `py.typed`, so consumers get its types — **but only if mypy can find it**, and
mypy **cannot follow a PEP 660 editable install**. In the consumer repos that means:

```bash
MYPYPATH=/path/to/yalgo-core mypy --strict <files>
```

Without `MYPYPATH`, consumers see `import-not-found` for `yalgo_core`. **That error is expected
and is not a defect** — verified 2026-09-22 that setting `MYPYPATH` resolves it and the check
passes clean.

## Consumers

| repo | imports | via |
|---|---|---|
| [`forced-flows`](https://github.com/x00Qy/forced-flows-public) | `yalgo_core.equity_cost_model` | `src/require_yalgo_core.py`, a guard that turns a missing install into instructions |
| the options-research repository this package was extracted from *(not public)* | `yalgo_core.stats_utils` | a shim module, so its existing import lines are unchanged |

Changing a public signature here breaks both. There is no deprecation process; the repositories are
developed together.
