---
name: data-and-configuration
description: "Author and validate Ultralytics dataset YAMLs, translate Python
  kwargs to safe YOLO CLI arg=value commands, inspect default config keys, and
  plan data/config commands before training, prediction, validation, or export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Data and Configuration

Use this sub-skill when the task is about Ultralytics dataset YAMLs, data layout checks, CLI/Python argument translation, config defaults, converters, or safe command planning. It is the right entry point before launching expensive `train`, `val`, `predict`, `track`, `benchmark`, or `export` runs.

## Route Here For

- Writing or reviewing `data.yaml` files for detection, segmentation, pose, OBB, semantic segmentation, and classification datasets.
- Converting Python API kwargs like `model.train(data="custom.yaml", epochs=10)` into canonical `yolo TASK MODE arg=value` commands.
- Checking whether config keys are known, deprecated, removed, or likely task/mode-specific.
- Planning a command that should be reviewed before it downloads data, opens media streams, trains, exports, or writes output files.
- Choosing safe converter/split APIs such as COCO-to-YOLO, DOTA-to-YOLO-OBB, mask-to-YOLO-seg, or dataset autosplit.

## Fast Path

1. Read `references/workflows.md` for dataset YAML schemas, CLI syntax, converters, and command-planning patterns.
2. Use `scripts/validate_dataset_yaml.py --help` and run it on local YAMLs before training or validation.
3. Use `scripts/plan_yolo_command.py --help` to validate kwargs and render a safe CLI command without invoking `yolo`.
4. If the next step is actual training or validation, hand off to `../training-and-validation/SKILL.md` after data/config checks pass.
5. If the next step is prediction/results interpretation, hand off to `../inference-and-results/SKILL.md`; for export, hand off to `../export-and-deployment/SKILL.md`; for model/task selection, hand off to `../model-families-and-tasks/SKILL.md`.

## Safe Defaults

- Prefer tiny smoke-test datasets and low-cost arguments while planning: `epochs=1`, `batch=1`, `imgsz=320`, `device=cpu`, `workers=0`, `save=False` where the mode supports it.
- Treat `download:` entries in dataset YAML as risky until reviewed; they may fetch large archives, run shell commands, or execute Python snippets when autodownload is enabled.
- Do not translate Python kwargs into `--flag value` syntax. Ultralytics CLI expects space-separated `arg=value` tokens after optional `TASK` and required `MODE`.
- Use relative placeholders such as `data=custom.yaml` in public examples; avoid machine-specific dataset roots.

## Bundled References

- `references/workflows.md`: dataset YAML templates, config-key groups, Python-to-CLI translation rules, converters, and planning examples.
- `references/troubleshooting.md`: common data/config failures and safe diagnosis steps.
- `scripts/validate_dataset_yaml.py`: offline dataset YAML linter with actionable diagnostics.
- `scripts/plan_yolo_command.py`: offline command planner that validates task, mode, CLI syntax, unknown/deprecated keys, and cost-risk flags.
