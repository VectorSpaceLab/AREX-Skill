---
name: opal_offline_segment_protocol
description: Prepare fixed-horizon offline state-action segments for OPAL primitive discovery and downstream latent relabeling.
---

# OPAL Offline Segment Protocol

## When To Use
Use this skill when an OPAL-style recovery needs to transform offline trajectories into fixed-horizon primitive-learning segments. Do not use it to train the primitive model or decide high-level latent actions.

## Inputs
- JSON trajectories with `states`, `actions`, and optional `rewards`.
- Primitive horizon `c` greater than zero.
- A segmentation mode; the bundled script implements deterministic non-overlapping windows.

## Outputs
- Segment records with `trajectory_id`, `start`, `horizon`, `states`, `actions`, `initial_state`, and optional reward summaries.
- A summary containing segment count and dropped short tails.

## Workflow
1. Validate that each trajectory has enough actions and states.
2. Slice non-overlapping windows of length `c`.
3. Preserve the first state as `s0` for the OPAL prior.
4. Keep reward metadata separate from primitive segment content.
5. Report dropped tails rather than padding silently.

## Validation
Run:

```bash
python tests/test_segment_protocol.py
```

## Limitations
The script is intentionally small and deterministic. It does not implement overlapping windows, padding, D4RL loading, or neural preprocessing.
