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

DETAILED_ATTRIBUTE_COLUMNS: Final[tuple[str, ...]] = (
    "attacking_crossing",
    "attacking_finishing",
    "attacking_heading_accuracy",
    "attacking_short_passing",
    "attacking_volleys",
    "skill_dribbling",
    "skill_curve",
    "skill_fk_accuracy",
    "skill_long_passing",
    "skill_ball_control",
    "movement_acceleration",
    "movement_sprint_speed",
    "movement_agility",
    "movement_reactions",
    "movement_balance",
    "power_shot_power",
    "power_jumping",
    "power_stamina",
    "power_strength",
    "power_long_shots",
    "mentality_aggression",
    "mentality_interceptions",
    "mentality_positioning",
    "mentality_vision",
    "mentality_penalties",
    "mentality_composure",
    "defending_marking_awareness",
    "defending_standing_tackle",
    "defending_sliding_tackle",
    "goalkeeping_diving",
    "goalkeeping_handling",
    "goalkeeping_kicking",
    "goalkeeping_positioning",
    "goalkeeping_reflexes",
)

REQUIRED_INTEGER_COLUMNS: Final[tuple[str, ...]] = (
    "player_id",
    "fifa_version",
    "fifa_update",
    "overall",
    "potential",
    "value_eur",
    "wage_eur",
    "age",
    "height_cm",
    "weight_kg",
    "nationality_id",
    "weak_foot",
    "skill_moves",
    "international_reputation",
    *DETAILED_ATTRIBUTE_COLUMNS,
)

NULLABLE_INTEGER_COLUMNS: Final[tuple[str, ...]] = (
    "league_id",
    "league_level",
    "club_team_id",
    "club_contract_valid_until_year",
    "release_clause_eur",
    "pace",
    "shooting",
    "passing",
    "dribbling",
    "defending",
    "physic",
    "goalkeeping_speed",
)

VALID_PLAYSTYLE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "Acrobatic",
        "Aerial Fortress",
        "Anticipate",
        "Block",
        "Bruiser",
        "Chip Shot",
        "Cross Claimer",
        "Dead Ball",
        "Deflector",
        "Enforcer",
        "Far Reach",
        "Far Throw",
        "Finesse Shot",
        "First Touch",
        "Footwork",
        "Gamechanger",
        "Incisive Pass",
        "Intercept",
        "Inventive",
        "Jockey",
        "Long Ball Pass",
        "Long Throw",
        "Low Driven Shot",
        "Pinged Pass",
        "Power Shot",
        "Precision Header",
        "Press Proven",
        "Quick Step",
        "Rapid",
        "Relentless",
        "Rush Out",
        "Slide Tackle",
        "Technical",
        "Tiki Taka",
        "Trickster",
        "Whipped Pass",
    }
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
