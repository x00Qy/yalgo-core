"""yalgo_core -- shared statistics and transaction-cost code.

Shared between the published `forced-flows` research and the options-research repository this package was extracted from.
That second repository is referred to below as "the options-research
repository"; it is not public, and nothing here depends on it.

WHAT IS HERE AND WHY ONLY THIS

  stats_utils         moved from the options-research repository with its git
                      history, byte-identical. Depends on nothing in it.
  equity_cost_model   new. Cash-segment delivery-equity costs, current era
                      only, every rate carrying a source and a fetch date.

WHAT IS DELIBERATELY NOT HERE

  spot_cost_model     it does NOT move. Its transitive dependency closure
                      inside the options-research repository is seven
                      modules -- lot_size,
                      spot_backtest_loop, daily_history,
                      real_nifty_spot_data_source, strategy_interface,
                      option_types and time_utils -- so extracting it would
                      either drag most of that repository's engine into
                      this package or invert the dependency and make this
                      package unusable from an unrelated project. lot_size is
                      NIFTY-only by design
                      and raises on any other underlying, which is the
                      opposite of what belongs in a package shared with an
                      equity project.

                      Measured, not assumed: see the extraction report.
"""
