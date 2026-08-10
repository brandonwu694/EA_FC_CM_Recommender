import pytest

from ea_fc_cm_recommender.league_mappings import (
    LEAGUE_COUNTRY_BY_ID,
    format_league_display_name,
    get_league_country,
)


@pytest.mark.parametrize(
    ("league_id", "league_name", "expected"),
    [
        (13, "Premier League", "England — Premier League"),
        (14, "Championship", "England — Championship"),
        (50, "Premiership", "Scotland — Premiership"),
        (332, "Premier League", "Ukraine — Premier League"),
        (2012, "Super League", "China — Super League"),
        (2149, "Super League", "India — Super League"),
    ],
)
def test_format_league_display_name(league_id, league_name, expected):
    assert format_league_display_name(league_id, league_name) == expected


def test_mapping_covers_current_snapshot_leagues():
    assert len(LEAGUE_COUNTRY_BY_ID) == 51


def test_get_league_country_rejects_unknown_identifier():
    with pytest.raises(ValueError, match="Unknown league_id: 999999"):
        get_league_country(999999)
