---
name: retargeting-and-motion-data
description: "Prepare ProtoMotions MotionLib data, conversion pipelines, PyRoki
  retargeting, contact labels, FPS handling, and motion utility checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProtoMotions retargeting and motion data

Use this sub-skill for MotionLib schemas, AMASS/PHUMA/SEED/Kimodo data preparation, SMPL/SOMA/G1/H1 retargeting, PyRoki pipeline reasoning, contact-label handling, FPS/downsampling, motion filtering, and packaged-motion utilities.

## Read first

- `references/motion-data-formats.md`: `.motion`, MotionLib `.pt`, YAML lists, contacts, FPS, and body alignment.
- `references/retargeting-pipeline.md`: SMPL/SOMA keypoint extraction, PyRoki retargeting, contacts, conversion, and packaging sequence.
- `references/conversion-utilities.md`: useful conversion/helper surfaces and when to run or skip them.
- `references/troubleshooting.md`: data, contact, filter, and environment failures.
- `scripts/subset_motion_lib.py`: CPU utility to sample every Nth motion from a packaged MotionLib.
- `scripts/summarize_motion_lib.py`: safe MotionLib `.pt` structure summary.

## Decision flow

1. Identify source skeleton/data: AMASS SMPL, SMPL-X, SOMA, PHUMA, SEED G1 CSV, Kimodo-generated CSV/NPZ, or already packaged MotionLib.
2. Confirm target robot/skeleton: `smpl`, `soma23`, `g1`, or `h1_2` are the main evidence-backed routes.
3. For robot retargeting, use separate ProtoMotions and PyRoki environments.
4. Preserve source motion contacts when retargeting whenever the pipeline provides them; re-computing contacts from imperfect retargeted output can be less reliable.
5. Package final `.motion` files into a MotionLib `.pt` before training.
6. Start with a small subset (`skip_freq` or `subset_motion_lib.py`) before full AMASS/SEED scale.

## Safe utilities

```bash
python scripts/summarize_motion_lib.py <motion_lib.pt>
python scripts/subset_motion_lib.py <input.pt> <output.pt> --sample-every 200
```

These helpers operate on local `.pt` files and do not require simulator execution.

## Retargeting cautions

- PyRoki optimizes trajectories and may require CUDA/JAX dependencies separate from ProtoMotions.
- The full AMASS-to-robot pipeline can be long and data-heavy; use skip/subset parameters for smoke tests.
- Contact labels must match motion length after FPS downsampling.
- Motion filters can drop invalid outputs; inspect thresholds before assuming conversion failed.
- If working from a package-only install, require user-provided conversion scripts or a source checkout because some data-prep scripts are not part of the installed package.
