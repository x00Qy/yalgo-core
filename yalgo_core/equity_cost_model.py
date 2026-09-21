r"""
equity_cost_model.py -- retail transaction cost on CASH-SEGMENT DELIVERY EQUITY.

SCOPE. Current-era rates only. Historical viability claims are out of scope;
sourcing the rate history is a separate task if a phase ever needs one.

SOURCE TIER. Every rate here comes from a BROKER-PUBLISHED SCHEDULE (Zerodha),
a secondary source fetched 2026-09-21, and none has been confirmed against the
statutory instrument. Every era carries verified=False accordingly.

BROKERAGE. The zero-brokerage default is a ZERODHA-SPECIFIC ASSUMPTION, not a
market fact. Delivery brokerage is zero on that schedule and is not zero at
most Indian brokers. Any viability claim built on the default is a claim about
a Zerodha account and has to say so.

WHY THAT SCOPE IS SAFE HERE. The forced-flows event study computes GROSS
abnormal returns. Cost enters only as the viability bar, and that bar is
TODAY'S cost -- regime (a) in PAPER_no_alpha_at_retail_cost_v2.md. Nothing in
forced-flows prices a historical trade, so a table that refuses to answer for
pre-2025 dates costs nothing and stops a guessed rate entering a figure.

THE RAISE IS THE POINT, not a limitation to be worked around. `rate_on()`
raises for any date before the earliest sourced era, exactly as
`spot_cost_model.stt_rate_on()` does in P1 -- that function's own docstring
contrasts it with `lot_size.py`, which opens its table at 1900-01-01 and
silently returns an UNVERIFIED tier, and calls that a live trap. This module
does not reproduce the trap.

EVERY RATE CARRIES A SOURCE AND A FETCH DATE, and at present NONE carries
`verified=True` -- none has been confirmed against a primary regulatory
document, so none may be quoted as though it had. When a rate is confirmed
against the statutory instrument, flip that one era and say which document.

=== WHAT IS AND IS NOT A PERCENTAGE OF NOTIONAL ===

All statutory charges here are percentages of turnover, so they are constant in
BASIS POINTS OF NOTIONAL whatever the scrip trades at -- the same property that
makes P1's futures floor index-independent.

DP CHARGES ARE NOT. They are a FIXED RUPEE amount per scrip per sell,
independent of quantity and of notional, so their bps contribution falls as
position size rises. That is why they are a stated parameter rather than a
date-keyed rate: the amount is a BROKER schedule, not a statutory rate, and it
differs between brokers and depositories. Passing it explicitly forces the
caller to say whose schedule they are using.

=== DELIVERY EQUITY IS NOT FUTURES ===

Two differences that matter and are easy to carry across wrongly:

  STT IS CHARGED ON BOTH SIDES for delivery (0.1% buy AND 0.1% sell), against
  the sell side only for futures. A round trip therefore pays it twice, and it
  is by far the dominant term.

  STAMP DUTY IS 0.015% for delivery against 0.002% for futures -- 7.5x -- and
  is still buy-side only.

Do not reuse `spot_cost_model`'s futures rates here. They are a different
schedule for a different segment.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

__all__ = [
    "RateEra", "STT_DELIVERY_BOTH_SIDES", "TXN_NSE_DELIVERY", "SEBI_FEE",
    "STAMP_DELIVERY_BUY", "GST_RATE", "IPFT_NSE", "DpSchedule",
    "ZERODHA_CDSL_2026_09", "rate_on", "EquityCostConfig", "round_trip_cost_rupees",
    "round_trip_cost_bps",
]

# The single fetch behind every statutory rate in this module.
#
# SECONDARY, and labelled so. zerodha.com/charges is a BROKER'S PUBLISHED
# SCHEDULE -- a summary of the statutory rates, not the statutory instrument.
# None of the rates below has been confirmed against the Finance Act, the
# relevant SEBI or exchange circular, or the Indian Stamp Act, so every era
# here carries verified=False. That is the same two-tier convention
# diag_cost_floor_table.py states in P1: PRIMARY means fetched from a primary
# source, SECONDARY means taken from a summary and not yet confirmed.
#
# NOTE A DIVERGENCE, recorded rather than quietly resolved: P1's
# spot_cost_model.py marks its 2026 futures STT era verified=True citing this
# same domain. One of the two is mislabelled. This module takes the
# conservative reading for its own rates and does not reach into P1 to change
# that one.
SOURCE: Final[str] = ("broker-published schedule (Zerodha), secondary source, "
                      "equity delivery (NSE) column")
FETCHED: Final[date] = date(2026, 9, 21)
CITATION: Final[str] = SOURCE + ", fetched " + FETCHED.isoformat()

# The earliest date any table here can answer for. Nothing is claimed before
# it; `rate_on` raises instead of extrapolating backwards.
EARLIEST_SOURCED: Final[date] = date(2026, 9, 21)


@dataclass(frozen=True)
class RateEra:
    """One rate, valid from `effective` until the next era begins.

    Deliberately the same shape as `spot_cost_model.RateEra` so that a future
    task which sources the rate history can add eras here without reshaping
    any caller. It is NOT imported from there: that module is futures-side and
    carries P1-internal dependencies (lot_size, spot_backtest_loop)."""
    effective: date
    rate: float
    provenance: str
    verified: bool


# --- STT: 0.1% on BUY and 0.1% on SELL, i.e. paid twice per round trip ------
# "STT/CTT ... 0.1% on buy & sell" -- SOURCE, FETCHED.
STT_DELIVERY_BOTH_SIDES: Final[tuple[RateEra, ...]] = (
    RateEra(EARLIEST_SOURCED, 0.001, CITATION, verified=False),
)

# --- Exchange transaction charge, NSE cash: 0.00307% of turnover, per leg ---
# "Transaction charges NSE: 0.00307%" -- SOURCE, FETCHED. BSE differs
# (0.00375%) and is deliberately not encoded: this module is NSE-only until a
# BSE figure is needed and sourced.
TXN_NSE_DELIVERY: Final[tuple[RateEra, ...]] = (
    RateEra(EARLIEST_SOURCED, 0.0000307, CITATION, verified=False),
)

# --- SEBI turnover fee: Rs 10 per crore, per leg ---------------------------
# "SEBI charges ₹10 / crore" -- SOURCE, FETCHED. 10 / 1e7 = 1e-6.
SEBI_FEE: Final[tuple[RateEra, ...]] = (
    RateEra(EARLIEST_SOURCED, 0.000001, CITATION, verified=False),
)

# --- Stamp duty: 0.015% of turnover, BUY SIDE ONLY -------------------------
# "Stamp charges 0.015% or ₹1500 / crore on buy side" -- SOURCE, FETCHED.
# Levied under the Indian Stamp Act 1899 as amended; nationally unified from
# 2020-07-01. The pre-unification state-varying regime is NOT encoded.
STAMP_DELIVERY_BUY: Final[tuple[RateEra, ...]] = (
    RateEra(EARLIEST_SOURCED, 0.00015, CITATION, verified=False),
)

# --- NSE Investor Protection Fund Trust: Rs 0.01 per crore, per leg --------
# "Charges for Investor's Protection Fund Trust (IPFT) by NSE -- Equity and
# Futures - ₹0.01 per crore + GST" -- SOURCE, FETCHED. Three orders of
# magnitude below the SEBI fee; included because omitting a known term is how
# a floor gets understated, which is the defect P1's cost model was built to
# stop.
IPFT_NSE: Final[tuple[RateEra, ...]] = (
    RateEra(EARLIEST_SOURCED, 0.000000001, CITATION, verified=False),
)

# --- GST: 18% of (brokerage + SEBI + transaction) --------------------------
# "GST 18% on (brokerage + SEBI charges + transaction charges)" -- SOURCE,
# FETCHED. Note it does NOT apply to STT or to stamp duty.
GST_RATE: Final[float] = 0.18

LEGS: Final[int] = 2


def rate_on(eras: tuple[RateEra, ...], on_date: date) -> RateEra:
    """The era in force on `on_date`.

    RAISES rather than guessing, for any date before the earliest sourced era.
    Same contract as `spot_cost_model.stt_rate_on`. Do not add a fallback
    branch here: a silent pre-table default is the trap this module exists to
    avoid, and the module docstring's scope line is only true while this
    function refuses."""
    applicable = [e for e in eras if e.effective <= on_date]
    if not applicable:
        raise ValueError(
            f"No sourced delivery-equity rate for {on_date.isoformat()} -- before "
            f"the earliest sourced era ({eras[0].effective.isoformat()}). This "
            f"module encodes CURRENT-ERA RATES ONLY and refuses to extrapolate "
            f"backwards. Sourcing the rate history is a separate task."
        )
    return max(applicable, key=lambda e: e.effective)


@dataclass(frozen=True)
class DpSchedule:
    """Depository-participant charge: a FIXED RUPEE amount per scrip per SELL,
    independent of quantity and of notional.

    Not a date-keyed rate, because it is not a statutory rate -- it is a broker
    schedule, and it differs between brokers and between depositories. The
    caller states which schedule they are using and when it was checked, so a
    figure derived from it can name its source the way every other figure in
    this project's chain must.

    `rupees_per_scrip_per_sell` is the ALL-IN amount including any GST already
    baked into the broker's published number; `gst_included` records whether
    that is so, to stop GST being applied twice."""
    rupees_per_scrip_per_sell: float
    broker: str
    checked_on: date
    gst_included: bool
    breakdown: str = ""


# "DP (Depository participant) charges -- ₹15.34 per scrip (₹3.5 CDSL fee +
# ₹9.5 Zerodha fee + ₹2.34 GST) is charged on the trading account ledger when
# stocks are sold, irrespective of quantity." -- SOURCE, FETCHED.
# The published 15.34 ALREADY INCLUDES its own 2.34 of GST, so gst_included is
# True and `round_trip_cost_rupees` does not gross it up again.
ZERODHA_CDSL_2026_09: Final[DpSchedule] = DpSchedule(
    rupees_per_scrip_per_sell=15.34,
    broker="Zerodha / CDSL",
    checked_on=FETCHED,
    gst_included=True,
    breakdown="3.50 CDSL + 9.50 Zerodha + 2.34 GST",
)


@dataclass(frozen=True)
class EquityCostConfig:
    """Brokerage is a broker choice, not a statutory rate, so it is a field
    rather than a table.

    THE ZERO DEFAULT IS A ZERODHA-SPECIFIC ASSUMPTION, not a market fact. Most
    Indian brokers charge for delivery; Zerodha's published schedule is zero
    ("Free equity delivery ... ₹0 brokerage", CITATION). A full-service broker
    at 0.3% of turnover per leg would add 60 bps to the round trip -- roughly
    2.5x the entire statutory floor computed here -- so a viability claim built
    on this default is a claim about a Zerodha account and must say so."""
    brokerage_per_order_rupees: float = 0.0
    dp: DpSchedule = ZERODHA_CDSL_2026_09


DEFAULT_EQUITY_COST: Final[EquityCostConfig] = EquityCostConfig()


def round_trip_cost_rupees(notional_rupees: float, on_date: date,
                           config: EquityCostConfig = DEFAULT_EQUITY_COST,
                           scrips_sold: int = 1) -> dict[str, float]:
    """Round-trip delivery-equity cost in RUPEES, itemised.

    `notional_rupees` is STATED BY THE CALLER and has no default: there is no
    sensible default position size, and a defaulted notional is how a
    fixed-rupee term silently becomes negligible. Buy and sell notional are
    taken as equal, which is the convention P1 uses for its futures round trip.

    `scrips_sold` multiplies the DP charge only; it is 1 for a single-name
    event study and is exposed so a basket does not understate it."""
    if notional_rupees <= 0:
        raise ValueError(
            f"notional_rupees must be positive, got {notional_rupees}. The DP "
            f"charge is a fixed rupee amount, so its share of cost is "
            f"meaningless without a stated position size."
        )

    stt = 2.0 * notional_rupees * rate_on(STT_DELIVERY_BOTH_SIDES, on_date).rate
    transaction = LEGS * notional_rupees * rate_on(TXN_NSE_DELIVERY, on_date).rate
    sebi = LEGS * notional_rupees * rate_on(SEBI_FEE, on_date).rate
    ipft = LEGS * notional_rupees * rate_on(IPFT_NSE, on_date).rate
    stamp = notional_rupees * rate_on(STAMP_DELIVERY_BUY, on_date).rate
    brokerage = config.brokerage_per_order_rupees * LEGS
    gst = GST_RATE * (brokerage + sebi + transaction)
    dp = config.dp.rupees_per_scrip_per_sell * scrips_sold
    if not config.dp.gst_included:
        dp *= (1.0 + GST_RATE)

    total = stt + transaction + sebi + ipft + stamp + brokerage + gst + dp
    return {
        "stt": stt, "transaction": transaction, "sebi": sebi, "ipft": ipft,
        "stamp": stamp, "brokerage": brokerage, "gst": gst, "dp": dp,
        "total": total,
    }


def round_trip_cost_bps(notional_rupees: float, on_date: date,
                        config: EquityCostConfig = DEFAULT_EQUITY_COST,
                        scrips_sold: int = 1) -> dict[str, float]:
    """The same itemisation in BASIS POINTS OF NOTIONAL.

    Every term except `dp` is constant in bps whatever the notional. `dp` is
    not, and its bps share falls as position size rises -- which is exactly why
    `notional_rupees` must be stated."""
    r = round_trip_cost_rupees(notional_rupees, on_date, config, scrips_sold)
    return {k: v / notional_rupees * 10_000.0 for k, v in r.items()}
