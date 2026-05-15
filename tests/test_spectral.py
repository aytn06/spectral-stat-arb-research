import pandas as pd

from src.spectral import marchenko_pastur_upper_edge, residualize_window


def test_mp_edge_and_residual_shape():
    dates = pd.bdate_range("2024-01-01", periods=100)
    window = pd.DataFrame(
        {
            "A": [0.01 * ((i % 5) - 2) for i in range(100)],
            "B": [0.008 * ((i % 7) - 3) for i in range(100)],
            "C": [0.006 * ((i % 3) - 1) for i in range(100)],
        },
        index=dates,
    )
    sectors = pd.Series({"A": "x", "B": "x", "C": "y"})
    residuals, meta = residualize_window(window, sectors, "rmt", fixed_components=2, min_components=1, max_components=3)
    assert residuals.shape == window.shape
    assert meta["mp_upper_edge"] == marchenko_pastur_upper_edge(3, 100)
