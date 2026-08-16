"""End-to-end construction of the processed player dataset."""

from pathlib import Path

import pandas as pd

from ea_fc_cm_recommender.loading import load_raw_players
from ea_fc_cm_recommender.preprocessing import (
    add_league_identity,
    add_player_status_flags,
    normalize_text_columns,
    parse_playstyles,
    select_processed_columns,
    split_player_positions,
    standardize_date_columns,
    standardize_integer_columns,
)
from ea_fc_cm_recommender.validation import (
    validate_preserved_row_count,
    validate_processed_players,
    validate_raw_players,
)


def preprocess_players(raw_players: pd.DataFrame) -> pd.DataFrame:
    """Transform raw players into the validated processed schema."""
    validate_raw_players(raw_players)

    players = normalize_text_columns(raw_players)
    players = standardize_date_columns(players)
    players = standardize_integer_columns(players)
    players = add_league_identity(players)
    players = split_player_positions(players)
    players = parse_playstyles(players)
    players = add_player_status_flags(players)
    players = select_processed_columns(players)

    validate_preserved_row_count(raw_players, players)
    validate_processed_players(players)
    return players


def _validate_parquet_output_path(path: Path) -> Path:
    """Validate and return a Parquet output path."""
    output_path = Path(path)
    if output_path.exists() and not output_path.is_file():
        raise ValueError(f"Parquet output path is not a file: {output_path}")
    if output_path.suffix.lower() != ".parquet":
        raise ValueError(f"Processed dataset must be Parquet: {output_path}")
    return output_path


def build_processed_dataset(raw_path: Path, output_path: Path) -> Path:
    """Load, preprocess, validate, and write the player dataset."""
    parquet_path = _validate_parquet_output_path(output_path)
    raw_players = load_raw_players(raw_path)
    processed_players = preprocess_players(raw_players)

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    processed_players.to_parquet(
        parquet_path,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )
    return parquet_path
