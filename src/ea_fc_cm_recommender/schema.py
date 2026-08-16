"""Schema definitions for raw and processed player data."""

from typing import Final


EXCLUDED_COLUMNS: Final[tuple[str, ...]] = (
    "work_rate",
    "nation_team_id",
    "nation_position",
    "nation_jersey_number",
    "player_tags",
    "club_loaned_from",
)

TEXT_COLUMNS: Final[tuple[str, ...]] = (
    "short_name",
    "long_name",
    "club_name",
    "league_name",
    "nationality_name",
    "club_position",
    "player_positions",
    "player_traits",
    "preferred_foot",
    "body_type",
)

DATE_COLUMNS: Final[tuple[str, ...]] = (
    "fifa_update_date",
    "dob",
    "club_joined_date",
)

VALID_PLAYER_POSITIONS: Final[frozenset[str]] = frozenset(
    {
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
)
