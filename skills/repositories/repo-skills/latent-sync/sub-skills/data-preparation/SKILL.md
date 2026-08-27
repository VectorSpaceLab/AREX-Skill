---
name: data-preparation
description: "Convert raw videos into the training-ready, face-aligned,
  AV-synced, quality-filtered LatentSync data tree."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-preparation

Use this sub-skill when a task needs LatentSync's raw-video preprocessing path: validating prerequisites, planning a run, executing safe stages, recovering from interrupted preprocessing, or explaining why a data-prep gate rejected clips.

## Route here for

- Raw `.mp4` tree cleanup, FPS/audio resampling, scene splitting, and 5-second segment generation.
- Face alignment and resizing for training-ready talking-head clips.
- AV sync confidence filtering, audio offset correction, and visual-quality filtering.
- Optional resolution and post-affine face-presence gates for noisy corpora.
- Preflight checks for inputs, codecs, auxiliary checkpoints, CUDA visibility, Python imports, and scratch directories.

## Entry points

- [`scripts/check_data_prep_inputs.py`](scripts/check_data_prep_inputs.py) — safe preflight checker that does not mutate data or run the heavy pipeline.
- [`scripts/run_data_pipeline.py`](scripts/run_data_pipeline.py) — parameterized planner/runner adapted from the repo's `data_processing_pipeline.sh` and `preprocess/data_processing_pipeline.py`.
- [`references/workflows.md`](references/workflows.md) — stage order, multiprocessing model, GPU requirements, checkpoints, and rerun strategy.
- [`references/data-formats.md`](references/data-formats.md) — raw input shape, intermediate sibling directories, final `high_visual_quality/` layout, and scratch semantics.
- [`references/troubleshooting.md`](references/troubleshooting.md) — codec, checkpoint, face-detection, GPU, worker-pool, and temp-dir failures.

## Source surfaces distilled

- Pipeline orchestration: `preprocess/data_processing_pipeline.py`, `data_processing_pipeline.sh`.
- CPU stages: `preprocess/remove_broken_videos.py`, `preprocess/resample_fps_hz.py`, `preprocess/detect_shot.py`, `preprocess/segment_videos.py`.
- Optional gates: `preprocess/filter_high_resolution.py`, `preprocess/remove_incorrect_affined.py`.
- GPU stages: `preprocess/affine_transform.py`, `preprocess/sync_av.py`, `preprocess/filter_visual_quality.py`.
- Pipeline internals: `latentsync/utils/affine_transform.py`, `latentsync/utils/av_reader.py`, `latentsync/utils/image_processor.py`, `latentsync/utils/face_detector.py`, `latentsync/utils/util.py`, `eval/syncnet_detect.py`, `eval/hyper_iqa.py`, `eval/syncnet/syncnet.py`, `eval/syncnet/syncnet_eval.py`, `configs/syncnet/*.yaml`, `docs/syncnet_arch.md`.

## Boundaries

Do not use this sub-skill for training launches, model checkpoint selection for U-Net/SyncNet training, single-pair inference, Gradio/Cog serving, or evaluation metrics that are not data-prep gates. Treat `tools/download_web_videos.py` as reference-only and do not run it from bundled helpers because it is network-bound and shells out to external downloaders.

## Operating rule

Run the preflight checker before any real data-prep run. Missing auxiliary checkpoints or CUDA should be surfaced as explicit prerequisites before worker pools start. The first pipeline stage deletes broken raw videos in place, so run the full executor only on a disposable copy of the raw tree or after consciously passing the destructive-input flag.
