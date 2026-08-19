"""Squad selection and profiling utilities."""

from numbers import Integral

import pandas as pd

from ea_fc_cm_recommender.schema import (
    PLAYER_POSITION_ORDER,
    VALID_PLAYER_POSITIONS,
)
from ea_fc_cm_recommender.validation import require_columns


def get_club_squad(
    players: pd.DataFrame,
    club_team_id: int,
) -> pd.DataFrame:
    """Return the current squad for a known club identifier."""
    require_columns(players, ("player_id", "club_team_id", "club_name"))

    # Make sure that boolean values are not accidentally converted to 0 or 1
    # Integral is compatible with both Python numbers and pandas/numpy integers
    if isinstance(club_team_id, bool) or not isinstance(club_team_id, Integral):
        raise ValueError("club_team_id must be a positive integer")
    if club_team_id <= 0:
        raise ValueError("club_team_id must be a positive integer")

    # Find all player rows belonging to the requested club
    squad = players.loc[players["club_team_id"].eq(club_team_id)]
    if squad.empty:
        raise ValueError(f"No players found for club_team_id: {club_team_id}")
    return squad.copy()


def get_players_for_position(
    squad: pd.DataFrame,
    position: str,
) -> pd.DataFrame:
    """Return squad players capable of playing the requested position."""
    require_columns(
        squad,
        ("player_id", "primary_position", "secondary_positions"),
    )

    if not isinstance(position, str):
        raise ValueError("position must be a valid player position")

    normalized_position = position.strip().upper()
    if normalized_position not in VALID_PLAYER_POSITIONS:
        raise ValueError(f"Unknown player position: {position}")

    primary_match = squad["primary_position"].eq(normalized_position)
    # Parse through list of secondary positions; players can possess more than one alternate position
    secondary_match = squad["secondary_positions"].map(
        lambda positions: normalized_position in positions
    )
    return squad.loc[primary_match | secondary_match].copy()


def build_position_profile(
    squad: pd.DataFrame,
    position: str,
) -> dict[str, object]:
    """Summarize squad coverage and quality for one position."""
    require_columns(squad, ("overall", "age", "potential", "playstyles"))

    position_players = get_players_for_position(squad, position)
    normalized_position = position.strip().upper()
    player_count = len(position_players)
    primary_position_count = int(
        position_players["primary_position"].eq(normalized_position).sum()
    )

    if position_players.empty:
        return {
            "position": normalized_position,
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

    overall_by_rank = position_players["overall"].sort_values(
        ascending=False
    )
    playstyles = sorted(
        {
            playstyle
            for player_playstyles in position_players["playstyles"]
            for playstyle in player_playstyles
        }
    )

    return {
        "position": normalized_position,
        "player_count": player_count,
        "primary_position_count": primary_position_count,
        "secondary_position_count": player_count - primary_position_count,
        "starter_overall": int(overall_by_rank.iloc[0]),
        "backup_overall": (
            int(overall_by_rank.iloc[1]) if player_count > 1 else None
        ),
        "average_overall": float(position_players["overall"].mean()),
        "average_age": float(position_players["age"].mean()),
        "highest_potential": int(position_players["potential"].max()),
        "playstyles": playstyles,
    }


def build_team_profile(squad: pd.DataFrame) -> dict[str, object]:
    """Summarize squad-wide quality and coverage for every position."""
    require_columns(
        squad,
        (
            "player_id",
            "club_team_id",
            "club_name",
            "primary_position",
            "secondary_positions",
            "overall",
            "age",
            "potential",
            "playstyles",
        ),
    )
    if squad.empty:
        raise ValueError("Squad has no players")

    club_ids = squad["club_team_id"].drop_duplicates()
    if club_ids.isna().any() or len(club_ids) != 1:
        raise ValueError("Squad must contain exactly one club_team_id")

    club_names = squad["club_name"].drop_duplicates()
    if club_names.isna().any() or len(club_names) != 1:
        raise ValueError("Squad must contain exactly one club_name")

    position_profiles = {
        position: build_position_profile(squad, position)
        for position in PLAYER_POSITION_ORDER
    }
    return {
        "club_team_id": int(club_ids.iloc[0]),
        "club_name": str(club_names.iloc[0]),
        "squad_size": len(squad),
        "average_overall": float(squad["overall"].mean()),
        "average_age": float(squad["age"].mean()),
        "position_profiles": position_profiles,
    }
