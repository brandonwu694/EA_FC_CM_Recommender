"""Reusable transformations for raw player data."""

from collections.abc import Iterable

import pandas as pd

from ea_fc_cm_recommender.league_mappings import (
    LEAGUE_COUNTRY_BY_ID,
    LEAGUE_DISPLAY_SEPARATOR,
)
from ea_fc_cm_recommender.schema import (
    EXCLUDED_COLUMNS,
    TEXT_COLUMNS,
    VALID_PLAYER_POSITIONS,
)


def _require_columns(
    players: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Validate that a dataframe contains the required columns."""
    missing_columns = [
        column for column in required_columns if column not in players.columns
    ]
    if missing_columns:
        raise ValueError(f"Required columns are missing: {missing_columns}")


def normalize_whitespace(series: pd.Series) -> pd.Series:
    """Normalize whitespace in a text series while preserving missing values."""
    return (
        series.astype("string")
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def normalize_text_columns(players: pd.DataFrame) -> pd.DataFrame:
    """Normalize whitespace in retained text columns."""
    _require_columns(players, TEXT_COLUMNS)

    normalized_columns = {
        column: normalize_whitespace(players[column])
        for column in TEXT_COLUMNS
    }
    return players.assign(**normalized_columns)


def split_player_positions(players: pd.DataFrame) -> pd.DataFrame:
    """Split ordered player positions into primary and secondary fields."""
    _require_columns(players, ("player_positions",))

    position_values = normalize_whitespace(players["player_positions"])
    if position_values.isna().any() or position_values.eq("").any():
        raise ValueError("player_positions contains missing or empty values")

    position_lists = position_values.str.split(",").map(
        lambda positions: [position.strip() for position in positions]
    )
    if position_lists.map(lambda positions: "" in positions).any():
        raise ValueError("player_positions contains empty position tokens")

    observed_positions = {
        position
        for positions in position_lists
        for position in positions
    }
    unknown_positions = sorted(observed_positions - VALID_PLAYER_POSITIONS)
    if unknown_positions:
        raise ValueError(f"Unknown player positions: {unknown_positions}")

    has_duplicates = position_lists.map(
        lambda positions: len(positions) != len(set(positions))
    )
    if has_duplicates.any():
        raise ValueError("player_positions contains duplicate positions")

    primary_positions = position_lists.str[0].astype("string")
    secondary_positions = position_lists.map(lambda positions: positions[1:])
    return players.assign(
        primary_position=primary_positions,
        secondary_positions=secondary_positions,
    )


def _validate_league_identity_pair(
    league_ids: pd.Series,
    league_names: pd.Series,
) -> None:
    """Validate that league ID and name are present or missing together."""
    id_is_missing = league_ids.isna()
    name_is_missing = league_names.isna() | league_names.eq("")

    if id_is_missing.ne(name_is_missing).any():
        raise ValueError("league_id and league_name must be missing together")


def add_league_identity(players: pd.DataFrame) -> pd.DataFrame:
    """Add league country and a country-qualified display name."""
    _require_columns(players, ("league_id", "league_name"))

    league_names = players["league_name"].astype("string")
    _validate_league_identity_pair(players["league_id"], league_names)

    try:
        league_ids = pd.to_numeric(players["league_id"], errors="raise").astype(
            "Int64"
        )
    except (TypeError, ValueError) as error:
        raise ValueError("league_id contains non-integer values") from error

    mapped_ids = set(LEAGUE_COUNTRY_BY_ID)
    observed_ids = set(league_ids.dropna().astype(int))
    unknown_ids = sorted(observed_ids - mapped_ids)
    if unknown_ids:
        raise ValueError(f"Unknown league_id values: {unknown_ids}")

    league_countries = league_ids.map(LEAGUE_COUNTRY_BY_ID).astype("string")
    display_names = league_countries.str.cat(
        league_names,
        sep=LEAGUE_DISPLAY_SEPARATOR,
    )
    return players.assign(
        league_country=league_countries,
        league_display_name=display_names,
    )


def add_loan_status(players: pd.DataFrame) -> pd.DataFrame:
    """Add whether each player is currently on loan."""
    _require_columns(players, ("club_loaned_from",))

    loan_parent = normalize_whitespace(players["club_loaned_from"])
    is_on_loan = loan_parent.notna() & loan_parent.ne("")
    return players.assign(is_on_loan=is_on_loan.astype(bool))


def add_goalkeeper_status(players: pd.DataFrame) -> pd.DataFrame:
    """Add whether each player's primary position is goalkeeper."""
    _require_columns(players, ("player_positions",))

    positions = normalize_whitespace(players["player_positions"])
    if positions.isna().any() or positions.eq("").any():
        raise ValueError("player_positions contains missing or empty values")

    primary_position = positions.str.split(",").str[0].str.strip()
    return players.assign(is_goalkeeper=primary_position.eq("GK").astype(bool))


def add_free_agent_status(players: pd.DataFrame) -> pd.DataFrame:
    """Add whether each player has no current club."""
    _require_columns(players, ("club_name",))

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
    _require_columns(players, EXCLUDED_COLUMNS)
    if "is_on_loan" not in players.columns:
        raise ValueError(
            "is_on_loan must be derived before dropping club_loaned_from"
        )

    return players.drop(columns=list(EXCLUDED_COLUMNS))
