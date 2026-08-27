---
name: data-preparation
description: "Prepare MMAudio audio/video feature manifests, memmaps, and extraction plans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-preparation

Use this sub-skill when you need to turn raw MMAudio audio, video, and caption inputs into clip manifests, feature-extraction plans, or TensorDict memmaps for later training.

## Use this route for

- Partitioning long audio into clip metadata without saving extra audio files.
- Checking audio caption TSVs against clip TSVs before feature extraction.
- Validating video subset TSVs and media roots before feature extraction.
- Understanding TensorDict memmap layouts and the TSVs that accompany them.
- Planning 16kHz vs 44.1kHz feature extraction and the expected tensor shapes.

## Do not use this route for

- Training loop, checkpoints, EMA synthesis, or distributed optimization; use `training`.
- Batch generation or evaluation metrics; use `evaluation`.
- Demo, CLI inference, or API command building; use `inference`.

## Read first

- `references/data-formats.md` for TSV columns, memmap layouts, dataset classes, and fixture names.
- `references/feature-extraction.md` for clip partitioning, extraction flow, mode switches, and command templates.
- `references/troubleshooting.md` for duplicate IDs, missing files, short media, distributed setup, decode, and OOM failures.

## Skill-owned scripts

- `scripts/partition_audio_clips.py` — deterministic CPU clip partitioner that writes `id`, `name`, `start_sample`, and `end_sample`.
- `scripts/inspect_feature_plan.py` — validates a planned audio or video extraction run and prints the command to launch it.

## Typical workflow

1. Confirm the fixture or dataset manifest names and the expected TSV columns.
2. If needed, partition audio into clips without saving audio copies.
3. Validate the planned extraction inputs, output paths, and 16k/44k mode.
4. Check that the expected memmap directory and TSV names match the plan.
5. Run the extractor only after the plan report is clean and the required weights are in place.

## Output contracts at a glance

- Audio clip manifests: `id`, `name`, `start_sample`, `end_sample`.
- Audio feature outputs: `{basename(output_dir)}/` plus `{basename(output_dir)}.tsv`.
- Video feature outputs: `vgg-{split}/` plus `vgg-{split}.tsv`.

## Route on

- If you now need DDP training, switch to `training`.
- If you now need demo generation or API usage, switch to `inference`.
- If you now need batch metrics or onset scoring, switch to `evaluation`.
