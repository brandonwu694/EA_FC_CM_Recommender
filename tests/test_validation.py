import pandas as pd
import pytest

from ea_fc_cm_recommender.schema import (
    BOOLEAN_COLUMNS,
    NULLABLE_INTEGER_COLUMNS,
    OUTFIELD_SUMMARY_COLUMNS,
    PROCESSED_PLAYER_COLUMNS,
    PROCESSED_STRING_COLUMNS,
    RAW_REQUIRED_COLUMNS,
    REQUIRED_INTEGER_COLUMNS,
)
from ea_fc_cm_recommender.validation import (
    validate_preserved_row_count,
    validate_processed_players,
    validate_raw_players,
)


def _valid_raw_players() -> pd.DataFrame:
    players = pd.DataFrame(
        {column: [1, 2] for column in RAW_REQUIRED_COLUMNS}
    )
    players["player_id"] = [1, 2]
    players["fifa_version"] = [26, 26]
    players["fifa_update"] = [4, 4]
    players["fifa_update_date"] = ["2025-09-19", "2025-09-19"]
    return players


def _valid_processed_players() -> pd.DataFrame:
    data = {
        column: pd.Series([50, 50], dtype="int64")
        for column in REQUIRED_INTEGER_COLUMNS
    }
    data.update(
        {
            column: pd.Series([pd.NA, pd.NA], dtype="Int64")
            for column in NULLABLE_INTEGER_COLUMNS
        }
    )
    data.update(
        {
            column: pd.Series(["value", "value"], dtype="string")
            for column in PROCESSED_STRING_COLUMNS
        }
    )
    data.update(
        {
            column: pd.Series([False, False], dtype=bool)
            for column in BOOLEAN_COLUMNS
        }
    )

    data.update(
        {
            "player_id": pd.Series([1, 2], dtype="int64"),
            "fifa_version": pd.Series([26, 26], dtype="int64"),
            "fifa_update": pd.Series([4, 4], dtype="int64"),
            "fifa_update_date": pd.to_datetime(
                ["2025-09-19", "2025-09-19"]
            ),
            "short_name": pd.Series(["Goalkeeper", "Striker"], dtype="string"),
            "long_name": pd.Series(
                ["Goalkeeper Example", "Striker Example"],
                dtype="string",
            ),
            "age": pd.Series([25, 30], dtype="int64"),
            "dob": pd.to_datetime(["2000-01-01", "1995-01-01"]),
            "height_cm": pd.Series([190, 180], dtype="int64"),
            "weight_kg": pd.Series([85, 75], dtype="int64"),
            "nationality_id": pd.Series([14, 14], dtype="int64"),
            "nationality_name": pd.Series(
                ["England", "England"],
                dtype="string",
            ),
            "club_team_id": pd.Series([100, 101], dtype="Int64"),
            "club_name": pd.Series(["Club One", "Club Two"], dtype="string"),
            "club_position": pd.Series(["GK", "SUB"], dtype="string"),
            "club_joined_date": pd.to_datetime(["2020-07-01", None]),
            "club_contract_valid_until_year": pd.Series(
                [2028, 2027],
                dtype="Int64",
            ),
            "league_id": pd.Series([13, 13], dtype="Int64"),
            "league_name": pd.Series(
                ["Premier League", "Premier League"],
                dtype="string",
            ),
            "league_level": pd.Series([1, 1], dtype="Int64"),
            "league_country": pd.Series(
                ["England", "England"],
                dtype="string",
            ),
            "league_display_name": pd.Series(
                ["England — Premier League", "England — Premier League"],
                dtype="string",
            ),
            "primary_position": pd.Series(["GK", "ST"], dtype="string"),
            "secondary_positions": pd.Series([[], ["RW"]], dtype=object),
            "preferred_foot": pd.Series(["Right", "Left"], dtype="string"),
            "weak_foot": pd.Series([3, 4], dtype="int64"),
            "skill_moves": pd.Series([1, 4], dtype="int64"),
            "international_reputation": pd.Series([2, 3], dtype="int64"),
            "playstyles": pd.Series(
                [["Footwork"], ["Finesse Shot+"]],
                dtype=object,
            ),
            "is_on_loan": pd.Series([False, True], dtype=bool),
            "is_goalkeeper": pd.Series([True, False], dtype=bool),
            "is_free_agent": pd.Series([False, False], dtype=bool),
            "overall": pd.Series([80, 75], dtype="int64"),
            "potential": pd.Series([85, 80], dtype="int64"),
            "value_eur": pd.Series([10_000_000, 5_000_000], dtype="int64"),
            "wage_eur": pd.Series([50_000, 25_000], dtype="int64"),
            "release_clause_eur": pd.Series(
                [20_000_000, pd.NA],
                dtype="Int64",
            ),
            "goalkeeping_speed": pd.Series([50, pd.NA], dtype="Int64"),
        }
    )
    for column in OUTFIELD_SUMMARY_COLUMNS:
        data[column] = pd.Series([pd.NA, 75], dtype="Int64")

    return pd.DataFrame(data).loc[:, list(PROCESSED_PLAYER_COLUMNS)]


def test_validate_raw_players_accepts_valid_input():
    assert validate_raw_players(_valid_raw_players()) is None


def test_validate_raw_players_rejects_missing_required_column():
    players = _valid_raw_players().drop(columns="player_traits")

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['player_traits'\]",
    ):
        validate_raw_players(players)


def test_validate_raw_players_rejects_duplicate_player_ids():
    players = _valid_raw_players()
    players["player_id"] = [1, 1]

    with pytest.raises(ValueError, match="player_id must be unique"):
        validate_raw_players(players)


def test_validate_preserved_row_count_accepts_equal_counts():
    raw_players = pd.DataFrame({"player_id": [1, 2]})
    processed_players = pd.DataFrame({"player_id": [1, 2]})

    assert validate_preserved_row_count(raw_players, processed_players) is None


def test_validate_preserved_row_count_rejects_changed_count():
    raw_players = pd.DataFrame({"player_id": [1, 2]})
    processed_players = pd.DataFrame({"player_id": [1]})

    with pytest.raises(ValueError, match="raw=2, processed=1"):
        validate_preserved_row_count(raw_players, processed_players)


def test_validate_processed_players_accepts_valid_input():
    assert validate_processed_players(_valid_processed_players()) is None


def test_validate_processed_players_rejects_wrong_column_order():
    players = _valid_processed_players()
    reordered = players.loc[:, [*players.columns[1:], players.columns[0]]]

    with pytest.raises(ValueError, match="not in the required order"):
        validate_processed_players(reordered)


def test_validate_processed_players_rejects_wrong_dtype():
    players = _valid_processed_players()
    players["overall"] = players["overall"].astype(float)

    with pytest.raises(ValueError, match="overall must have dtype int64"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_out_of_range_rating():
    players = _valid_processed_players()
    players.at[0, "overall"] = 100

    with pytest.raises(ValueError, match="overall must be between 1 and 99"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_nonpositive_identifier():
    players = _valid_processed_players()
    players.at[0, "club_team_id"] = 0

    with pytest.raises(ValueError, match="club_team_id must contain positive"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_unknown_preferred_foot():
    players = _valid_processed_players()
    players.at[0, "preferred_foot"] = "Both"

    with pytest.raises(ValueError, match="Unknown preferred_foot values"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_potential_below_overall():
    players = _valid_processed_players()
    players.at[0, "potential"] = 79

    with pytest.raises(ValueError, match="potential must be greater"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_invalid_list_value():
    players = _valid_processed_players()
    players.at[0, "playstyles"] = "Footwork"

    with pytest.raises(ValueError, match="playstyles must contain lists"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_unknown_position():
    players = _valid_processed_players()
    players.at[1, "primary_position"] = "UNKNOWN"

    with pytest.raises(ValueError, match="Unknown primary positions"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_free_agent_with_club():
    players = _valid_processed_players()
    players.at[0, "is_free_agent"] = True

    with pytest.raises(ValueError, match="club_team_id violates structural-null"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_goalkeeper_without_speed():
    players = _valid_processed_players()
    players.at[0, "goalkeeping_speed"] = pd.NA

    with pytest.raises(
        ValueError,
        match="goalkeeping_speed violates structural-null",
    ):
        validate_processed_players(players)


def test_validate_processed_players_rejects_loan_with_joined_date():
    players = _valid_processed_players()
    players.at[1, "club_joined_date"] = pd.Timestamp("2022-07-01")

    with pytest.raises(ValueError, match="club_joined_date violates structural-null"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_invalid_release_clause_null():
    players = _valid_processed_players()
    players.at[1, "release_clause_eur"] = 10_000_000

    with pytest.raises(ValueError, match="release_clause_eur violates structural-null"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_inconsistent_club_name():
    players = _valid_processed_players()
    players.at[1, "club_team_id"] = 100

    with pytest.raises(ValueError, match="inconsistent club_name"):
        validate_processed_players(players)


def test_validate_processed_players_rejects_future_joined_date():
    players = _valid_processed_players()
    players.at[0, "club_joined_date"] = pd.Timestamp("2026-01-01")

    with pytest.raises(ValueError, match="club_joined_date must not be after"):
        validate_processed_players(players)
