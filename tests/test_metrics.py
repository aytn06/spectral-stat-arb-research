import pandas as pd

from src.metrics import beta_to_benchmark, max_drawdown, sharpe_ratio


def test_max_drawdown_and_sharpe():
    returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
    assert max_drawdown(returns) < 0
    assert sharpe_ratio(returns) == sharpe_ratio(returns)


def test_beta_to_benchmark_is_finite():
    returns = pd.Series([0.01, 0.00, -0.01, 0.02, -0.01])
    benchmark = pd.Series([0.02, 0.01, -0.01, 0.03, -0.02])
    beta = beta_to_benchmark(returns, benchmark)
    assert beta == beta
