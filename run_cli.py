# I acknowledge the use of Google Gemini (2026, Google, https://gemini.google.com/) to review a draft of my work and provide feedback.
"""Entry point for running the StockFlow text-based CLI application."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.cli import StockFlowCLI
from src.manager import DEFAULT_INVENTORY_PATH


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the StockFlow CLI launcher."""
    parser = argparse.ArgumentParser(
        description="StockFlow — Text-Based Inventory & Stock Control CLI"
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help=(
            "Path to the JSON inventory file "
            f"(default: {DEFAULT_INVENTORY_PATH.as_posix()})"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch the interactive StockFlow CLI application."""
    args = parse_args(argv)
    cli = StockFlowCLI(filepath=args.data)
    cli.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
