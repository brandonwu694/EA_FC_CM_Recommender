# Phase 1 Preprocessing Decisions

This document records the current data assumptions and transformation decisions
for the FC 26 player dataset. The implementation is intentionally limited to
Phase 1; recommendation and candidate-ranking logic belong to later phases.

The canonical code definitions live in:

- `src/ea_fc_cm_recommender/schema.py`
- `src/ea_fc_cm_recommender/league_mappings.py`
- `src/ea_fc_cm_recommender/preprocessing.py`

## Source Data and Row Grain

The raw snapshot is `data/raw/FC26_20250921.csv`.

- It contains 18,405 rows and 110 columns.
- It represents FC 26 update 4, dated 2025-09-19.
- One row represents one player in that snapshot.
- `player_id` is complete and unique in the file.
- Names are descriptive fields and are not unique identifiers.

If multiple updates are combined later, a longitudinal key must include the
player identifier and update identifier or date.

The raw CSV is immutable. All cleaning must produce a separate processed
dataset under `data/processed/`.

## Current Transformations

### Raw Data Loading

`load_raw_players()` reads a non-empty CSV from an explicit `Path`. It verifies
that the path exists, is a file, and has a `.csv` extension before reading it
with consistent pandas options. Empty files and header-only datasets fail with
informative errors.

The loader does not search for the project root, choose among files in
`data/raw/`, clean values, or enforce the FC 26 domain schema. The future
pipeline supplies the input path, preprocessing performs transformations, and
validation enforces data assumptions.

### Whitespace Normalization

`normalize_whitespace()` and `normalize_text_columns()`:

- convert non-breaking spaces to ordinary spaces
- collapse repeated whitespace, tabs, and newlines
- trim leading and trailing whitespace
- preserve missing values
- preserve capitalization, accents, punctuation, and spelling

The selected text columns are defined in `schema.py`. The function intentionally
does not casefold, remove accents, or rewrite category labels.

### Date Standardization

The source date columns are defined by `DATE_COLUMNS` in `schema.py`:

```text
fifa_update_date
dob
club_joined_date
```

`standardize_date_columns()` parses these fields strictly as `YYYY-MM-DD` and
returns pandas datetime columns. Missing values remain `NaT`; malformed values
raise an error rather than being silently coerced. In the current snapshot,
only `club_joined_date` is nullable, with 1,414 structurally missing values for
loaned players and free agents.

### Numeric Standardization

`standardize_integer_columns()` converts retained numeric fields without
silently truncating fractional values. Complete fields use NumPy `int64`, while
structurally nullable fields use pandas `Int64` so missing values remain
`pd.NA` rather than forcing the entire column to floating point.

Required integers include player and snapshot identifiers, OVR, potential, age,
value, wage, physical measurements, nationality ID, profile ratings, and the
detailed player attributes needed for later role-fit scoring. Nullable integers
include club and league identifiers, league level, contract year, release
clause, outfield summary attributes, and goalkeeper speed.

Jersey numbers are not part of the retained numeric contract because they do
not contribute to recommendation logic. Previously agreed deprecated or
national-team fields remain excluded. Derived status flags are already emitted
as non-nullable Boolean columns by their respective transformations.

### League Identity

The raw dataset contains `league_id`, `league_name`, and `league_level`, but no
country field. Some names, including `Premier League`, `Pro League`, and
`Super League`, identify competitions in more than one league system.

League identity is mapped by `league_id`, never inferred from the ambiguous
name. Preprocessing preserves the source fields and adds:

```text
league_country
league_display_name
```

The display convention is country first:

```text
England — Premier League
Ukraine — Premier League
Belgium — Pro League
Saudi Arabia — Pro League
```

`league_country` describes the competition's league system rather than every
participating club's physical location. For example, a cross-border club is
still associated with the league system in which the competition operates.

All 51 non-null league IDs in the current snapshot have an explicit mapping.
The 89 free agents have both league ID and name missing; partial league identity
is treated as a data-quality error.

### Player Status Flags

Preprocessing derives three deterministic Boolean fields:

```text
is_on_loan
is_goalkeeper
is_free_agent
```

In the current snapshot:

```text
is_on_loan       1,325 players
is_goalkeeper    2,062 players
is_free_agent       89 players
```

`is_on_loan` preserves the transfer-eligibility signal before the sparse
`club_loaned_from` field is removed. Candidate exclusion is not performed in
preprocessing; it belongs to the later candidate-generation phase.

`is_goalkeeper` explains the mutually exclusive goalkeeper and outfield summary
attributes. `is_free_agent` explains the structurally missing club and league
fields.

### Player Positions

`player_positions` is an ordered comma-delimited source field. The first token
is the primary position and the remaining tokens are alternative positions.

For example:

```text
player_positions     = "CM, CDM, CAM"
primary_position     = "CM"
secondary_positions  = ["CDM", "CAM"]
```

Position parsing:

- splits on commas and trims each token
- preserves source order
- represents no secondary positions as an empty list
- rejects missing, empty, duplicate, or unknown tokens
- preserves the raw position field until the final allowlist is defined

The supported vocabulary includes valid `RWB`, `LWB`, and `CF` codes even
though they do not occur in the current snapshot.

### Excluded Source Columns

The canonical exclusion list is defined in `schema.py`. Current decisions are:

| Source field | Reason |
|---|---|
| `work_rate` | Entirely missing in this snapshot |
| `nation_team_id` | Sparse and not required for the current recommender |
| `nation_position` | Temporary national-team selection context |
| `nation_jersey_number` | No current recommendation value |
| `player_tags` | Sparse and overlaps attributes and PlayStyles |
| `club_loaned_from` | Replaced by `is_on_loan` for the current scope |

The raw fields remain recoverable from the source CSV.

### Final Processed Schema

`PROCESSED_PLAYER_COLUMNS` in `schema.py` is the authoritative ordered output
contract. `select_processed_columns()` runs after all derivations, verifies
that every processed field exists, selects them in a stable order, and ignores
any other source columns.

The final selection omits raw fields replaced by `primary_position`,
`secondary_positions`, `playstyles`, and `is_on_loan`. It also omits URLs,
face metadata, body type, jersey numbers, national-team selection fields, and
the raw positional-rating strings. Identifiers, snapshot lineage, financial
fields, club and league context, player profile fields, summary ratings, and
detailed attributes remain available for later recommendation phases.

Using an allowlist prevents new source columns from silently entering the
processed dataset and fixes the Parquet column order across repeated runs.

### Validation

`validate_raw_players()` checks the input schema, snapshot fields, and player
identifiers before transformation. `validate_processed_players()` enforces the
ordered output schema, dtypes, identifiers, category consistency, value ranges,
position and PlayStyle collections, dates, and documented structural-null
relationships. `validate_preserved_row_count()` ensures preprocessing neither
adds nor removes players.

Validators do not clean or impute values. They return `None` when every rule
passes and raise an informative `ValueError` when a data contract is violated.
The current 18,405-row snapshot passes both raw and processed validation.

### End-to-End Pipeline

`preprocess_players()` validates raw data, applies each transformation in an
explicit order, selects the final schema, verifies row-count preservation, and
validates the processed result. It returns a new DataFrame and does not modify
the raw input.

`build_processed_dataset()` loads an explicit raw CSV path, calls the validated
preprocessing workflow, creates the output directory when needed, and writes an
indexed-free Snappy-compressed Parquet file through PyArrow. The output path
must use the `.parquet` extension.

## Structural Missingness

Missing values are not automatically treated as data errors.

### Goalkeepers and Outfield Players

- `goalkeeping_speed` is populated for goalkeepers and null for outfield players.
- `pace`, `shooting`, `passing`, `dribbling`, `defending`, and `physic` are
  populated for outfield players and null for goalkeepers.
- These numeric nulls must not be replaced with zero or text such as `"N/A"`.

### Loans and Free Agents

- `club_joined_date` is missing for exactly the loaned and free-agent players.
- Eight club and league fields are missing for exactly the 89 free agents.
- These nulls should remain and be validated against the derived status flags.

### Release Clauses and Zero Values

`release_clause_eur` is missing exactly when a player is on loan, is a free
agent, or has `value_eur == 0` in this snapshot.

The 20 contracted, non-loan, zero-value cases are all outfield players aged 40
or older. Their zero market values and null release clauses form a consistent
source-data rule and should not be imputed.

### PlayStyles

`parse_playstyles()` converts the comma-delimited `player_traits` source field
into the list-valued `playstyles` field. It normalizes whitespace, preserves
source order and capitalization, and changes the source's `"PlayStyle +"`
notation to `"PlayStyle+"`. Missing or blank source values become empty lists.

Each value is validated by removing an optional trailing `+` and comparing the
base name with `VALID_PLAYSTYLE_NAMES` in `schema.py`. This detects unexpected
categories without silently rewriting their names. Empty and duplicate tokens
are treated as data-quality errors. The raw `player_traits` field remains
available until the final processed-column allowlist is applied.

## Schema Organization

Responsibilities are separated as follows:

```text
schema.py
    Schema-policy constants, processed columns, and dtype contracts.

league_mappings.py
    League ID reference data and display formatting.

loading.py
    Raw CSV loading and basic file-level checks.

pipeline.py
    Validated transformation orchestration and Parquet output.

preprocessing.py
    Stateless dataframe transformations.

validation.py
    Raw and processed schema, range, and structural-null validation.
```

Schema constants are not runtime configuration. A future `config.py` should be
reserved for paths, logging, or environment-specific settings.

## Remaining Phase 1 Work

The reusable end-to-end preprocessing workflow is implemented and tested.
Remaining work includes:

1. Add a command-line entry point under `scripts/`.
2. Run and document the command that creates the reproducible dataset under
   `data/processed/`.

## Tests

Run the focused test suite from the project root:

```bash
pytest
```

Synthetic fixtures are preferred for unit tests. Full-snapshot checks may be
used for integration validation once the complete pipeline exists.
