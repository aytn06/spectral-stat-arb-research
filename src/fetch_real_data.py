from __future__ import annotations

"""Download a real large-cap U.S. equity panel for the stat-arb pipeline.

The public repo ships a synthetic benchmark so the methodology is reproducible
without redistributing proprietary data. This script is a local-only helper for
building a real panel from free public web sources and running the same
residualization workflow on actual stocks.

Data source:
- Daily price/volume history from Nasdaq's public historical endpoint

Output schema matches src.data_loader.load_panel_data:
- date
- ticker
- sector
- close
- volume
- benchmark_close
"""

import argparse
import json
import subprocess
import time
from pathlib import Path

import pandas as pd


DEFAULT_OUTPUT = "data/real_us_largecap_panel.csv"
DEFAULT_START = "2019-05-22"
DEFAULT_END = "2025-06-30"
DEFAULT_BENCHMARK = "SPY"

REAL_LARGE_CAP_UNIVERSE = {
    "communication_services": ["GOOGL", "META", "NFLX", "DIS"],
    "consumer": ["WMT", "HD", "MCD", "COST"],
    "financials": ["JPM", "BAC", "GS", "BLK"],
    "healthcare": ["JNJ", "MRK", "ABBV", "PFE"],
    "industrials": ["HON", "CAT", "UPS", "UNP"],
    "technology": ["AAPL", "MSFT", "ORCL", "CSCO"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a real large-cap U.S. equity panel from Nasdaq historical data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK)
    return parser


def nasdaq_asset_class(symbol: str) -> str:
    return "etf" if symbol.upper() == DEFAULT_BENCHMARK else "stocks"


def nasdaq_history_url(symbol: str, start: str, end: str) -> str:
    return (
        "https://api.nasdaq.com/api/quote/"
        f"{symbol}/historical?assetclass={nasdaq_asset_class(symbol)}"
        f"&fromdate={start}&limit=9999&todate={end}"
    )


def parse_nasdaq_number(value: str) -> float:
    return float(value.replace("$", "").replace(",", ""))


def fetch_nasdaq_history(symbol: str, start: str, end: str) -> pd.DataFrame:
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    time.sleep(0.35)
    response = subprocess.run(
        ["curl", "-s", "-L", "-A", user_agent, nasdaq_history_url(symbol, start=start, end=end)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if response.returncode != 0:
        raise RuntimeError(f"curl failed for {symbol}: {response.stderr.strip()}")

    document = json.loads(response.stdout)
    data = document.get("data") or {}
    trades = data.get("tradesTable") or {}
    rows = trades.get("rows") or []
    if not rows:
        raise RuntimeError(f"Empty Nasdaq historical response for {symbol}")

    frame = pd.DataFrame(rows)
    frame = frame.rename(columns={"date": "date", "close": "close", "volume": "volume"})
    frame["date"] = pd.to_datetime(frame["date"], format="%m/%d/%Y")
    frame["close"] = frame["close"].map(parse_nasdaq_number)
    frame["volume"] = frame["volume"].str.replace(",", "", regex=False).astype(float)
    frame = frame[["date", "close", "volume"]].copy()
    return frame.sort_values("date").reset_index(drop=True)


def build_real_panel(start: str, end: str, benchmark: str) -> pd.DataFrame:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)

    benchmark_df = fetch_nasdaq_history(benchmark, start=start, end=end)
    benchmark_df = benchmark_df[(benchmark_df["date"] >= start_ts) & (benchmark_df["date"] <= end_ts)].copy()
    benchmark_df = benchmark_df.rename(columns={"close": "benchmark_close"})[["date", "benchmark_close"]]
    benchmark_dates = benchmark_df["date"].drop_duplicates().sort_values()

    rows: list[pd.DataFrame] = []
    selected_symbols: list[str] = []
    for sector, tickers in REAL_LARGE_CAP_UNIVERSE.items():
        for ticker in tickers:
            hist = fetch_nasdaq_history(ticker, start=start, end=end)
            hist = hist[(hist["date"] >= start_ts) & (hist["date"] <= end_ts)].copy()
            hist["ticker"] = ticker
            hist["sector"] = sector
            merged = benchmark_df.merge(hist, on="date", how="left")
            # Require a full history over the selected benchmark window.
            if merged[["close", "volume"]].isna().any().any():
                raise RuntimeError(
                    f"{ticker} does not have a complete Nasdaq history from {start} to {end}."
                )
            rows.append(merged[["date", "ticker", "sector", "close", "volume", "benchmark_close"]])
            selected_symbols.append(ticker)

    panel = pd.concat(rows, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True)
    expected_rows = len(benchmark_dates) * len(selected_symbols)
    if len(panel) != expected_rows:
        raise RuntimeError(
            f"Unexpected panel size: got {len(panel)} rows, expected {expected_rows}."
        )
    return panel


def main() -> None:
    args = build_parser().parse_args()
    panel = build_real_panel(start=args.start, end=args.end, benchmark=args.benchmark)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output, index=False)
    print(
        f"Wrote {len(panel):,} rows for {panel['ticker'].nunique()} tickers "
        f"from {panel['date'].min().date()} to {panel['date'].max().date()} "
        f"to {output}"
    )


if __name__ == "__main__":
    main()
