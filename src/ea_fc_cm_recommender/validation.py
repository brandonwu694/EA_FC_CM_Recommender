"""Validation rules for raw and processed player data."""

from collections.abc import Iterable

import pandas as pd

from ea_fc_cm_recommender.league_mappings import (
    LEAGUE_COUNTRY_BY_ID,
    LEAGUE_DISPLAY_SEPARATOR,
)
from ea_fc_cm_recommender.schema import (
    BOOLEAN_COLUMNS,
    DATE_COLUMNS,
    DETAILED_ATTRIBUTE_COLUMNS,
    NULLABLE_INTEGER_COLUMNS,
    OUTFIELD_SUMMARY_COLUMNS,
    PROCESSED_LIST_COLUMNS,
    PROCESSED_PLAYER_COLUMNS,
    PROCESSED_STRING_COLUMNS,
    RAW_REQUIRED_COLUMNS,
    REQUIRED_INTEGER_COLUMNS,
    VALID_PLAYER_POSITIONS,
    VALID_PREFERRED_FEET,
    VALID_PLAYSTYLE_NAMES,
)


def require_columns(
    players: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Validate that a dataframe contains the required columns."""
    missing_columns = [
        column for column in required_columns if column not in players.columns
    ]
    if missing_columns:
        raise ValueError(f"Required columns are missing: {missing_columns}")


def _validate_non_empty(players: pd.DataFrame) -> None:
    if players.empty:
        raise ValueError("Player dataset has no rows")


def _validate_unique_column_labels(players: pd.DataFrame) -> None:
    duplicate_columns = players.columns[players.columns.duplicated()].tolist()
    if duplicate_columns:
        raise ValueError(f"Duplicate column labels: {duplicate_columns}")


def _numeric_integer_values(series: pd.Series) -> pd.Series:
    try:
        numeric_values = pd.to_numeric(series, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{series.name} contains non-numeric values"
        ) from error

    if numeric_values.isna().any():
        raise ValueError(f"{series.name} contains missing values")
    if numeric_values.mod(1).ne(0).any():
        raise ValueError(f"{series.name} contains non-integer values")
    return numeric_values


def _validate_player_ids(series: pd.Series) -> None:
    player_ids = _numeric_integer_values(series)
    if player_ids.le(0).any():
        raise ValueError("player_id must contain positive values")
    if player_ids.duplicated().any():
        raise ValueError("player_id must be unique")


def validate_raw_players(players: pd.DataFrame) -> None:
    """Validate the raw player data required by preprocessing."""
    _validate_non_empty(players)
    _validate_unique_column_labels(players)
    require_columns(players, RAW_REQUIRED_COLUMNS)
    _validate_player_ids(players["player_id"])

    snapshot_columns = ("fifa_version", "fifa_update", "fifa_update_date")
    if players.loc[:, list(snapshot_columns)].isna().any().any():
        raise ValueError("Snapshot fields must not contain missing values")


def validate_preserved_row_count(
    raw_players: pd.DataFrame,
    processed_players: pd.DataFrame,
) -> None:
    """Validate that preprocessing preserved every raw player row."""
    if len(raw_players) != len(processed_players):
        raise ValueError(
            "Preprocessing changed the row count: "
            f"raw={len(raw_players)}, processed={len(processed_players)}"
        )


def _validate_exact_processed_columns(players: pd.DataFrame) -> None:
    observed_columns = tuple(players.columns)
    if observed_columns == PROCESSED_PLAYER_COLUMNS:
        return

    missing_columns = [
        column
        for column in PROCESSED_PLAYER_COLUMNS
        if column not in observed_columns
    ]
    unexpected_columns = [
        column
        for column in observed_columns
        if column not in PROCESSED_PLAYER_COLUMNS
    ]
    if missing_columns or unexpected_columns:
        raise ValueError(
            "Processed columns do not match the schema; "
            f"missing={missing_columns}, unexpected={unexpected_columns}"
        )
    raise ValueError("Processed columns are not in the required order")


def _validate_processed_dtypes(players: pd.DataFrame) -> None:
    for column in REQUIRED_INTEGER_COLUMNS:
        if str(players[column].dtype) != "int64":
            raise ValueError(f"{column} must have dtype int64")
    for column in NULLABLE_INTEGER_COLUMNS:
        if str(players[column].dtype) != "Int64":
            raise ValueError(f"{column} must have dtype Int64")
    for column in DATE_COLUMNS:
        if not pd.api.types.is_datetime64_any_dtype(players[column]):
            raise ValueError(f"{column} must have a datetime dtype")
    for column in BOOLEAN_COLUMNS:
        if players[column].dtype != bool:
            raise ValueError(f"{column} must have dtype bool")
    for column in PROCESSED_STRING_COLUMNS:
        if not isinstance(players[column].dtype, pd.StringDtype):
            raise ValueError(f"{column} must have a pandas string dtype")


def _validate_list_column(series: pd.Series) -> None:
    invalid_values = series.map(
        lambda value: not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
    )
    if invalid_values.any():
        raise ValueError(f"{series.name} must contain lists of strings")


def _validate_range(
    players: pd.DataFrame,
    columns: Iterable[str],
    minimum: int,
    maximum: int,
) -> None:
    for column in columns:
        invalid_values = players[column].notna() & ~players[column].between(
            minimum,
            maximum,
        )
        if invalid_values.any():
            raise ValueError(
                f"{column} must be between {minimum} and {maximum}"
            )


def _validate_non_negative(
    players: pd.DataFrame,
    columns: Iterable[str],
) -> None:
    for column in columns:
        if players[column].dropna().lt(0).any():
            raise ValueError(f"{column} must be non-negative")


def _validate_positive(
    players: pd.DataFrame,
    columns: Iterable[str],
) -> None:
    for column in columns:
        if players[column].dropna().le(0).any():
            raise ValueError(f"{column} must contain positive values")


def _validate_text_values(players: pd.DataFrame) -> None:
    required_text = (
        "short_name",
        "long_name",
        "nationality_name",
        "primary_position",
        "preferred_foot",
    )
    for column in required_text:
        if players[column].isna().any() or players[column].eq("").any():
            raise ValueError(f"{column} must contain non-empty values")

    for column in PROCESSED_STRING_COLUMNS:
        values = players[column].dropna()
        normalized = (
            values.str.replace("\u00a0", " ", regex=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        if values.ne(normalized).any():
            raise ValueError(f"{column} contains non-normalized whitespace")

    observed_feet = set(players["preferred_foot"])
    unknown_feet = sorted(observed_feet - VALID_PREFERRED_FEET)
    if unknown_feet:
        raise ValueError(f"Unknown preferred_foot values: {unknown_feet}")


def _validate_positions(players: pd.DataFrame) -> None:
    unknown_primary = sorted(
        set(players["primary_position"]) - VALID_PLAYER_POSITIONS
    )
    if unknown_primary:
        raise ValueError(f"Unknown primary positions: {unknown_primary}")

    for primary, secondary in zip(
        players["primary_position"],
        players["secondary_positions"],
        strict=True,
    ):
        unknown_secondary = sorted(set(secondary) - VALID_PLAYER_POSITIONS)
        if unknown_secondary:
            raise ValueError(
                f"Unknown secondary positions: {unknown_secondary}"
            )
        if len(secondary) != len(set(secondary)):
            raise ValueError("secondary_positions contains duplicates")
        if primary in secondary:
            raise ValueError(
                "primary_position must not appear in secondary_positions"
            )


def _validate_playstyles(players: pd.DataFrame) -> None:
    for playstyles in players["playstyles"]:
        if len(playstyles) != len(set(playstyles)):
            raise ValueError("playstyles contains duplicates")

        unknown_names = sorted(
            {
                playstyle.removesuffix("+")
                for playstyle in playstyles
            }
            - VALID_PLAYSTYLE_NAMES
        )
        if unknown_names:
            raise ValueError(f"Unknown PlayStyle names: {unknown_names}")


def _validate_consistent_mapping(
    players: pd.DataFrame,
    key: str,
    dependent_columns: Iterable[str],
) -> None:
    identified_players = players.dropna(subset=[key])
    for column in dependent_columns:
        value_counts = identified_players.groupby(key)[column].nunique(
            dropna=False
        )
        inconsistent_ids = value_counts[value_counts.gt(1)].index.tolist()
        if inconsistent_ids:
            raise ValueError(
                f"{key} maps to inconsistent {column} values: "
                f"{inconsistent_ids}"
            )


def _validate_league_identity(players: pd.DataFrame) -> None:
    observed_ids = set(players["league_id"].dropna().astype(int))
    unknown_ids = sorted(observed_ids - set(LEAGUE_COUNTRY_BY_ID))
    if unknown_ids:
        raise ValueError(f"Unknown league_id values: {unknown_ids}")

    expected_countries = players["league_id"].map(
        LEAGUE_COUNTRY_BY_ID
    ).astype("string")
    expected_display_names = expected_countries.str.cat(
        players["league_name"],
        sep=LEAGUE_DISPLAY_SEPARATOR,
    )

    country_matches = players["league_country"].eq(expected_countries) | (
        players["league_country"].isna() & expected_countries.isna()
    )
    if not country_matches.all():
        raise ValueError("league_country does not match league_id")

    display_matches = players["league_display_name"].eq(
        expected_display_names
    ) | (
        players["league_display_name"].isna()
        & expected_display_names.isna()
    )
    if not display_matches.all():
        raise ValueError(
            "league_display_name does not match league country and name"
        )


def _validate_missingness_equivalence(
    players: pd.DataFrame,
    columns: Iterable[str],
    expected_missing: pd.Series,
    rule: str,
) -> None:
    for column in columns:
        if not players[column].isna().eq(expected_missing).all():
            raise ValueError(f"{column} violates structural-null rule: {rule}")


def _validate_structural_nulls(players: pd.DataFrame) -> None:
    is_on_loan = players["is_on_loan"]
    is_goalkeeper = players["is_goalkeeper"]
    is_free_agent = players["is_free_agent"]

    if (is_on_loan & is_free_agent).any():
        raise ValueError("A player cannot be both on loan and a free agent")
    if not is_goalkeeper.eq(players["primary_position"].eq("GK")).all():
        raise ValueError("is_goalkeeper must match primary_position")

    free_agent_fields = (
        "club_team_id",
        "club_name",
        "club_position",
        "club_contract_valid_until_year",
        "league_id",
        "league_name",
        "league_level",
        "league_country",
        "league_display_name",
    )
    _validate_missingness_equivalence(
        players,
        free_agent_fields,
        is_free_agent,
        "missing exactly for free agents",
    )
    _validate_missingness_equivalence(
        players,
        ("club_joined_date",),
        is_on_loan | is_free_agent,
        "missing exactly for loans and free agents",
    )
    _validate_missingness_equivalence(
        players,
        ("release_clause_eur",),
        is_on_loan | is_free_agent | players["value_eur"].eq(0),
        "missing exactly for loans, free agents, and zero-value players",
    )
    _validate_missingness_equivalence(
        players,
        ("goalkeeping_speed",),
        ~is_goalkeeper,
        "missing exactly for outfield players",
    )
    _validate_missingness_equivalence(
        players,
        OUTFIELD_SUMMARY_COLUMNS,
        is_goalkeeper,
        "missing exactly for goalkeepers",
    )


def _validate_dates(players: pd.DataFrame) -> None:
    if players["fifa_update_date"].isna().any():
        raise ValueError("fifa_update_date must not contain missing values")
    if players["dob"].isna().any():
        raise ValueError("dob must not contain missing values")
    if players["dob"].gt(players["fifa_update_date"]).any():
        raise ValueError("dob must not be after fifa_update_date")

    joined_after_update = players["club_joined_date"].notna() & players[
        "club_joined_date"
    ].gt(players["fifa_update_date"])
    if joined_after_update.any():
        raise ValueError("club_joined_date must not be after fifa_update_date")

    contract_before_update = players[
        "club_contract_valid_until_year"
    ].notna() & players["club_contract_valid_until_year"].lt(
        players["fifa_update_date"].dt.year
    )
    if contract_before_update.any():
        raise ValueError(
            "club contract year must not be before the update year"
        )


def validate_processed_players(players: pd.DataFrame) -> None:
    """Validate the final processed player dataset."""
    _validate_non_empty(players)
    _validate_unique_column_labels(players)
    _validate_exact_processed_columns(players)
    _validate_processed_dtypes(players)

    _validate_player_ids(players["player_id"])
    _validate_positive(
        players,
        (
            "fifa_version",
            "fifa_update",
            "nationality_id",
            "club_team_id",
            "league_id",
        ),
    )
    for column in PROCESSED_LIST_COLUMNS:
        _validate_list_column(players[column])

    _validate_text_values(players)
    _validate_positions(players)
    _validate_playstyles(players)

    _validate_range(players, ("overall", "potential"), 1, 99)
    _validate_range(players, DETAILED_ATTRIBUTE_COLUMNS, 1, 99)
    _validate_range(
        players,
        (*OUTFIELD_SUMMARY_COLUMNS, "goalkeeping_speed"),
        1,
        99,
    )
    _validate_range(players, ("weak_foot", "skill_moves"), 1, 5)
    _validate_range(players, ("international_reputation",), 1, 5)
    _validate_range(players, ("league_level",), 1, 10)
    _validate_range(players, ("age",), 15, 60)
    _validate_range(players, ("height_cm",), 100, 250)
    _validate_range(players, ("weight_kg",), 30, 200)
    _validate_non_negative(
        players,
        ("value_eur", "wage_eur", "release_clause_eur"),
    )
    
    if players["potential"].lt(players["overall"]).any():
        raise ValueError("potential must be greater than or equal to overall")

    _validate_consistent_mapping(
        players,
        "club_team_id",
        ("club_name", "league_id"),
    )
    _validate_consistent_mapping(
        players,
        "league_id",
        (
            "league_name",
            "league_level",
            "league_country",
            "league_display_name",
        ),
    )
    _validate_league_identity(players)
    _validate_structural_nulls(players)
    _validate_dates(players)
