---
name: recommendation-and-analysis
description: "Turn fitted Surprise models or prediction lists into ranked
  recommendations, precision/recall@k summaries, and safe dump/load roundtrips."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Recommendation and Analysis

Use this sub-skill when you already have a fitted Surprise model, a `Trainset`, or a list of `Prediction` objects and you need to:
- build an anti-testset from known users and items,
- rank candidate items into top-N recommendations,
- compute precision@k / recall@k over prediction lists,
- serialize predictions or fitted algorithms with `dump.dump` / `dump.load`,
- interpret `Prediction` records and raw ids safely.

## What this route covers
- `Trainset.build_anti_testset(fill=None)` and fill behavior
- stable top-N ranking over `Prediction` outputs
- precision/recall@k conventions, including zero-division handling
- `dump.dump` and `dump.load` roundtrips using temp files
- raw-id handling for recommendation output

## What this route excludes
- model fitting or tuning
- cross-validation and search
- algorithm internals beyond cross-links and the minimal `Prediction` / `AlgoBase` contract

## Entry points
- `references/recommendation.md` for usage patterns and output contracts
- `references/troubleshooting.md` for common failure modes
- `scripts/top_n_smoke.py` for anti-testset ranking and tie ordering
- `scripts/precision_recall_smoke.py` for zero-division cases in precision/recall@k
- `scripts/serialize_smoke.py` for temp-file dump/load roundtrip

## Use when
- you already have `algo.test(...)` output and want ranked recommendations
- you need per-user precision/recall@k from a `Prediction` list
- you need to persist predictions or a fitted algorithm without keeping the original process alive

## Handoff notes
If you still need trainset creation or model fitting, hand off to the data-loading or prediction-algorithms route first, then return here with a fitted model or predictions.
