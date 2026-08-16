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
    split_player_positions,
)
from ea_fc_cm_recommender.schema import (
    EXCLUDED_COLUMNS,
    TEXT_COLUMNS,
    VALID_PLAYER_POSITIONS,
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
        {column: ["value"] for column in TEXT_COLUMNS if column != "body_type"}
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
