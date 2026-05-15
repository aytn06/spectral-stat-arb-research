from __future__ import annotations

import argparse

from .generate_research_artifacts import main as generate_artifacts_main


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Generate the plotting/report artifact pack for the stat-arb project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )


def main() -> None:
    build_parser().parse_args()
    generate_artifacts_main()


if __name__ == "__main__":
    main()
