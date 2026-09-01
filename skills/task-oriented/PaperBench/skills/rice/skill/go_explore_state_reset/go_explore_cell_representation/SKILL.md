---
name: go_explore_cell_representation
description: Build stable Go-Explore archive cell keys from structured or grid observations for bounded recovery experiments.
---

# Go-Explore Cell Representation

Use this skill when a recovery or implementation needs to convert raw environment observations into archive cells for Go-Explore Phase 1. Do not use it to choose actions, score trajectories, or evaluate robustification; it only defines state abstraction.

## Inputs

- A structured state dictionary such as `{"x": 1, "y": 2, "room": 0}` or a grid observation with coordinates.
- A cell configuration with `fields` for domain-knowledge cells or `bucket_size` for coordinate bucketing.

## Outputs

- A deterministic, hashable cell key represented as a tuple.
- Metadata describing the representation mode and selected fields.

## Workflow

1. Prefer domain fields when they are explicitly configured.
2. Validate that every requested field exists in the state.
3. Convert configured fields into a tuple ordered exactly as requested.
4. For coordinate-only states, bucket `x` and `y` by `bucket_size`.
5. Keep score, action preferences, and downstream control text out of the key.

## Validation

Run `python tests/test_cell_representation.py` or validate the full tree with `validate_skill_tree.py --run-tests`.

## Limitations

This skill does not decide which abstraction is best for a new environment. It provides deterministic mechanics for a chosen abstraction and makes collisions explicit through bucketing.
