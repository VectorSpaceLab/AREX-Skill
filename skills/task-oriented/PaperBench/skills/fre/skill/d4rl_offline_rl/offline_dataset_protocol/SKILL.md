---
name: offline_dataset_protocol
description: Validate fixed offline reinforcement learning transition datasets and summarize D4RL-style provenance before recovery experiments.
---

# Offline Dataset Protocol

Use this skill when a recovery or benchmark task needs to verify that training data is a fixed offline RL transition dataset. Do not use it to collect online rollouts, run simulators, or claim that synthetic proxy data is a real D4RL dataset.

## Inputs

- A JSON file containing either a list of transition records or an object with a `transitions` list.
- Each transition must contain `observation`, `action`, `reward`, `next_observation`, `terminal`, and `timeout`.
- Optional metadata fields such as `source`, `domain`, `variant`, and `is_resource_derived`.

## Outputs

- A JSON validation report with `ok`, counts, `quality_tags`, `errors`, and `metadata`.
- The report preserves whether the dataset is synthetic proxy data, resource-derived data, or a real benchmark item.

## Workflow

1. Load the dataset JSON without mutating it.
2. Confirm that every transition has the required keys.
3. Coerce rewards to floats and terminal/timeout markers to booleans.
4. Count transitions, terminal endings, timeout endings, and combined episode endings.
5. Add the `fixed_dataset` tag and optional tags from metadata.
6. Reject empty datasets or missing fields.

## Validation

Run `python scripts/validate_offline_dataset.py <dataset.json>` for CLI validation. Run `python -m pytest tests` or the Distiller `validate_skill_tree.py --run-tests` command for deterministic tests.

## Limitations

This skill validates dataset structure and provenance; it does not implement a full D4RL environment, simulator, or benchmark download.
