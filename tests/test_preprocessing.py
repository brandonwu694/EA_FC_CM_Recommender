import pandas as pd

from ea_fc_cm_recommender.preprocessing import normalize_whitespace


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
