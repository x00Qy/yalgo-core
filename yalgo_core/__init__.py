"""yalgo_core -- shared engine for YALGO Quant Labs.

WHAT IS HERE AND WHY ONLY THIS

  stats_utils         moved from P1 (option-trading-bot-main) with its git
                      history, byte-identical. Depends on nothing in P1.
  equity_cost_model   new. Cash-segment delivery-equity costs, current era
                      only, every rate carrying a source and a fetch date.

WHAT IS DELIBERATELY NOT HERE

  spot_cost_model     it does NOT move. Its transitive dependency closure
                      inside P1 is seven modules -- lot_size,
                      spot_backtest_loop, daily_history,
                      real_nifty_spot_data_source, strategy_interface,
                      option_types and time_utils -- so extracting it would
                      either drag most of P1's engine into this package or
                      invert the dependency and make this package unusable
                      from a non-P1 project. lot_size is NIFTY-only by design
                      and raises on any other underlying, which is the
                      opposite of what belongs in a package shared with an
                      equity project.

                      Measured, not assumed: see the extraction report.
"""
