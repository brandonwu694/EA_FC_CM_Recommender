"""Loading utilities for player datasets."""

from pathlib import Path

import pandas as pd


def _validate_raw_csv_path(path: Path) -> Path:
    """Validate and return a raw CSV path."""
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Raw player dataset not found: {dataset_path}"
        )
    if not dataset_path.is_file():
        raise ValueError(f"Raw player dataset is not a file: {dataset_path}")
    if dataset_path.suffix.lower() != ".csv":
        raise ValueError(f"Raw player dataset must be a CSV: {dataset_path}")
    return dataset_path


def load_raw_players(path: Path) -> pd.DataFrame:
    """Load a non-empty raw player CSV from an explicit path."""
    dataset_path = _validate_raw_csv_path(path)

    try:
        players = pd.read_csv(dataset_path, low_memory=False)
    except pd.errors.EmptyDataError as error:
        raise ValueError(
            f"Raw player dataset is empty: {dataset_path}"
        ) from error

    if players.empty:
        raise ValueError(f"Raw player dataset has no rows: {dataset_path}")
    return players
