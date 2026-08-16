import pandas as pd
import pytest

from ea_fc_cm_recommender.preprocessing import (
    _require_columns,
    add_free_agent_status,
    add_goalkeeper_status,
    add_league_identity,
    add_loan_status,
    add_player_status_flags,
    drop_unused_columns,
    normalize_text_columns,
    normalize_whitespace,
    parse_playstyles,
    select_processed_columns,
    split_player_positions,
    standardize_date_columns,
    standardize_integer_columns,
)
from ea_fc_cm_recommender.schema import (
    BOOLEAN_COLUMNS,
    DATE_COLUMNS,
    DETAILED_ATTRIBUTE_COLUMNS,
    EXCLUDED_COLUMNS,
    NULLABLE_INTEGER_COLUMNS,
    PROCESSED_PLAYER_COLUMNS,
    REQUIRED_INTEGER_COLUMNS,
    TEXT_COLUMNS,
    VALID_PLAYER_POSITIONS,
    VALID_PLAYSTYLE_NAMES,
)


def test_normalize_whitespace_collapses_unicode_whitespace():
    values = pd.Series(
        ["  Real   Madrid  ", "Playmaker\u00a0 +", "Line\tBreak\nText"],
        name="text",
    )

    result = normalize_whitespace(values)

    expected = pd.Series(
        ["Real Madrid", "Playmaker +", "Line Break Text"],
        dtype="string",
        name="text",
    )
    pd.testing.assert_series_equal(result, expected)


def test_normalize_whitespace_preserves_missing_values():
    values = pd.Series([None, pd.NA, float("nan")], name="text")

    result = normalize_whitespace(values)

    assert result.isna().all()
    assert result.dtype == pd.StringDtype()


def test_normalize_whitespace_preserves_text_meaning():
    values = pd.Series(
        ["Süper Lig", "1. FC Köln", "Paris Saint-Germain", "D'Alessandro"],
        name="text",
    )

    result = normalize_whitespace(values)

    expected = values.astype("string")
    pd.testing.assert_series_equal(result, expected)


def test_normalize_whitespace_does_not_modify_input():
    values = pd.Series(["  Real   Madrid  "], name="text")
    original = values.copy()

    normalize_whitespace(values)

    pd.testing.assert_series_equal(values, original)


def test_normalize_text_columns_cleans_selected_columns():
    players = pd.DataFrame(
        {
            **{
                column: ["  Example\u00a0  Value  "]
                for column in TEXT_COLUMNS
            },
            "player_id": [1],
        }
    )

    result = normalize_text_columns(players)

    for column in TEXT_COLUMNS:
        assert result.at[0, column] == "Example Value"
        assert result[column].dtype == pd.StringDtype()
    assert result.at[0, "player_id"] == 1


def test_normalize_text_columns_preserves_missing_values_and_input():
    players = pd.DataFrame(
        {column: [None] for column in TEXT_COLUMNS}
    )
    original = players.copy()

    result = normalize_text_columns(players)

    assert result[list(TEXT_COLUMNS)].isna().all().all()
    pd.testing.assert_frame_equal(players, original)


def test_normalize_text_columns_rejects_incomplete_source_schema():
    players = pd.DataFrame(
        {
            column: ["value"]
            for column in TEXT_COLUMNS
            if column != "preferred_foot"
        }
    )

    with pytest.raises(ValueError, match="Required columns are missing"):
        normalize_text_columns(players)


def test_require_columns_reports_all_missing_columns():
    players = pd.DataFrame({"player_id": [1]})

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['club_name', 'league_name'\]",
    ):
        _require_columns(players, ("player_id", "club_name", "league_name"))


def test_standardize_date_columns_converts_dates_and_preserves_missing_values():
    players = pd.DataFrame(
        {
            "fifa_update_date": ["2025-09-19", "2025-09-19"],
            "dob": ["2003-06-29", "1998-07-22"],
            "club_joined_date": ["2023-07-01", None],
            "player_id": [252371, 239053],
        }
    )
    original = players.copy()

    result = standardize_date_columns(players)

    for column in DATE_COLUMNS:
        assert pd.api.types.is_datetime64_any_dtype(result[column])
    assert result.at[0, "fifa_update_date"] == pd.Timestamp("2025-09-19")
    assert result.at[0, "dob"] == pd.Timestamp("2003-06-29")
    assert result.at[0, "club_joined_date"] == pd.Timestamp("2023-07-01")
    assert pd.isna(result.at[1, "club_joined_date"])
    assert result["player_id"].equals(players["player_id"])
    pd.testing.assert_frame_equal(players, original)


def test_standardize_date_columns_rejects_malformed_dates():
    players = pd.DataFrame(
        {
            "fifa_update_date": ["2025-09-19"],
            "dob": ["not-a-date"],
            "club_joined_date": ["2023-07-01"],
        }
    )

    with pytest.raises(ValueError):
        standardize_date_columns(players)


def test_standardize_date_columns_rejects_incomplete_source_schema():
    players = pd.DataFrame(
        {
            "fifa_update_date": ["2025-09-19"],
            "dob": ["2003-06-29"],
        }
    )

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['club_joined_date'\]",
    ):
        standardize_date_columns(players)


def _integer_players() -> pd.DataFrame:
    return pd.DataFrame(
        {
            **{column: ["1", "2"] for column in REQUIRED_INTEGER_COLUMNS},
            **{
                column: ["1.0", None]
                for column in NULLABLE_INTEGER_COLUMNS
            },
            "short_name": ["Player One", "Player Two"],
        }
    )


def test_standardize_integer_columns_applies_dtype_contract():
    players = _integer_players()
    original = players.copy()

    result = standardize_integer_columns(players)

    assert all(
        result[column].dtype == "int64"
        for column in REQUIRED_INTEGER_COLUMNS
    )
    assert all(
        result[column].dtype == "Int64"
        for column in NULLABLE_INTEGER_COLUMNS
    )
    assert result["short_name"].equals(players["short_name"])
    assert pd.isna(result.at[1, "release_clause_eur"])
    pd.testing.assert_frame_equal(players, original)


def test_standardize_integer_columns_rejects_missing_required_values():
    players = _integer_players()
    players.at[0, "overall"] = None

    with pytest.raises(ValueError, match="overall contains missing values"):
        standardize_integer_columns(players)


def test_standardize_integer_columns_rejects_fractional_values():
    players = _integer_players()
    players.at[0, "value_eur"] = "10.5"

    with pytest.raises(ValueError, match="value_eur contains non-integer values"):
        standardize_integer_columns(players)


def test_standardize_integer_columns_rejects_non_numeric_values():
    players = _integer_players()
    players.at[0, "wage_eur"] = "unknown"

    with pytest.raises(ValueError, match="wage_eur contains non-numeric values"):
        standardize_integer_columns(players)


def test_standardize_integer_columns_rejects_incomplete_source_schema():
    players = _integer_players().drop(columns="goalkeeping_speed")

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['goalkeeping_speed'\]",
    ):
        standardize_integer_columns(players)


def test_detailed_attributes_are_required_integer_columns():
    assert set(DETAILED_ATTRIBUTE_COLUMNS).issubset(REQUIRED_INTEGER_COLUMNS)


def test_split_player_positions_preserves_order_and_original_column():
    players = pd.DataFrame(
        {"player_positions": ["RB, RM", "CM,CDM,CAM", "GK"]}
    )
    original = players.copy()

    result = split_player_positions(players)

    assert result["primary_position"].tolist() == ["RB", "CM", "GK"]
    assert result["secondary_positions"].tolist() == [
        ["RM"],
        ["CDM", "CAM"],
        [],
    ]
    assert result["primary_position"].dtype == pd.StringDtype()
    pd.testing.assert_frame_equal(players, original)


@pytest.mark.parametrize("value", [None, "", "   "])
def test_split_player_positions_rejects_missing_or_empty_values(value):
    players = pd.DataFrame({"player_positions": [value]})

    with pytest.raises(ValueError, match="missing or empty values"):
        split_player_positions(players)


def test_split_player_positions_rejects_empty_tokens():
    players = pd.DataFrame({"player_positions": ["RB, , RM"]})

    with pytest.raises(ValueError, match="empty position tokens"):
        split_player_positions(players)


def test_split_player_positions_rejects_unknown_tokens():
    players = pd.DataFrame({"player_positions": ["RB, UNKNOWN"]})

    with pytest.raises(ValueError, match=r"Unknown player positions: \['UNKNOWN'\]"):
        split_player_positions(players)


def test_split_player_positions_rejects_duplicate_tokens():
    players = pd.DataFrame({"player_positions": ["CM, CDM, CM"]})

    with pytest.raises(ValueError, match="duplicate positions"):
        split_player_positions(players)


@pytest.mark.parametrize("position", ["RWB", "LWB", "CF"])
def test_split_player_positions_accepts_supported_unobserved_positions(position):
    players = pd.DataFrame({"player_positions": [position]})

    result = split_player_positions(players)

    assert result.at[0, "primary_position"] == position
    assert result.at[0, "secondary_positions"] == []


def test_valid_player_positions_match_current_supported_schema():
    assert VALID_PLAYER_POSITIONS == {
        "GK",
        "RB",
        "RWB",
        "CB",
        "LB",
        "LWB",
        "CDM",
        "CM",
        "CAM",
        "RM",
        "LM",
        "RW",
        "LW",
        "CF",
        "ST",
    }


def test_parse_playstyles_normalizes_plus_and_preserves_names():
    players = pd.DataFrame(
        {
            "player_traits": [
                " Relentless +,  Low Driven Shot, Tiki Taka ",
                None,
                "   ",
            ],
            "player_id": [1, 2, 3],
        }
    )
    original = players.copy()

    result = parse_playstyles(players)

    assert result["playstyles"].tolist() == [
        ["Relentless+", "Low Driven Shot", "Tiki Taka"],
        [],
        [],
    ]
    assert result["player_id"].tolist() == [1, 2, 3]
    pd.testing.assert_frame_equal(players, original)


def test_parse_playstyles_validates_plus_variant_by_base_name():
    players = pd.DataFrame({"player_traits": ["Unknown Style +"]})

    with pytest.raises(
        ValueError,
        match=r"Unknown PlayStyle names: \['Unknown Style'\]",
    ):
        parse_playstyles(players)


def test_parse_playstyles_rejects_empty_tokens():
    players = pd.DataFrame({"player_traits": ["Rapid, , Quick Step"]})

    with pytest.raises(ValueError, match="empty PlayStyle tokens"):
        parse_playstyles(players)


def test_parse_playstyles_rejects_duplicate_tokens():
    players = pd.DataFrame({"player_traits": ["Rapid, Rapid"]})

    with pytest.raises(ValueError, match="duplicate PlayStyles"):
        parse_playstyles(players)


def test_parse_playstyles_rejects_missing_source_column():
    players = pd.DataFrame({"player_id": [1]})

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['player_traits'\]",
    ):
        parse_playstyles(players)


def test_valid_playstyle_names_use_canonical_base_names():
    assert "Relentless" in VALID_PLAYSTYLE_NAMES
    assert "Relentless+" not in VALID_PLAYSTYLE_NAMES
    assert "Relentless +" not in VALID_PLAYSTYLE_NAMES


def test_add_league_identity_adds_country_first_display_names():
    players = pd.DataFrame(
        {
            "league_id": [13, 332, 350, None],
            "league_name": [
                "Premier League",
                "Premier League",
                "Pro League",
                None,
            ],
        }
    )
    original = players.copy()

    result = add_league_identity(players)

    assert result["league_country"].iloc[:3].tolist() == [
        "England",
        "Ukraine",
        "Saudi Arabia",
    ]
    assert result["league_display_name"].iloc[:3].tolist() == [
        "England — Premier League",
        "Ukraine — Premier League",
        "Saudi Arabia — Pro League",
    ]
    assert pd.isna(result.at[3, "league_country"])
    assert pd.isna(result.at[3, "league_display_name"])
    pd.testing.assert_frame_equal(players, original)


@pytest.mark.parametrize(
    ("league_id", "league_name"),
    [(13, None), (None, "Premier League")],
)
def test_add_league_identity_rejects_partially_missing_identity(
    league_id, league_name
):
    players = pd.DataFrame(
        {"league_id": [league_id], "league_name": [league_name]}
    )

    with pytest.raises(ValueError, match="must be missing together"):
        add_league_identity(players)


def test_add_league_identity_rejects_unknown_identifier():
    players = pd.DataFrame(
        {"league_id": [999999], "league_name": ["Unknown League"]}
    )

    with pytest.raises(ValueError, match=r"Unknown league_id values: \[999999\]"):
        add_league_identity(players)


def test_add_league_identity_rejects_noninteger_identifier():
    players = pd.DataFrame(
        {"league_id": [13.5], "league_name": ["Premier League"]}
    )

    with pytest.raises(ValueError, match="non-integer values"):
        add_league_identity(players)


def test_drop_unused_columns_removes_only_excluded_columns():
    players = pd.DataFrame(
        {
            "player_id": [1],
            "work_rate": [None],
            "nation_team_id": [None],
            "nation_position": [None],
            "nation_jersey_number": [None],
            "player_tags": [None],
            "club_loaned_from": ["Parent Club"],
            "is_on_loan": [True],
        }
    )

    result = drop_unused_columns(players)

    assert list(result.columns) == ["player_id", "is_on_loan"]
    assert not set(EXCLUDED_COLUMNS).intersection(result.columns)


def test_drop_unused_columns_does_not_modify_input():
    players = pd.DataFrame(
        {**{column: [None] for column in EXCLUDED_COLUMNS}, "is_on_loan": [False]}
    )
    original = players.copy()

    drop_unused_columns(players)

    pd.testing.assert_frame_equal(players, original)


def test_drop_unused_columns_rejects_incomplete_source_schema():
    players = pd.DataFrame({"work_rate": [None]})

    with pytest.raises(ValueError, match="Required columns are missing"):
        drop_unused_columns(players)


def test_drop_unused_columns_requires_derived_loan_status():
    players = pd.DataFrame({column: [None] for column in EXCLUDED_COLUMNS})

    with pytest.raises(ValueError, match="is_on_loan must be derived"):
        drop_unused_columns(players)


def test_add_loan_status_classifies_nonempty_parent_club():
    players = pd.DataFrame(
        {"club_loaned_from": [None, "", "   ", "Parent Club"]}
    )

    result = add_loan_status(players)

    assert result["is_on_loan"].tolist() == [False, False, False, True]
    assert result["is_on_loan"].dtype == bool


def test_add_goalkeeper_status_uses_primary_position():
    players = pd.DataFrame(
        {"player_positions": ["GK", "  GK  ", "CB", "CB, GK"]}
    )

    result = add_goalkeeper_status(players)

    assert result["is_goalkeeper"].tolist() == [True, True, False, False]
    assert result["is_goalkeeper"].dtype == bool


def test_add_goalkeeper_status_rejects_missing_positions():
    players = pd.DataFrame({"player_positions": ["GK", None]})

    with pytest.raises(ValueError, match="missing or empty"):
        add_goalkeeper_status(players)


def test_add_free_agent_status_classifies_missing_or_empty_club():
    players = pd.DataFrame({"club_name": [None, "", "   ", "Real Madrid"]})

    result = add_free_agent_status(players)

    assert result["is_free_agent"].tolist() == [True, True, True, False]
    assert result["is_free_agent"].dtype == bool


def test_add_player_status_flags_adds_all_indicators():
    players = pd.DataFrame(
        {
            "club_loaned_from": ["Parent Club", None],
            "player_positions": ["ST", "GK"],
            "club_name": ["Loan Club", None],
        }
    )

    result = add_player_status_flags(players)

    assert result[["is_on_loan", "is_goalkeeper", "is_free_agent"]].to_dict("list") == {
        "is_on_loan": [True, False],
        "is_goalkeeper": [False, True],
        "is_free_agent": [False, True],
    }


def test_select_processed_columns_enforces_columns_and_order():
    players = pd.DataFrame(
        {
            **{column: [column] for column in PROCESSED_PLAYER_COLUMNS},
            "player_traits": ["Rapid"],
            "unexpected_source_field": ["ignored"],
        }
    )
    original = players.copy()

    result = select_processed_columns(players)

    assert tuple(result.columns) == PROCESSED_PLAYER_COLUMNS
    assert "player_traits" not in result.columns
    assert "unexpected_source_field" not in result.columns
    pd.testing.assert_frame_equal(players, original)


def test_select_processed_columns_rejects_missing_processed_field():
    players = pd.DataFrame(
        {
            column: [column]
            for column in PROCESSED_PLAYER_COLUMNS
            if column != "playstyles"
        }
    )

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['playstyles'\]",
    ):
        select_processed_columns(players)


def test_processed_player_columns_are_unique():
    assert len(PROCESSED_PLAYER_COLUMNS) == len(set(PROCESSED_PLAYER_COLUMNS))


def test_processed_player_columns_exclude_replaced_and_unused_fields():
    excluded_output_fields = {
        *EXCLUDED_COLUMNS,
        "player_positions",
        "player_traits",
        "body_type",
        "player_url",
        "player_face_url",
        "real_face",
        "club_jersey_number",
        "ls",
        "lcm",
        "rcb",
    }

    assert excluded_output_fields.isdisjoint(PROCESSED_PLAYER_COLUMNS)
    assert set(BOOLEAN_COLUMNS).issubset(PROCESSED_PLAYER_COLUMNS)
