from __future__ import annotations

import argparse

from .build_reports import main as build_reports_main


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Build the plotting and report files for the stat-arb project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )


def main() -> None:
    build_parser().parse_args()
    build_reports_main()


if __name__ == "__main__":
    main()
