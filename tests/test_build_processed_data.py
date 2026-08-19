from pathlib import Path

from ea_fc_cm_recommender import cli


def test_main_calls_pipeline_with_paths(monkeypatch, capsys, tmp_path):
    input_path = tmp_path / "players.csv"
    output_path = tmp_path / "players.parquet"
    received_paths = {}

    def fake_build(raw_path, processed_path):
        received_paths["raw"] = raw_path
        received_paths["processed"] = processed_path
        return processed_path

    monkeypatch.setattr(
        cli,
        "build_processed_dataset",
        fake_build,
    )

    exit_code = cli.main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert received_paths == {
        "raw": input_path,
        "processed": output_path,
    }
    assert capsys.readouterr().out.strip() == (
        f"Created processed dataset: {output_path}"
    )


def test_main_reports_expected_build_error(monkeypatch, capsys):
    def fake_build(raw_path, output_path):
        raise ValueError("invalid processed schema")

    monkeypatch.setattr(
        cli,
        "build_processed_dataset",
        fake_build,
    )

    exit_code = cli.main(
        [
            "--input",
            "players.csv",
            "--output",
            "players.parquet",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Build failed: invalid processed schema"


def test_parser_converts_arguments_to_paths():
    args = cli._build_parser().parse_args(
        [
            "--input",
            "data/raw/players.csv",
            "--output",
            "data/processed/players.parquet",
        ]
    )

    assert args.input == Path("data/raw/players.csv")
    assert args.output == Path("data/processed/players.parquet")
