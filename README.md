# ⚽ EA FC Career Mode Player Recommender

A contextual recommendation system that recommends realistic and useful transfer targets for EA FC Career Mode saves.

---

## 📊 Dataset

This project uses FC 26 player data from
[Kaggle](https://www.kaggle.com/code/hamzazerou/fc26-data-analyzing)
as the primary source for player ratings, positions, and attributes.

---

## 🎯 Features

- Realistic Transfer Recommendations: Suggests players based on squad needs, club level, transfer budget, and real-world transfer context rather than simply recommending the highest-rated options.
- Centralized Player Discovery: Provides a single place to compare and rank potential signings, reducing the need to manually search through player databases, videos, forums, or social media for transfer ideas.
- More Varied Career Mode Saves: Encourages signings that fit each club's circumstances, helping users avoid repeatedly buying the same popular players and making unfamiliar clubs easier to manage realistically.
- Explainable Recommendations: Breaks down why each player is recommended using factors such as squad impact, player quality, role fit, and transfer realism.

---

## Development Status

The project is currently in **Phase 1: Data Ingestion and Preprocessing**.

Implemented preprocessing components include:

- conservative whitespace normalization for selected text fields
- country-qualified league identities
- loan, goalkeeper, and free-agent status flags
- primary and secondary position parsing
- validated PlayStyle parsing
- strict date standardization
- explicit required and nullable integer dtypes
- an ordered final processed-column allowlist
- explicit removal of agreed unused source columns
- raw and processed data-contract validation
- validated raw-to-processed pipeline with Parquet output
- command-line processed-data build entry point
- focused unit tests for each transformation and validation rule

The reusable raw-to-processed pipeline and command-line entry point are
implemented.

See [Preprocessing Decisions](docs/PREPROCESSING.md) for the current data
assumptions and implementation status. The broader roadmap remains in
[Project Plan](docs/PLAN.md).

## Project Structure

```text
data/
├── raw/
└── processed/
notebooks/
└── fc26_player_eda.ipynb
scripts/
└── build_processed_data.py
src/
└── ea_fc_cm_recommender/
    ├── league_mappings.py
    ├── loading.py
    ├── pipeline.py
    ├── preprocessing.py
    ├── schema.py
    └── validation.py
tests/
├── test_build_processed_data.py
├── test_league_mappings.py
├── test_loading.py
├── test_pipeline.py
├── test_preprocessing.py
└── test_validation.py
```

- `data/raw/` contains source data and must not be modified in place.
- `data/processed/` will contain reproducible processed outputs.
- `schema.py` is the canonical location for schema-policy constants.
- `league_mappings.py` contains league reference data.
- `loading.py` loads raw data from explicit filesystem paths.
- `pipeline.py` orchestrates validation, transformations, and Parquet output.
- `preprocessing.py` contains reusable, stateless transformations.
- `validation.py` enforces raw and processed data contracts.

## Building the Processed Dataset

Run the build command from the project root with the project environment
active:

```bash
PYTHONPATH=src python -m scripts.build_processed_data \
  --input data/raw/FC26_20250921.csv \
  --output data/processed/FC26_20250921.parquet
```

The command validates the raw data, applies the complete preprocessing
pipeline, validates the 78-column result, and writes an index-free,
Snappy-compressed Parquet file. Generated processed data is ignored by Git and
can be reproduced from the raw snapshot and code.

## Running Tests

From the project root, with the project environment active:

```bash
pytest
```

Pytest reads `pytest.ini` so the package under `src/` can be imported without
manually setting `PYTHONPATH`.
