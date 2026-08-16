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

The source `player_traits` field contains PlayStyles. Missing values are expected
to become an empty PlayStyle collection, but parsing has not yet been
implemented. `+` variants must remain distinguishable from their base names.

## Schema Organization

Responsibilities are separated as follows:

```text
schema.py
    Schema-policy constants and, later, processed columns and dtype contracts.

league_mappings.py
    League ID reference data and display formatting.

preprocessing.py
    Stateless dataframe transformations.

validation.py
    Planned processed-data and structural-null validation.
```

Schema constants are not runtime configuration. A future `config.py` should be
reserved for paths, logging, or environment-specific settings.

## Remaining Phase 1 Work

The current functions are tested individually but are not yet connected through
an end-to-end preprocessing workflow. Remaining work includes:

1. Parse `player_traits` into a PlayStyle list.
2. Standardize the remaining numeric and Boolean dtypes.
3. Define the final processed-column allowlist.
4. Add identifier, range, structural-null, and schema validation.
5. Implement raw-data loading and transformation orchestration.
6. Write and verify a reproducible Parquet dataset under `data/processed/`.

## Tests

Run the focused test suite from the project root:

```bash
pytest
```

Synthetic fixtures are preferred for unit tests. Full-snapshot checks may be
used for integration validation once the complete pipeline exists.
