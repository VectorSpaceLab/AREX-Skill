# Data workflows

## Layout-first validation

Before instantiating a loader, verify required directories and matching
basenames. For RobotWin, check both selected splits and every task's
`qpos`, `videos`, and `umt5_wan`; for AC-One/Aloha, check `videos`, `qpos`,
and `instructions`; for latent actions, check the four-way intersection
including `metas`. Keep a small `max_episodes` during validation.

## RoboTwin conversion

The public conversion workflow is two phases: optionally download selected
RoboTwin tasks, then convert raw episodes using a YAML configuration with
`source_root`, `target_root`, task selection, frame/video settings, and
language embedding options. It writes videos, qpos/action tensors, language
embeddings, and metadata. Downloading needs network and storage; conversion
can be CPU-heavy and writes substantial output. Review the target path and
available disk before execution, and do not treat `--help` as conversion
validation.

## LeRobot camera and T5 preparation

For LeRobot, first ensure the metadata/data/video tree is readable. Prefer
precomputing a concatenated camera feature once rather than stitching at every
sample. If T5 embeddings are absent, use the repository's cache-generation
workflow in a main process with WAN T5 assets; its worker guard deliberately
rejects encoder initialization inside DataLoader workers. Cache generation
updates episode metadata and writes `.pt` files, so make a backup and use a
lock-aware single preparation job.

## Camera concatenation

For three images loaded as arrays:

```python
from concat_cameras import resize_and_concatenate_frames
combined = resize_and_concatenate_frames(head, left_wrist, right_wrist)
```

Use `python scripts/concat_cameras.py --help` for the bundled CLI. It accepts
three image paths and an output path, validates matching channels and positive
sizes, and writes a deterministic image without touching dataset metadata.

## Safe smoke checks

Parser/help checks are safe. A tiny synthetic image triplet can exercise the
camera helper. Do not download model/data assets, invoke conversion on a real
root, rewrite LeRobot metadata, or create T5 caches as a routine skill check.
