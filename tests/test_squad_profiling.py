import pandas as pd
import pytest

from ea_fc_cm_recommender.squad_profiling import (
    build_position_profile,
    build_team_profile,
    get_club_squad,
    get_players_for_position,
)
from ea_fc_cm_recommender.schema import PLAYER_POSITION_ORDER


def _players() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "player_id": [1, 2, 3, 4],
            "club_team_id": pd.Series([100, 200, 100, pd.NA], dtype="Int64"),
            "club_name": pd.Series(
                ["Club One", "Club Two", "Club One", pd.NA],
                dtype="string",
            ),
            "short_name": ["Starter", "Opponent", "Loan Player", "Free Agent"],
            "is_on_loan": [False, False, True, False],
        }
    )


def test_get_club_squad_selects_current_players_and_preserves_order():
    squad = get_club_squad(_players(), 100)

    assert squad["player_id"].tolist() == [1, 3]
    assert squad["short_name"].tolist() == ["Starter", "Loan Player"]
    assert squad["is_on_loan"].tolist() == [False, True]


def test_get_club_squad_returns_independent_copy():
    players = _players()
    original = players.copy()

    squad = get_club_squad(players, 100)
    squad.loc[:, "club_name"] = "Changed Club"

    pd.testing.assert_frame_equal(players, original)


@pytest.mark.parametrize("club_team_id", [0, -1, True, 1.5, "100"])
def test_get_club_squad_rejects_invalid_identifier(club_team_id):
    with pytest.raises(ValueError, match="must be a positive integer"):
        get_club_squad(_players(), club_team_id)


def test_get_club_squad_reports_when_no_players_are_found():
    with pytest.raises(ValueError, match="No players found for club_team_id: 999"):
        get_club_squad(_players(), 999)


def test_get_club_squad_rejects_missing_required_columns():
    players = _players().drop(columns=["player_id", "club_name"])

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['player_id', 'club_name'\]",
    ):
        get_club_squad(players, 100)


def _squad() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "player_id": [1, 2, 3, 4],
            "club_team_id": [100, 100, 100, 100],
            "club_name": ["Club One", "Club One", "Club One", "Club One"],
            "short_name": ["Primary RB", "Versatile CB", "Striker", "Wing Back"],
            "primary_position": ["RB", "CB", "ST", "RWB"],
            "secondary_positions": [
                ["RWB"],
                ["RB"],
                [],
                ["RB", "RM"],
            ],
            "overall": [80, 78, 85, 72],
            "age": [25, 22, 29, 20],
            "potential": [82, 85, 85, 88],
            "playstyles": [
                ["Jockey"],
                ["Block", "Jockey"],
                ["Power Shot"],
                ["Rapid", "Jockey"],
            ],
        }
    )


def test_get_players_for_position_matches_primary_and_secondary_positions():
    players = get_players_for_position(_squad(), "RB")

    assert players["player_id"].tolist() == [1, 2, 4]


def test_get_players_for_position_normalizes_the_requested_position():
    players = get_players_for_position(_squad(), " rb ")

    assert players["player_id"].tolist() == [1, 2, 4]


def test_get_players_for_position_returns_empty_dataframe_for_no_coverage():
    players = get_players_for_position(_squad(), "GK")

    assert players.empty
    assert players.columns.tolist() == _squad().columns.tolist()


@pytest.mark.parametrize("position", [None, 1, True, "invalid"])
def test_get_players_for_position_rejects_invalid_positions(position):
    with pytest.raises(ValueError, match="position|Unknown player position"):
        get_players_for_position(_squad(), position)


def test_get_players_for_position_rejects_missing_required_columns():
    squad = _squad().drop(columns=["secondary_positions"])

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['secondary_positions'\]",
    ):
        get_players_for_position(squad, "RB")


def test_get_players_for_position_returns_independent_copy():
    squad = _squad()
    original = squad.copy(deep=True)

    players = get_players_for_position(squad, "RB")
    players.loc[:, "primary_position"] = "ST"

    pd.testing.assert_frame_equal(squad, original)


def test_build_position_profile_summarizes_primary_and_secondary_coverage():
    profile = build_position_profile(_squad(), "RB")

    assert profile == {
        "position": "RB",
        "player_count": 3,
        "primary_position_count": 1,
        "secondary_position_count": 2,
        "starter_overall": 80,
        "backup_overall": 78,
        "average_overall": pytest.approx(76.66666666666667),
        "average_age": pytest.approx(22.333333333333332),
        "highest_potential": 88,
        "playstyles": ["Block", "Jockey", "Rapid"],
    }


def test_build_position_profile_handles_one_available_player():
    profile = build_position_profile(_squad(), "ST")

    assert profile["player_count"] == 1
    assert profile["starter_overall"] == 85
    assert profile["backup_overall"] is None
    assert profile["playstyles"] == ["Power Shot"]


def test_build_position_profile_handles_no_position_coverage():
    profile = build_position_profile(_squad(), "GK")

    assert profile == {
        "position": "GK",
        "player_count": 0,
        "primary_position_count": 0,
        "secondary_position_count": 0,
        "starter_overall": None,
        "backup_overall": None,
        "average_overall": None,
        "average_age": None,
        "highest_potential": None,
        "playstyles": [],
    }


def test_build_position_profile_normalizes_the_requested_position():
    profile = build_position_profile(_squad(), " rb ")

    assert profile["position"] == "RB"


def test_build_position_profile_rejects_missing_profile_columns():
    squad = _squad().drop(columns=["overall", "playstyles"])

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['overall', 'playstyles'\]",
    ):
        build_position_profile(squad, "RB")


def test_build_team_profile_summarizes_squad_and_every_position():
    profile = build_team_profile(_squad())

    assert profile["club_team_id"] == 100
    assert profile["club_name"] == "Club One"
    assert profile["squad_size"] == 4
    assert profile["average_overall"] == pytest.approx(78.75)
    assert profile["average_age"] == pytest.approx(24.0)

    position_profiles = profile["position_profiles"]
    assert list(position_profiles) == list(PLAYER_POSITION_ORDER)
    assert position_profiles["RB"] == build_position_profile(_squad(), "RB")
    assert position_profiles["GK"]["player_count"] == 0


def test_build_team_profile_rejects_an_empty_squad():
    with pytest.raises(ValueError, match="Squad has no players"):
        build_team_profile(_squad().iloc[0:0])


def test_build_team_profile_rejects_multiple_clubs():
    squad = _squad()
    squad.loc[3, "club_team_id"] = 200

    with pytest.raises(
        ValueError,
        match="Squad must contain exactly one club_team_id",
    ):
        build_team_profile(squad)


def test_build_team_profile_rejects_inconsistent_club_names():
    squad = _squad()
    squad.loc[3, "club_name"] = "Different Club"

    with pytest.raises(
        ValueError,
        match="Squad must contain exactly one club_name",
    ):
        build_team_profile(squad)


def test_build_team_profile_rejects_missing_required_columns():
    squad = _squad().drop(columns=["club_team_id", "potential"])

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['club_team_id', 'potential'\]",
    ):
        build_team_profile(squad)
