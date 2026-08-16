import pandas as pd
import pytest

from ea_fc_cm_recommender.preprocessing import (
    EXCLUDED_COLUMNS,
    add_free_agent_status,
    add_goalkeeper_status,
    add_loan_status,
    add_player_status_flags,
    drop_unused_columns,
    normalize_whitespace,
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

    with pytest.raises(ValueError, match="Expected columns are missing"):
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
