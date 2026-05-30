# Original Georgia Tech Project Summary

This note records the original Georgia Tech stat-arb project behind the repo.

The original historical equity panel came from a confidential university
database, so I cannot redistribute it here. The GitHub repo uses a structured
benchmark and a public large-cap extension so the method can still be inspected
and rerun.

The saved project materials report the following historical comparison:

- raw PCA residualization: Sharpe around `0.8`
- RMT-filtered residualization: Sharpe around `1.3`
- max drawdown around `8%`
- `|beta_SPY| < 0.05`

The intended comparison was apples-to-apples. Both versions used the same
historical universe, dates, signal construction, constraints, rebalance
schedule, and `5` bps one-way cost assumption. The point of the comparison was
to isolate the residualization step.

So this repo should be read in two layers:

- the runnable repo shows the method
- this note preserves the original historical summary

Supporting files:

- [original_project_evidence/original_historical_run_summary.md](original_project_evidence/original_historical_run_summary.md)
- [original_project_evidence/original_results_table.md](original_project_evidence/original_results_table.md)
- [../results/original_historical_performance_summary.csv](../results/original_historical_performance_summary.csv)
