---
name: inference-and-demos
description: "Use MMAction2 inference APIs, inferencers, labels, visualization
  outputs, and optional pose/detection demo flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMAction2 inference and demos

Use this sub-skill when the user needs MMAction2 action-recognition inference, high-level inferencer usage, label mapping, prediction dumps, headless visualization, or the optional human-detection/pose paths used by skeleton and spatio-temporal detection workflows.

## Route here for

- Direct recognizer inference with `init_recognizer` and `inference_recognizer`, including access to `ActionDataSample.pred_score`.
- High-level `ActionRecogInferencer` or `MMAction2Inferencer` workflows using local configs/checkpoints, model aliases, label files, `pred_out_file`, and `vid_out_dir`.
- Video-file, rawframe-folder, decoded-array, audio-feature `.npy`, and already-packed pose/dict inputs when the selected API supports that input form.
- CPU/GPU device choice, safe build-only checks, and troubleshooting of decode, visualization, optional dependency, and config/checkpoint mismatch failures.
- Optional skeleton recognition and spatio-temporal detection flows that depend on separately installed detector/pose packages and local checkpoints.

## Route elsewhere

- Dataset annotation formats, data preparation, config authoring, and `--cfg-options` design: `../data-and-configs/SKILL.md`.
- Training, testing, evaluation metrics, distributed launch, and work directory management: `../training-and-evaluation/SKILL.md`.
- Model-family selection beyond inference, custom modules, registry extension, export, and deployment: `../models-and-extension/SKILL.md`.

## Choose the smallest safe entry point

1. **Build/config smoke only**: run [`scripts/mmaction2_inference_smoke.py`](scripts/mmaction2_inference_smoke.py) with `--config CONFIG.py --check-build-only`. It imports MMAction2, parses a local config, builds with `checkpoint=None`, and never downloads weights.
2. **Need raw scores or an `ActionDataSample`**: use `init_recognizer(..., device="cpu")` plus `inference_recognizer(...)`; read `result.pred_score` and map class indices with a user-supplied label file.
3. **Need packaged prediction/visualization output**: use `ActionRecogInferencer` for action recognition, especially when selecting `input_format="video"`, `"rawframes"`, or `"array"`.
4. **Need a unified demo-like wrapper**: use `MMAction2Inferencer(rec=..., rec_weights=..., device=..., label_file=...)`; use it one input at a time when saving visualizations.
5. **Need skeleton or spatio-temporal detection**: first confirm optional detector/pose dependencies and local detector/pose/action checkpoints; then follow the staged workflows in the references.

## Safety defaults

- Prefer `device="cpu"` unless the user explicitly asks for CUDA and the runtime proves CUDA is available. Several public APIs default to `"cuda:0"`, so pass the device explicitly on CPU-only hosts.
- Prefer local config and checkpoint paths. Model aliases or full model names can trigger metadata weight lookup; do not rely on remote downloads for smoke checks.
- Keep GUI display disabled on headless servers (`show=False`); save visualizations with `vid_out_dir` or request `return_vis=True` in code.
- When dumping predictions, use a file extension supported by MMEngine serialization and keep `return_datasamples=False` unless the consumer explicitly needs `ActionDataSample` objects.

## Local references

- [`references/api-reference.md`](references/api-reference.md) — verified signatures, defaults, input forms, result objects, devices, labels, and checkpoint/model selection.
- [`references/demo-workflows.md`](references/demo-workflows.md) — concrete API snippets, demo-like command patterns, visualization, skeleton, and spatio-temporal detection workflows.
- [`references/troubleshooting.md`](references/troubleshooting.md) — common inference failures and recovery steps, including optional dependency and video decode errors.
- [`scripts/mmaction2_inference_smoke.py`](scripts/mmaction2_inference_smoke.py) — safe build/inference smoke helper with signature printing and no downloads by default.
