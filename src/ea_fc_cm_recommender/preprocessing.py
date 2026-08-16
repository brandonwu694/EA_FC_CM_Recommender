"""Reusable transformations for raw player data."""

import pandas as pd


EXCLUDED_COLUMNS = (
    "work_rate",
    "nation_team_id",
    "nation_position",
    "nation_jersey_number",
    "player_tags",
    "club_loaned_from",
)


def normalize_whitespace(series: pd.Series) -> pd.Series:
    """Normalize whitespace in a text series while preserving missing values."""
    return (
        series.astype("string")
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def add_loan_status(players: pd.DataFrame) -> pd.DataFrame:
    """Add whether each player is currently on loan."""
    if "club_loaned_from" not in players.columns:
        raise ValueError("Expected column is missing: club_loaned_from")

    loan_parent = normalize_whitespace(players["club_loaned_from"])
    is_on_loan = loan_parent.notna() & loan_parent.ne("")
    return players.assign(is_on_loan=is_on_loan.astype(bool))


def add_goalkeeper_status(players: pd.DataFrame) -> pd.DataFrame:
    """Add whether each player's primary position is goalkeeper."""
    if "player_positions" not in players.columns:
        raise ValueError("Expected column is missing: player_positions")

    positions = normalize_whitespace(players["player_positions"])
    if positions.isna().any() or positions.eq("").any():
        raise ValueError("player_positions contains missing or empty values")

    primary_position = positions.str.split(",").str[0].str.strip()
    return players.assign(is_goalkeeper=primary_position.eq("GK").astype(bool))


def add_free_agent_status(players: pd.DataFrame) -> pd.DataFrame:
    """Add whether each player has no current club."""
    if "club_name" not in players.columns:
        raise ValueError("Expected column is missing: club_name")

    club_names = normalize_whitespace(players["club_name"])
    is_free_agent = club_names.isna() | club_names.eq("")
    return players.assign(is_free_agent=is_free_agent.astype(bool))


def add_player_status_flags(players: pd.DataFrame) -> pd.DataFrame:
    """Add loan, goalkeeper, and free-agent status flags."""
    players = add_loan_status(players)
    players = add_goalkeeper_status(players)
    return add_free_agent_status(players)


def drop_unused_columns(players: pd.DataFrame) -> pd.DataFrame:
    """Remove raw columns excluded from the processed player schema."""
    missing_columns = [
        column for column in EXCLUDED_COLUMNS if column not in players.columns
    ]
    if missing_columns:
        raise ValueError(f"Expected columns are missing: {missing_columns}")
    if "is_on_loan" not in players.columns:
        raise ValueError(
            "is_on_loan must be derived before dropping club_loaned_from"
        )

    return players.drop(columns=list(EXCLUDED_COLUMNS))
