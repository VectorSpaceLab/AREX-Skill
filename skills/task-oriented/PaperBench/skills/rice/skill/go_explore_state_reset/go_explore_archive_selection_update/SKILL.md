---
name: go_explore_archive_selection_update
description: Maintain and sample Go-Explore archive entries using score, length, and exploration metadata.
---

# Go-Explore Archive Selection and Update

Use this skill when implementing Phase 1 archive mechanics for Go-Explore-style exploration. It owns insertion, replacement, and deterministic sampling of archive cells. Do not use it for cell encoding or environment stepping.

## Inputs

- A candidate trajectory record with `cell_key`, `state`, `actions`, `score`, and optional `length`.
- An archive dictionary keyed by encoded cells.
- Optional seeded random generator and selection settings.

## Outputs

- An updated archive entry when the candidate is new or improves an existing entry.
- A selected archive entry for return-then-explore.

## Workflow

1. Insert candidates for unseen cells.
2. Replace existing entries only if the candidate has higher cumulative score or equal score with a shorter trajectory.
3. Track update and selection counts for auditability.
4. Sample cells with a deterministic seeded weighted rule that favors high score and low selection count.
5. Return both the selected key and entry so recovery logs can prove which frontier was explored.

## Validation

Run `python tests/test_archive.py` or validate with `validate_skill_tree.py --run-tests`.

## Limitations

This skill intentionally keeps the weighting simple for bounded recovery. Full Atari-scale Go-Explore can use richer weights, but the replacement invariant should remain the same.
