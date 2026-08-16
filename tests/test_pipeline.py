import pandas as pd
import pytest

from ea_fc_cm_recommender.pipeline import (
    build_processed_dataset,
    preprocess_players,
)
from ea_fc_cm_recommender.schema import (
    NULLABLE_INTEGER_COLUMNS,
    OUTFIELD_SUMMARY_COLUMNS,
    PROCESSED_PLAYER_COLUMNS,
    RAW_REQUIRED_COLUMNS,
    REQUIRED_INTEGER_COLUMNS,
)


def _raw_players() -> pd.DataFrame:
    data = {
        column: [50, 50]
        for column in RAW_REQUIRED_COLUMNS
    }
    data.update(
        {
            "player_id": [1, 2],
            "fifa_version": [26, 26],
            "fifa_update": [4, 4],
            "fifa_update_date": ["2025-09-19", "2025-09-19"],
            "short_name": ["Goalkeeper", "Striker"],
            "long_name": ["Goalkeeper Example", "Striker Example"],
            "player_positions": ["GK", "ST, RW"],
            "overall": [80, 75],
            "potential": [85, 80],
            "value_eur": [10_000_000, 5_000_000],
            "wage_eur": [50_000, 25_000],
            "age": [25, 30],
            "dob": ["2000-01-01", "1995-01-01"],
            "height_cm": [190, 180],
            "weight_kg": [85, 75],
            "league_id": [13, 13],
            "league_name": ["Premier League", "Premier League"],
            "league_level": [1, 1],
            "club_team_id": [100, 101],
            "club_name": ["Club One", "Club Two"],
            "club_position": ["GK", "SUB"],
            "club_loaned_from": [None, "Parent Club"],
            "club_joined_date": ["2020-07-01", None],
            "club_contract_valid_until_year": [2028, 2027],
            "nationality_id": [14, 14],
            "nationality_name": ["England", "England"],
            "preferred_foot": ["Right", "Left"],
            "weak_foot": [3, 4],
            "skill_moves": [1, 4],
            "international_reputation": [2, 3],
            "release_clause_eur": [20_000_000, None],
            "player_traits": ["Footwork", "Finesse Shot +"],
            "goalkeeping_speed": [50, None],
        }
    )
    for column in OUTFIELD_SUMMARY_COLUMNS:
        data[column] = [None, 75]
    return pd.DataFrame(data)


def test_preprocess_players_builds_valid_ordered_schema():
    raw_players = _raw_players()
    original = raw_players.copy()

    result = preprocess_players(raw_players)

    assert result.shape == (2, len(PROCESSED_PLAYER_COLUMNS))
    assert tuple(result.columns) == PROCESSED_PLAYER_COLUMNS
    assert result["primary_position"].tolist() == ["GK", "ST"]
    assert result["secondary_positions"].tolist() == [[], ["RW"]]
    assert result["playstyles"].tolist() == [
        ["Footwork"],
        ["Finesse Shot+"],
    ]
    assert all(
        result[column].dtype == "int64"
        for column in REQUIRED_INTEGER_COLUMNS
    )
    assert all(
        result[column].dtype == "Int64"
        for column in NULLABLE_INTEGER_COLUMNS
    )
    pd.testing.assert_frame_equal(raw_players, original)


def test_preprocess_players_rejects_invalid_raw_schema():
    raw_players = _raw_players().drop(columns="player_traits")

    with pytest.raises(
        ValueError,
        match=r"Required columns are missing: \['player_traits'\]",
    ):
        preprocess_players(raw_players)


def test_build_processed_dataset_writes_parquet(tmp_path):
    raw_path = tmp_path / "raw" / "players.csv"
    output_path = tmp_path / "processed" / "players.parquet"
    raw_path.parent.mkdir()
    _raw_players().to_csv(raw_path, index=False)

    result_path = build_processed_dataset(raw_path, output_path)
    restored = pd.read_parquet(result_path)

    assert result_path == output_path
    assert result_path.is_file()
    assert restored.shape == (2, len(PROCESSED_PLAYER_COLUMNS))
    assert tuple(restored.columns) == PROCESSED_PLAYER_COLUMNS
    assert restored["secondary_positions"].map(list).tolist() == [[], ["RW"]]
    assert restored["playstyles"].map(list).tolist() == [
        ["Footwork"],
        ["Finesse Shot+"],
    ]


def test_build_processed_dataset_rejects_non_parquet_output(tmp_path):
    raw_path = tmp_path / "players.csv"
    _raw_players().to_csv(raw_path, index=False)

    with pytest.raises(ValueError, match="must be Parquet"):
        build_processed_dataset(raw_path, tmp_path / "players.csv")
