---
name: go_explore_return_then_explore_loop
description: Execute a bounded Go-Explore return-then-explore Phase 1 loop in resettable sparse-reward environments.
---

# Go-Explore Return Then Explore Loop

Use this skill to run the central Go-Explore Phase 1 mechanism after cell encoding and archive update rules are available. It is appropriate for resettable or replayable environments where a selected archive state can be restored before exploratory actions are taken.

## Inputs

- A resettable environment exposing state snapshots, actions, and rewards.
- Cell encoder and archive update/select functions.
- Iteration count, rollout horizon, action schedule, and random seed.

## Outputs

- Expanded archive.
- Best trajectory, score, and goal flag.
- Trace proving selected cells were restored before exploration.

## Workflow

1. Insert the start state into the archive.
2. Select a cell from the archive with seeded deterministic selection.
3. Restore the saved state for that cell without exploratory actions.
4. Execute exploratory actions for a bounded horizon.
5. Encode each visited state and update the archive using score and length rules.
6. Repeat until the iteration budget ends or the goal is reached.

## Validation

Run `python tests/test_return_loop.py` or validate with `validate_skill_tree.py --run-tests`.

## Limitations

This skill is a bounded recovery implementation, not an Atari emulator. It is faithful to the reset/archive/explore mechanism but does not perform neural robustification.
