PYTHON ?= python3
VENV ?= .venv

.PHONY: setup test sample-data backtest plots artifacts

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

sample-data:
	$(PYTHON) -m src.sample_data

backtest:
	$(PYTHON) -m src.run_backtest

plots:
	$(PYTHON) -m src.make_plots

artifacts:
	$(PYTHON) -m src.generate_research_artifacts
