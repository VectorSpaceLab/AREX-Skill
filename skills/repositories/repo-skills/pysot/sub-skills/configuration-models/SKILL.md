---
name: configuration-models
description: "Inspect, edit, validate, and reason about PySOT YACS configs,
  model builders, tracker mappings, model-zoo naming, and safe model
  construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySOT configuration and model guidance

Use this sub-skill when the task is about PySOT experiment YAMLs, `cfg` keys, `META_ARC`, model-family selection, backbone/RPN/head/neck/tracker mappings, model-zoo names, or safe construction of `ModelBuilder`/`build_tracker` without running a benchmark or training job.

## Read this sub-skill when

- A user asks to edit, compare, or validate a PySOT config file.
- A user asks which SiamRPN, SiamMask, long-term, AlexNet, ResNet, or MobileNetV2 variant fits a task.
- A user asks what `META_ARC`, `TRACK.TYPE`, `ANCHOR.*`, `RPN.KWARGS.anchor_num`, `TRAIN.OUTPUT_SIZE`, or `BACKBONE.KWARGS.used_layers` means.
- A user gets `KeyError`, missing-key, anchor-count, `size not match!`, `ModelBuilder`, or `build_tracker` failures while loading a config or building the model graph.
- A user wants a safe preflight before using a snapshot, running a demo/test, or starting training.

## Route elsewhere

- Demo, video/webcam/image-folder tracking, snapshot loading, and benchmark test execution: read sibling `tracking-inference`.
- Training datasets, crop/annotation formats, distributed launch, pretrained training backbones, and training data validation: read sibling `training-data`.
- Benchmark dataset/result directory layouts, OPE/EAO/AR/F1 metrics, `eval.py`, and hyperparameter-search result interpretation: read sibling `evaluation-toolkit`.
- Cross-cutting install/import/backend guidance belongs in the root PySOT troubleshooting reference; keep config/model-specific diagnosis here.

## Operating workflow

1. Identify the user-supplied PySOT config path and the intended workflow: model choice, config edit, construction smoke, tracking run, training, or evaluation.
2. Read [references/configuration.md](references/configuration.md) for required YAML sections, common model families, safe edit rules, and anchor/output-size formulas.
3. Read [references/model-api.md](references/model-api.md) before writing code that imports `cfg`, `ModelBuilder`, or `build_tracker`.
4. Read [references/model-zoo.md](references/model-zoo.md) when selecting among model-zoo names or interpreting suffixes such as `_otb`, `_lt`, `_8gpu`, and `_16gpu`.
5. Run the bundled validator before any heavy workflow:

   ```bash
   python scripts/validate_config.py --config path/to/config.yaml
   ```

   If the task specifically asks whether the model graph and tracker can be constructed, add:

   ```bash
   python scripts/validate_config.py --config path/to/config.yaml --instantiate-model
   ```

   This is a CPU-safe construction smoke: it does not load a snapshot, open video, run inference, launch training, download assets, or evaluate benchmarks.
6. If validation fails, use [references/troubleshooting.md](references/troubleshooting.md). Fix config keys and rerun validation before routing to execution-oriented sub-skills.

## Key safety rules

- Pair a downloaded snapshot with the config family it was trained for; do not assume a checkpoint can be loaded under a different backbone, RPN, mask, or tracker setting.
- Treat full benchmark/test/training runs as user-asset and often CUDA-dependent workflows. This sub-skill only validates config/model construction.
- PySOT's package metadata installs the `toolkit` distribution; importing `pysot` normally depends on using the source checkout through PYTHONPATH or an editable-development setup.
- Do not ask future users to reopen original repository docs or scripts for the information covered here; use the bundled references and helper script.

## References and bundled helper

- [references/configuration.md](references/configuration.md) — config sections, model-family keys, edit workflow, anchor and output-size checks.
- [references/model-api.md](references/model-api.md) — verified `cfg`, `ModelBuilder`, component maps, tracker dispatch, and safe construction pattern.
- [references/model-zoo.md](references/model-zoo.md) — model-zoo name grammar, suffixes, benchmark columns, and selection guidance.
- [references/troubleshooting.md](references/troubleshooting.md) — config/model failure modes and expected validator signals.
- [scripts/validate_config.py](scripts/validate_config.py) — safe argparse validator for PySOT YAML configs and optional construction smoke.
