---
name: evaluation
description: "Route LatentSync scoring, comparison, and diagnostic plotting for
  SyncNet confidence, SyncNet accuracy, FVD, and batch evaluation support."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation

Use this sub-skill after candidate videos, real/fake comparison folders, or a trained SyncNet checkpoint already exist and the task is to score, compare, or diagnose them.

Do **not** use this sub-skill to create single videos, launch training, or run the raw data-preparation pipeline.

## Route here when

- The user asks for SyncNet confidence, AV offset, SyncNet accuracy, FVD, or metric comparison.
- A generated-video folder needs batch scoring or a real-vs-fake metric.
- A SyncNet training checkpoint needs a validation-accuracy check or loss-curve plot.
- The blocker is likely a missing metric checkpoint, face detector, temp directory, ffmpeg/media backend, or evaluation config.
- The user asks what the preprocessing HyperIQA quality gate means.

## Route elsewhere when

- The user wants to generate a video, run Gradio, or tune generation parameters for one example: use the inference sub-skill.
- The user wants to start or configure U-Net/SyncNet training: use the training sub-skill.
- The user wants raw-video cleanup, affine face alignment, AV sync filtering, or visual-quality filtering: use the data-preparation sub-skill.
- The only generation need is producing candidate batches before evaluation; use this sub-skill only for the batch-evaluation framing, then route detailed generation setup to inference.

## Owned evidence surfaces

- `eval/eval_sync_conf.py` and `eval/eval_sync_conf.sh` for per-video or folder SyncNet confidence and AV offset.
- `eval/eval_syncnet_acc.py` and `eval/eval_syncnet_acc.sh` for checkpoint-level SyncNet validation accuracy.
- `eval/eval_fvd.py` and `eval/fvd.py` for real-vs-fake face-cropped FVD.
- `eval/inference_videos.py` as batch-candidate support, not as a metric.
- `eval/draw_syncnet_lines.py` and `scripts/plot_syncnet_curves.py` for SyncNet training-curve plots.
- `eval/hyper_iqa.py` as the visual-quality reference used by preprocessing.
- Detector/model internals used by the above: `eval/syncnet_detect.py`, `eval/syncnet/syncnet_eval.py`, `eval/syncnet/`, `eval/detectors/`, `latentsync/data/syncnet_dataset.py`, `latentsync/models/stable_syncnet.py`, `latentsync/utils/util.py`, and `configs/syncnet/*.yaml`.

## Start here

1. Read [`references/workflows.md`](references/workflows.md) to choose the correct evaluation entry point.
2. Read [`references/metrics.md`](references/metrics.md) before interpreting confidence, accuracy, FVD, or HyperIQA scores.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) before rerunning failed metric jobs.
4. Use [`scripts/run_evaluation.py`](scripts/run_evaluation.py) for parameterized SyncNet confidence, SyncNet accuracy, and FVD runs.
5. Use [`scripts/plot_syncnet_curves.py`](scripts/plot_syncnet_curves.py) only when plotting SyncNet checkpoint loss curves.

## Operating rules

- Treat missing checkpoints as prerequisites and name the missing file before retrying.
- Prefer explicit `--repo-root` and repo-root-relative paths; the bundled scripts do not depend on a fixed checkout location.
- Use isolated temp directories for SyncNet confidence runs, especially in parallel batch scoring.
- Keep FVD comparisons consistent: same crop logic, similar clip lengths, and enough videos per side for a meaningful covariance estimate.
- Keep HyperIQA in this sub-skill as a semantics/reference item; data-preparation owns running the visual-quality filter.
