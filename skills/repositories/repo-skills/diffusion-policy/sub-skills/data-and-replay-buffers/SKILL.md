---
name: data-and-replay-buffers
description: "Inspect Diffusion Policy dataset interfaces, ReplayBuffer stores,
  SequenceSampler horizons and padding, and normalizer contracts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# data-and-replay-buffers

Use this sub-skill when you need to understand or validate Diffusion Policy data stores, dataset adapters, sequence sampling, and normalization without touching training loops or policy internals.

## Use for
- zarr or zip ReplayBuffer inspection
- episode counts, `episode_ends`, shapes, dtypes, chunking, and length mismatches
- low-dimensional versus image dataset samples and `shape_meta` routing
- `SequenceSampler` horizon, padding, `episode_mask`, and `key_first_k` behavior
- normalizer selection, key lookup, and dataset conversion routes

## Route elsewhere
- training, evaluation, Ray multiruns, and metrics aggregation -> `training-and-evaluation`
- policy inference, checkpoint logic, model families, and losses -> `policies-and-models`
- live robot capture, RealSense, UR5, SpaceMouse, and safety-gated execution -> `real-robot-operations`

## Fast validation
1. Run `python scripts/inspect_replay_buffer.py --path <replay-buffer> --max-keys 12` from this sub-skill directory to inspect a zarr directory or zip store without modifying it.
2. Add `--json` when another tool should consume the summary.
3. Use the checklist in `references/troubleshooting.md` when episode lengths, keys, or shapes are inconsistent.

## What to read next
- `references/data-and-replay-buffers.md`
- `references/api-reference.md`
- `references/troubleshooting.md`

## Bundled helper
- `scripts/inspect_replay_buffer.py` — read-only inspector for ReplayBuffer zarr directories and zip stores.

## First checks when data looks wrong
- Compare `meta/episode_ends[-1]` to every `data/*` leading dimension.
- Confirm the sample shape matches the dataset family: flat low-dim tensor versus dict of image and state keys.
- Confirm the normalizer keys match the returned sample keys exactly.
- Treat repeated boundary frames as expected padding, not corruption.
