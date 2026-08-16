import pandas as pd
import pytest

from ea_fc_cm_recommender.loading import load_raw_players


def test_load_raw_players_reads_csv(tmp_path):
    path = tmp_path / "players.csv"
    expected = pd.DataFrame(
        {
            "player_id": [1, 2],
            "short_name": ["Player One", "Player Two"],
        }
    )
    expected.to_csv(path, index=False)

    result = load_raw_players(path)

    pd.testing.assert_frame_equal(result, expected)


def test_load_raw_players_rejects_missing_path(tmp_path):
    path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError, match="dataset not found"):
        load_raw_players(path)


def test_load_raw_players_rejects_directory(tmp_path):
    with pytest.raises(ValueError, match="dataset is not a file"):
        load_raw_players(tmp_path)


def test_load_raw_players_rejects_non_csv_file(tmp_path):
    path = tmp_path / "players.txt"
    path.write_text("player_id\n1\n")

    with pytest.raises(ValueError, match="dataset must be a CSV"):
        load_raw_players(path)


def test_load_raw_players_rejects_empty_file(tmp_path):
    path = tmp_path / "players.csv"
    path.write_text("")

    with pytest.raises(ValueError, match="dataset is empty"):
        load_raw_players(path)


def test_load_raw_players_rejects_header_only_csv(tmp_path):
    path = tmp_path / "players.csv"
    pd.DataFrame(columns=["player_id"]).to_csv(path, index=False)

    with pytest.raises(ValueError, match="dataset has no rows"):
        load_raw_players(path)
