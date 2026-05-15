from pathlib import Path

from src.data_loader import build_market_panel, load_panel_data


SAMPLE_DATA = Path(__file__).resolve().parents[1] / "data" / "sample_prices.csv"


def test_load_sample_panel():
    df = load_panel_data(str(SAMPLE_DATA))
    assert {"date", "ticker", "sector", "close", "volume", "benchmark_close"}.issubset(df.columns)
    panel = build_market_panel(df)
    assert panel.prices.shape == panel.returns.shape
    assert len(panel.sectors) == panel.prices.shape[1]
