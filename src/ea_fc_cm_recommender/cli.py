"""Command-line interface for project workflows."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ea_fc_cm_recommender.pipeline import build_processed_dataset


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the processed EA FC player Parquet dataset."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the raw player CSV.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path for the processed Parquet file.",
    )   
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the processed-data build command."""
    args = _build_parser().parse_args(argv)

    try:
        output_path = build_processed_dataset(args.input, args.output)
    except (FileNotFoundError, OSError, ValueError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1

    print(f"Created processed dataset: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
