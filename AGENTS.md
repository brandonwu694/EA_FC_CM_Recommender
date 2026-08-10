# AGENTS.md

## Project Context

This repository contains the **EA FC Career Mode Player Recommender**, an explainable recommendation system for ranking realistic and useful Career Mode transfer targets.

The full project roadmap lives in:

```text
docs/PLAN.md
```

Use `docs/PLAN.md` for project-wide context, future phases, scoring design, evaluation plans, and architectural intent.

Do **not** implement future phases unless the current task explicitly asks for them.

---

## Current Development Phase

### Phase 1 — Data Ingestion and Preprocessing

The current priority is to build a reliable preprocessing pipeline for the raw EA FC player dataset.

The goal of Phase 1 is to transform raw source data into a clean, validated, reusable processed dataset that later recommendation logic can consume.

### Phase 1 Responsibilities

Phase 1 should:

1. Load the raw player dataset.
2. Inspect and verify the expected schema.
3. Select only fields required by the project.
4. Standardize important values.
5. Handle missing or malformed values consistently.
6. Validate critical player fields.
7. Write the cleaned dataset to the processed data layer.
8. Keep preprocessing logic reusable and testable.

### Important Fields

Preserve and standardize relevant fields such as:

- player identifier
- player name
- club
- league
- overall rating
- potential
- age
- primary position
- secondary positions
- PlayStyles
- market value
- wage
- other attributes that are clearly needed by future recommendation logic

Do not retain unnecessary columns merely because they exist in the source dataset.

If the exact source schema differs from expectations, inspect the data first and adapt the mapping intentionally rather than silently guessing.

---

## Data Organization

Use the following structure unless the project evolves enough to justify a change:

```text
data/
├── raw/
└── processed/
```

### `data/raw/`

- Contains source data in its original form.
- Do not modify raw files in place.
- Raw data should be reproducible from the documented source.

### `data/processed/`

- Contains cleaned and standardized outputs.
- Processed files should be reproducible from code.
- Prefer efficient tabular formats such as Parquet when appropriate.

Do not add a persistent `features/` layer unless there is a demonstrated need to store engineered recommendation features.

---

## Phase 1 Design Principles

### Keep Raw and Processed Data Separate

Never overwrite source files.

All transformations should flow from:

```text
raw data
    ↓
preprocessing code
    ↓
processed data
```

### Prefer Explicit Transformations

Preprocessing should be easy to trace.

Prefer:

```python
players = standardize_positions(players)
players = standardize_playstyles(players)
players = validate_players(players)
```

over large functions that perform many unrelated transformations internally.

### Validate Assumptions

Important assumptions should fail clearly.

Examples:

- required columns are missing
- player identifiers are unexpectedly duplicated
- OVR contains invalid values
- age is outside a reasonable range
- club or position fields cannot be interpreted

Prefer informative exceptions over silently producing incorrect output.

### Avoid Premature Recommendation Logic

Phase 1 should not contain:

- squad-need scoring
- recommendation scoring
- transfer feasibility
- candidate ranking
- transfer-rumor scoring
- historical evaluation

Those belong to later phases described in `docs/PLAN.md`.

---

## Code Style

### Prioritize Readability

Code should be easy for another developer to understand without needing to reverse-engineer clever abstractions.

Prefer:

- descriptive names
- short functions with one clear responsibility
- straightforward control flow
- explicit transformations
- small reusable helpers where they reduce duplication

Avoid:

- unnecessary abstraction
- deeply nested logic
- clever one-liners that reduce readability
- large functions that mix loading, cleaning, validation, and output
- optimization that makes the implementation harder to understand without measurable benefit

---

## Readability vs. Optimization

Favor clean and maintainable code first, while avoiding obviously inefficient approaches.

Use efficient operations when they remain easy to understand.

For tabular processing:

- prefer vectorized pandas or Polars operations over row-by-row Python loops when practical
- avoid repeatedly reading the same file
- avoid unnecessary copies of large DataFrames
- batch transformations when doing so remains readable
- use appropriate dtypes where useful

Do not introduce complex optimization techniques unless profiling demonstrates a real bottleneck.

The preferred order is:

```text
correctness
    ↓
readability
    ↓
maintainability
    ↓
measured optimization
```

---

## Comments

Write comments sparingly and concisely.

Comments should explain **why** something is being done when the reasoning is not obvious.

Good:

```python
# Preserve unknown positions so schema changes fail during validation.
```

Avoid comments that simply restate the code:

```python
# Drop null values.
df = df.dropna()
```

Prefer clear code over explanatory comment blocks.

Do not leave verbose AI-style comments throughout the codebase.

---

## Docstrings

Use short docstrings for public or reusable functions.

Prefer concise descriptions such as:

```python
def load_players(path: Path) -> pd.DataFrame:
    """Load the raw EA FC player dataset."""
```

For functions with non-obvious inputs, outputs, or validation behavior, include enough detail to make the contract clear.

Do not add lengthy docstrings to trivial private helpers.

---

## Functions and Modules

Organize code around responsibilities rather than implementation steps.

A likely Phase 1 structure is:

```text
src/
└── ...
    ├── loading.py
    ├── preprocessing.py
    └── validation.py
```

Exact filenames may change if a clearer structure emerges.

Typical responsibilities:

### Loading

- locate source files
- read raw data
- enforce basic input expectations

### Preprocessing

- rename/select columns
- normalize text
- standardize positions
- standardize PlayStyles
- handle missing values
- normalize numeric fields

### Validation

- required-column checks
- identifier checks
- range checks
- schema checks
- processed-data validation

Keep high-level orchestration separate from reusable transformation logic when practical.

---

## Testing

Add focused tests for preprocessing behavior.

Prioritize tests for:

- required-column validation
- position normalization
- PlayStyle parsing
- numeric cleaning
- missing-value handling
- duplicate identifiers
- invalid values
- expected processed schema

Tests should be small and deterministic.

Prefer synthetic fixtures over depending on the full raw dataset for unit tests.

---

## Dependencies

Keep dependencies minimal.

Before adding a package, consider whether the standard library or an existing project dependency already solves the problem clearly.

Do not add large frameworks for functionality that can be implemented simply.

---

## File and Path Handling

Prefer `pathlib.Path` over hard-coded string paths.

Do not hard-code user-specific absolute paths.

Paths should work from a fresh clone of the repository.

---

## Reproducibility

A developer should be able to:

1. obtain the raw dataset
2. place it in the documented raw-data location
3. run the preprocessing workflow
4. reproduce the processed dataset

Any manual transformation required between these steps should be documented or automated.

---

## Before Making Changes

Before editing code:

1. Read the relevant existing files.
2. Check `docs/PLAN.md` when broader architectural context is needed.
3. Identify the smallest scope required for the current task.
4. Preserve existing interfaces unless a change is justified.
5. Avoid implementing future phases preemptively.

---

## After Making Changes

After completing a task:

1. Run relevant tests.
2. Verify the preprocessing output when applicable.
3. Check that no raw data was modified.
4. Remove unnecessary debug code.
5. Keep comments concise.
6. Summarize important implementation decisions.

If the work completes a meaningful portion of Phase 1, record enough context for the next task to understand:

- what was implemented
- important assumptions
- input/output schema decisions
- unresolved issues
- likely next step

---

## Future Phases

Later work may include:

- team profiling
- squad-need analysis
- candidate generation
- transfer feasibility
- feature engineering
- recommendation scoring
- ranking
- transfer-rumor integration
- historical backtesting
- optional learned ranking

These are intentionally outside the current Phase 1 scope.

Refer to:

```text
docs/PLAN.md
```

for the intended design before beginning any later phase.

Do not infer or implement future architecture solely from this file.
