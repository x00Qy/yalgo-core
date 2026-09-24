# yalgo-core

**The shared statistics and transaction-cost package behind the published
[`forced-flows`](https://github.com/x00Qy/forced-flows-public) research.** It exists so that two repositories compute a
p-value and a cost floor with the *same* code rather than two drifting copies of it.

**It is installed, not run.** No scripts, no data files, no network calls. Everything it exports
is either pure arithmetic or a rate table written into the source with its provenance.

```bash
pip install -e .
```

## What is in it

| module | what it is |
|---|---|
| `yalgo_core.stats_utils` | Welch t-test, one-sample t-test, two-proportion z-test, Wilson interval, exact binomial p-value, binomial log-pmf. All return `(statistic, p_value)` tuples. |
| `yalgo_core.equity_cost_model` | Round-trip cost for cash-segment **delivery equity**, in basis points of notional and in rupees, date-keyed across statutory rate eras, plus the fixed-rupee CDSL/DP charge. |
| `yalgo_core.py.typed` | PEP 561 marker — the package ships type information. |

`stats_utils` carries its own git history from the research repository it was extracted from,
including the commit that fixed a real bug in it: t-statistics were being converted to p-values
through the standard normal CDF rather than the Student-t CDF, which overstated significance on
small samples. That history is the reason the extraction preserved commits rather than starting
clean.

## Two things about the cost model, stated up front

**The rates are sourced to a broker-published schedule, not to a statutory instrument.** Every
rate era carries a source and a fetch date, and at present **none carries `verified=True`** —
none has been confirmed against a primary regulatory document, so none should be quoted as though
it had been.

**The zero-brokerage default is a single broker's schedule, not a market fact.** Delivery
brokerage is zero there and is not zero at most Indian brokers. Any viability claim built on the
default is a claim about that kind of account and has to say so.

**`rate_on()` raises rather than guessing** for a date outside its sourced range. That is the
design, not a limitation to work around: a cost model that silently extrapolates is how a cost
floor ends up wrong by a factor of two, which is exactly what happened in the research that
produced this package and is recorded in its addendum chain.

## Units

All statutory charges are percentages of turnover, so they are **constant in basis points of
notional** whatever the scrip trades at. **DP charges are not** — they are a fixed rupee amount
per scrip per sell, so in bps they fall as position size rises, and any bar expressed in bps
therefore moves with position size. The module docstring sets this out in full; it is the single
easiest thing to get wrong when quoting a cost floor.

## Type checking

```bash
pip install mypy scipy-stubs
mypy --strict yalgo_core
```

`scipy-stubs` is required for a clean run. The package ships `py.typed`, so consumers get its
types — but mypy cannot follow a PEP 660 editable install, so a consumer repository additionally
needs `MYPYPATH` pointed at this directory. Without it, consumers see `import-not-found` for
`yalgo_core`; **that error is expected and is not a defect.**

See [`SETUP.md`](SETUP.md) for the pinned versions, what else was tested against them, and the
full type-checking notes.

## Licence and data

MIT for the code. **It grants no rights over market data**, and this package contains none — see
[`LICENSE`](LICENSE) for the carve-out and for why the cost model is not an authoritative source.
