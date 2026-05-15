# Contributing

This repo is organized like a research codebase rather than a generic Python package. The highest-value contributions improve reproducibility, diagnostics, or the clarity of the public artifact pack.

## Workflow

```bash
python -m src.sample_data
python -m src.run_backtest
python -m src.generate_research_artifacts
pytest
```

## Guardrails

- weight application should remain one day delayed relative to the signal timestamp
- public-benchmark model selection should remain validation-only
- original-project summaries should stay clearly labeled as preserved summaries, not reproduced benchmark outputs

## Good Contributions

- cleaner portfolio diagnostics
- tighter tests around factor-count selection and beta neutrality
- better explanations of why the RMT sleeve behaves differently from naive PCA
- recovered original-project evidence artifacts
