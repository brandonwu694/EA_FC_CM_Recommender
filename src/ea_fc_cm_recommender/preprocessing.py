"""Reusable transformations for raw player data."""

import pandas as pd


def normalize_whitespace(series: pd.Series) -> pd.Series:
    """Normalize whitespace in a text series while preserving missing values."""
    return (
        series.astype("string")
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
