---
name: ultralytics
description: "Use this skill for Ultralytics YOLO package workflows: CLI/Python
  model usage, data/config setup, train/val, prediction/results,
  export/deployment, tracking/solutions, model-family selection, and repo
  development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Ultralytics Repo Skill

Use this skill when a user asks for help with Ultralytics YOLO workflows, the `ultralytics` Python package, or this repository's public APIs and maintainer tasks. Ultralytics covers detection, instance segmentation, semantic segmentation, classification, pose, oriented boxes, tracking, model export, deployment helpers, and analytics solutions.

## Start Here

- Read `references/repo-provenance.md` when deciding whether this skill matches the current checkout or needs refresh.
- Read `references/routing-map.md` when a request spans more than one workflow or could route to multiple sub-skills.
- Read `references/version-and-capability-notes.md` for version-sensitive items such as YOLO26, semantic segmentation, SAM3, downloads, optional extras, and backend requirements.
- Read `references/shared-cli-config-keys.md` before validating `yolo TASK MODE arg=value` syntax or translating Python kwargs to CLI args.
- Run `scripts/check_ultralytics_env.py --json` to inspect an active environment without downloads, training, export, or media processing.

## Route by User Goal

- **Data and configuration**: use `sub-skills/data-and-configuration/SKILL.md` for dataset YAMLs, label layout, config defaults, CLI/Python arg translation, converters, and safe command planning.
- **Training and validation**: use `sub-skills/training-and-validation/SKILL.md` for `model.train()`, `model.val()`, `model.tune()`, `yolo train`, `yolo val`, resume, devices, metrics, and tuning.
- **Inference and results**: use `sub-skills/inference-and-results/SKILL.md` for `model.predict()`, `model(source)`, `yolo predict`, source types, streaming, batching, `Results` extraction, saving, and thread-safe inference.
- **Export and deployment**: use `sub-skills/export-and-deployment/SKILL.md` for `model.export()`, `yolo export`, `benchmark`, ONNX/OpenVINO/TensorRT/CoreML/TFLite and deployment-format troubleshooting.
- **Tracking and solutions**: use `sub-skills/tracking-and-solutions/SKILL.md` for `model.track()`, `yolo track`, tracker YAMLs, ReID/deep trackers, object counting, heatmaps, speed/queue/region workflows, Streamlit, and `yolo solutions`.
- **Model families and tasks**: use `sub-skills/model-families-and-tasks/SKILL.md` for choosing `YOLO`, `YOLOWorld`, `YOLOE`, `NAS`, `SAM`, `FastSAM`, or `RTDETR`, and for mapping detect/segment/semantic/classify/pose/OBB tasks to outputs.
- **Repo development**: use `sub-skills/repo-development/SKILL.md` for editing this repository, selecting focused tests, docs/style checks, optional extras, CI-like verification, and maintainer-safe native checks.

## Common First Decisions

- **CLI shape**: Ultralytics uses `yolo TASK MODE arg=value`; avoid normal `--flag value` syntax for YOLO config arguments.
- **Downloads**: names such as `yolo26n.pt`, `sam3.pt`, or `coco8.yaml` may download weights or datasets. Prefer explicit local paths for offline or deterministic work.
- **Task outputs**: detection uses boxes, segmentation uses boxes and masks, semantic segmentation uses dense `semantic_mask`, classification uses `probs`, pose uses keypoints, and OBB uses rotated geometry.
- **Side effects**: training, validation, prediction, export, tracking, and solutions can write runs, labels, media, or exports. Set `project`, `name`, `exist_ok`, `save=False`, or dry-run helper scripts when deterministic output matters.
- **Optional dependencies**: install extras narrowly. Use export extras only for export workflows, solutions extras for analytics apps, logging extras for integrations, and dev extras for repository checks.
- **Hardware**: GPU acceleration is optional for many inspections, but TensorRT, CUDA export, large training, and some ReID/deep trackers need compatible GPU packages and drivers.

## Safe Baseline

```bash
pip install ultralytics
python - <<'PY'
import ultralytics
print(ultralytics.__version__)
print("YOLO" in dir(ultralytics))
PY
yolo help
```

For local repository development, use editable install only in a disposable or project-specific environment and keep optional extras narrow. Do not install broad extras such as `dev`, `export`, `solutions`, or `logging` unless the selected workflow actually needs them.

## Bundled Helpers

- `scripts/check_ultralytics_env.py`: reports package versions, CLI availability, and optional backend modules in the active Python environment.
- Sub-skill helpers are dry-run planners or inspectors. They do not train, infer, export, download weights, open media, or run native tests unless their help text explicitly says so.
