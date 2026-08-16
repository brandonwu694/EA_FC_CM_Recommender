"""Reference data for unambiguous league display names."""

from collections.abc import Mapping


LEAGUE_DISPLAY_SEPARATOR = " — "

# Countries identify the league system, not every participating club's location.
LEAGUE_COUNTRY_BY_ID: Mapping[int, str] = {
    1: "Denmark",
    4: "Belgium",
    7: "Brazil",
    10: "Netherlands",
    13: "England",
    14: "England",
    16: "France",
    17: "France",
    19: "Germany",
    20: "Germany",
    31: "Italy",
    32: "Italy",
    39: "United States",  # MLS also includes Canadian clubs.
    41: "Norway",
    50: "Scotland",
    53: "Spain",
    54: "Spain",
    56: "Sweden",
    60: "England",
    61: "England",
    63: "Greece",
    64: "Hungary",
    65: "Republic of Ireland",
    66: "Poland",
    68: "Türkiye",
    80: "Austria",
    83: "South Korea",
    189: "Switzerland",
    308: "Portugal",
    313: "Azerbaijan",
    317: "Croatia",
    318: "Cyprus",
    319: "Czechia",
    322: "Finland",
    330: "Romania",
    332: "Ukraine",
    335: "Chile",
    336: "Colombia",
    337: "Paraguay",
    338: "Uruguay",
    350: "Saudi Arabia",
    351: "Australia",  # A-League Men also includes New Zealand clubs.
    353: "Argentina",
    2012: "China",
    2013: "United Arab Emirates",
    2017: "Bolivia",
    2018: "Ecuador",
    2019: "Venezuela",
    2020: "Peru",
    2076: "Germany",
    2149: "India",
}


def get_league_country(league_id: int) -> str:
    """Return the league-system country for a known league identifier."""
    try:
        return LEAGUE_COUNTRY_BY_ID[league_id]
    except KeyError as error:
        raise ValueError(f"Unknown league_id: {league_id}") from error


def format_league_display_name(league_id: int, league_name: str) -> str:
    """Build a country-qualified league display name."""
    return (
        f"{get_league_country(league_id)}"
        f"{LEAGUE_DISPLAY_SEPARATOR}"
        f"{league_name}"
    )
