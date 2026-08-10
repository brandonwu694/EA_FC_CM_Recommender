# EA FC Career Mode Player Recommender — Project Plan

## 1. Project Goal

Build a contextual recommendation system for EA FC Career Mode that recommends realistic and useful transfer targets based on:

- the user's current club
- the position they want to strengthen
- the quality and depth of the current squad
- candidate player quality and potential
- relevant PlayStyles
- positional versatility
- transfer feasibility
- real-world transfer rumors

The final system should return the **top 3–5 recommended signings**, each with an interpretable score out of 10 and an explanation of why the player is a good fit.

---

## 2. Data Sources

### Primary Player Dataset

Use an EA FC player dataset containing, where available:

- overall rating
- potential
- age
- positions
- PlayStyles
- current club
- league
- market value
- wage
- detailed player attributes

### Transfer Rumor Data

Store:

- player
- linked club
- source
- publication date
- rumor strength or reliability

### Potential Future Data Sources

- historical completed transfers
- historical squad snapshots
- club transfer budgets
- club or league prestige information

---

## 3. User Inputs

### Required Inputs

- club
- desired position

Example:

```text
Club: Chelsea
Position: CDM
```

### Optional Future Inputs

- preferred age range
- immediate starter vs. prospect
- maximum transfer fee
- preferred tactical role
- realism preference

These are not required for the initial version.

---

## 4. Overall Recommendation Pipeline

```text
User selects club + position
            ↓
Build current squad profile
            ↓
Identify positional needs
            ↓
Generate candidate players
            ↓
Apply feasibility filters
            ↓
Engineer candidate/team features
            ↓
Calculate recommendation score
            ↓
Rank candidates
            ↓
Return top 3–5 recommendations
```

---

# Implementation Phases

The project should be implemented one phase at a time. Complete, test, and summarize each phase before moving to the next.

---

## Phase 1 — Data Ingestion and Preprocessing

### Goal

Create a reliable player-data pipeline that transforms the raw EA FC dataset into a clean format suitable for later recommendation logic.

### Tasks

1. Inspect the raw dataset schema.
2. Identify the columns required by the project.
3. Implement a reusable data loader.
4. Standardize:
   - club names
   - league names
   - positions
   - PlayStyles
   - missing values
   - numeric columns
5. Validate important fields such as:
   - player identifiers
   - overall rating
   - age
   - club
   - positions
6. Save a cleaned processed dataset.

### Suggested Data Layout

```text
data/
├── raw/
└── processed/
```

The raw layer should remain unchanged. The processed layer should contain cleaned, standardized data used by the application.

### Deliverable

A reproducible processed player dataset and reusable preprocessing code.

---

## Phase 2 — Team Profile

### Goal

Analyze the selected club so later recommendations can be evaluated relative to the team's current squad.

### Positional Features

For each position, calculate:

- starter OVR
- backup OVR
- average positional OVR
- number of players
- average age
- highest potential
- positional depth
- PlayStyle coverage

### Team-Level Features

Calculate:

- starting XI average OVR
- squad average OVR
- average squad age
- general club quality level

### Example

```text
Team average starter OVR: 84

ST starter OVR: 79
CDM starter OVR: 87
```

The system should recognize ST as a larger weakness than CDM.

### Deliverable

A reusable team-profile representation generated from a selected club.

---

## Phase 3 — Squad Need

### Goal

Estimate how strongly the selected club needs reinforcement at each position.

### Inputs

Consider:

- current starter quality
- backup quality
- number of players capable of playing the position
- positional OVR relative to team standard
- age of existing players
- potential of existing players

### Example

```text
ST Need Score: 0.92
CAM Need Score: 0.21
CB Need Score: 0.55
```

The user may still request any position, but the final recommendation score should reflect how strongly the club needs reinforcement there.

### Deliverable

A normalized positional-need score for the selected club.

---

## Phase 4 — Candidate Generation

### Goal

Reduce the full player database to a manageable set of plausible transfer candidates before detailed ranking.

### Candidate Criteria

Initial filters may include:

- can play the requested position
- not currently at the selected club
- meets a broad minimum quality threshold
- not dramatically below the club's level
- reasonably transferable

Position compatibility should include:

- primary position
- secondary positions
- positions that can reasonably be converted to the requested position

Filters should remain permissive enough that strong candidates are not removed too early.

### Target

```text
All EA FC players
      ↓
~100–500 candidates
```

### Deliverable

A candidate-generation function that returns plausible players for a selected club and position.

---

## Phase 5 — Transfer Feasibility

### Goal

Prevent obviously unrealistic recommendations.

### Potential Signals

- player market value
- wage
- buying club strength
- selling club strength
- league reputation
- player OVR
- estimated transfer budget
- club prestige difference

Some feasibility signals may be used as hard filters, while others may contribute to the realism score.

### Example

```text
Real Madrid → elite player
high feasibility

Lower-league club → elite Real Madrid player
extremely low feasibility
```

The first version does not need a perfect financial model. The purpose is to eliminate clearly implausible recommendations.

### Deliverable

A transfer-feasibility score or filtering layer.

---

## Phase 6 — Feature Engineering

### Goal

Construct features describing how well each candidate fits the selected club.

### Player Features

- OVR
- potential
- age
- positions
- PlayStyles
- market value
- wage

### Team-Relative Features

- OVR improvement over current starter
- OVR improvement over positional average
- depth improvement
- age-profile improvement
- potential improvement

### Role Features

- relevant PlayStyle count
- PlayStyle compatibility
- primary-position compatibility
- secondary-position usefulness
- ease of positional conversion

### Contextual Features

- squad need
- transfer feasibility
- real-world rumor strength

### Deliverable

A recommendation-ready feature representation for each candidate.

---

## Phase 7 — Recommendation Score

### Goal

Create an interpretable rule-based ranking system.

The initial score should sum to **10 points**:

```text
Recommendation Score =
Realism +
Quality Improvement +
Squad Need +
Player / Role Fit
```

Each category contributes up to **2.5 points**.

---

### 7.1 Realism — 2.5 Points

Measure whether the transfer makes sense in the real world.

Consider:

- transfer rumor strength
- source credibility
- number of independent reports
- rumor recency
- financial feasibility
- club/player level compatibility

Example interpretation:

```text
2.5 → heavily linked and highly plausible
2.0 → realistic transfer
1.5 → plausible but little evidence
1.0 → no rumor, but reasonable
0.0 → extremely unrealistic
```

A player should not automatically receive zero simply because no rumor exists.

---

### 7.2 Quality Improvement — 2.5 Points

Measure how much the player improves the requested position.

Primary signal:

```text
candidate OVR - current starter OVR
```

Additional signals:

- candidate OVR vs. positional average
- potential improvement
- backup or rotation improvement

Avoid using overall squad OVR change as the primary measure because one signing usually changes it very little.

---

### 7.3 Squad Need — 2.5 Points

Measure how badly the club needs reinforcement at the requested position.

Consider:

- starter quality
- backup quality
- positional depth
- team-relative weakness
- age profile
- potential of existing players

Example:

```text
Only one 78-rated ST on an 84-rated team
→ very high squad-need score

Three CAMs rated 88, 85, and 83
→ very low squad-need score
```

---

### 7.4 Player / Role Fit — 2.5 Points

Combine:

- PlayStyle fit
- age
- potential
- positional versatility
- position compatibility

#### PlayStyles

Do not simply reward a higher total number of PlayStyles.

Create role-specific PlayStyle groups.

Example:

```text
Holding CDM

- Intercept
- Anticipate
- Bruiser
- Long Ball Pass
- Press Proven
```

Measure how well the candidate's PlayStyles match the intended role.

#### Age

Do not assume younger is always better.

Evaluate age alongside:

- OVR
- potential
- team expectations
- development runway

A title contender may prefer an elite 28-year-old starter over a promising 20-year-old prospect.

#### Positional Versatility

Reward useful versatility rather than simply counting positions.

A secondary position should be more valuable when it covers another area of squad need.

---

## Phase 8 — Ranking and Recommendation Output

### Goal

Rank candidates and return the strongest recommendations with clear explanations.

### Ranking

Calculate the final score for each candidate and sort in descending order.

Example:

```text
Player A    9.1
Player B    8.7
Player C    8.4
Player D    7.9
Player E    7.6
```

Return the top 3–5 recommendations.

### Recommendation Explanation

Each result should include the score breakdown and a short explanation.

Example:

```text
1. Player A — 9.1 / 10

Realism:              2.2 / 2.5
Quality Improvement:  2.4 / 2.5
Squad Need:           2.5 / 2.5
Player Fit:           2.0 / 2.5

Why:
- Improves starting ST from 80 → 87 OVR
- ST is currently the weakest position in the squad
- Strong relevant PlayStyles
- Age 23 with additional development potential
- Has been credibly linked with the club
```

The system should remain explainable rather than returning only a ranked list.

### Deliverable

Top 3–5 recommendations with score breakdowns and explanations.

---

## Phase 9 — Transfer Rumor Integration

### Goal

Add real-world transfer context without introducing data leakage.

### Required Fields

- player
- linked club
- source
- publication date
- reliability or rumor-strength score

### As-Of Date

Rumor information must be filtered using an explicit cutoff date.

Example:

```text
Evaluation date: June 1, 2026
```

Only reports published on or before that date may influence recommendations generated for that snapshot.

### Deliverable

A reproducible rumor-data pipeline that can be joined to candidate recommendations.

---

## Phase 10 — Evaluation and Backtesting

### Goal

Evaluate the recommender using completed real-world transfers.

Do not rely only on:

```text
Actual transfer scored ≥ 8 / 10
```

This may remain an intuitive secondary metric, but ranking quality should be the primary evaluation.

### Evaluation Process

For each completed transfer:

```text
Build the club's squad before the transfer
          ↓
Request the transferred player's position
          ↓
Generate recommendations
          ↓
Determine where the actual signing ranked
```

Example:

```text
1. Candidate A
2. Candidate B
3. Actual signing
4. Candidate C
5. Candidate D
```

The completed transfer appeared in the top 3 recommendations.

### Evaluation Metrics

Potential metrics include:

- Hit Rate @ 3
- Hit Rate @ 5
- Recall @ 5
- Mean Reciprocal Rank
- NDCG @ 5

Secondary metric:

- percentage of completed transfers scoring at least 8 / 10

### Historical Backtesting

Once the initial evaluation works, test across multiple transfer windows rather than relying on only one summer.

### Deliverable

A repeatable evaluation pipeline and documented recommender performance.

---

# Future Extension — Learned Ranking Model

Machine learning is optional and should only be introduced after the rule-based system is complete and evaluated.

Historical training data could contain:

```text
team
player
date
team squad before transfer
player attributes
transfer outcome
```

Possible learned objective:

```text
P(player is a suitable signing | team, player, context)
```

Alternatively, use a learning-to-rank model to directly rank candidates.

The hand-engineered recommendation features can become inputs to the learned model.

---

# Development Strategy

## V1 — Rule-Based Recommender

Build:

- data preprocessing
- team analysis
- squad-need calculation
- candidate generation
- transfer feasibility
- feature engineering
- weighted scoring
- ranking
- recommendation explanations

No machine learning is required.

## V2 — Historical Evaluation

Add:

- transfer rumor integration
- historical squad snapshots
- completed transfers
- ranking metrics
- backtesting

## V3 — Optional Learned Ranking

Only if justified by the results:

- create labeled historical examples
- train a ranking or probability model
- compare learned ranking against the rule-based baseline

---

# AI-Assisted Development Workflow

Use this document as the high-level roadmap rather than providing the entire project scope to an AI assistant for every implementation task.

For each phase:

1. Introduce the current phase and its goal.
2. Provide only the files and context relevant to that phase.
3. Break the phase into small implementation tasks.
4. Implement and test each task.
5. Validate the phase output.
6. Summarize:
   - what was implemented
   - important design decisions
   - resulting inputs and outputs
   - unresolved issues
7. Use that summary as context when beginning the next phase.

Example:

```text
Full Project Plan
        ↓
Current Phase
        ↓
Small Implementation Task
        ↓
Test / Validate
        ↓
Summarize Decisions
        ↓
Next Task
```

Avoid asking an AI assistant to implement later recommendation, ranking, or evaluation stages before their dependencies are complete.

---

# Final Scope

The core project is:

> Build an explainable contextual recommendation system that identifies and ranks realistic EA FC Career Mode transfer targets based on a club's existing squad, requested position, candidate quality, tactical characteristics, transfer feasibility, and real-world transfer information.

Minimum viable pipeline:

```text
Team + Position
      ↓
Team Analysis
      ↓
Candidate Generation
      ↓
Feasibility
      ↓
Feature Engineering
      ↓
10-Point Fit Score
      ↓
Ranking
      ↓
Top 3–5 + Explanation
```

The rule-based recommender plus historical evaluation is sufficient for a complete portfolio project. A learned ranking model should remain an optional extension rather than a requirement.
