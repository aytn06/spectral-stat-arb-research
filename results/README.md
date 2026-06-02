# Results

This folder has the main benchmark result files:

- `performance_summary.csv`
- `final_performance_summary.csv`
- `model_selection_summary.csv`
- `factor_diagnostics.csv`
- `eigenvalue_filter_diagnostics.csv`
- `residual_quality_series.csv`
- `walkforward_method_comparison.csv`
- `scenario_method_comparison.csv`
- `cost_sensitivity.csv`
- `parameter_sensitivity.csv`
- `regime_summary.csv`
- `public_data_split.csv`
- `validation_window_correlation.csv`
- `validation_window_rmt_filtered_correlation.csv`

The newer diagnostics add two checks that were missing before:

- `walkforward_method_comparison.csv` repeats the raw-PCA-versus-RMT comparison
  across multiple expanding folds instead of relying on a single split.
- `scenario_method_comparison.csv` reruns the core comparison on a null
  benchmark with the residual alpha switched off, so the method has to face a
  cleaner no-edge baseline.

I also kept the original-project summaries here:

- `original_project_performance_summary.csv`
- `original_project_method_summary.csv`
- `original_project_cost_sensitivity.csv`
- `original_historical_performance_summary.csv`
