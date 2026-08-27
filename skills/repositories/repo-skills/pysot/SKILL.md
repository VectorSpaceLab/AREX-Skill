---
name: pysot
description: "Operate PySOT visual object tracking workflows: configs,
  model/tracker APIs, demo/test inference, training data preparation, and
  toolkit evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySOT repo skill

Use this skill when the task is about PySOT, SiamRPN/SiamRPN++/DaSiamRPN/SiamMask visual object tracking, PySOT experiment YAMLs, PySOT tracker snapshots, training data preparation, or the PySOT evaluation toolkit.

This skill is an operating router. It gives safe preflights and routes to focused sub-skills; it does not claim that full tracking, training, or evaluation can run without the user's snapshots, datasets, video/display setup, and compatible PyTorch/CUDA environment.

## First checks

1. Identify the user's task family: config/model, tracking inference, training/data, or evaluation/results.
2. Confirm whether the task is a safe preflight or a full native workflow. Safe preflights may run without model/data assets; full workflows usually need external files and sometimes CUDA.
3. If the environment itself is uncertain, read [references/environment-and-install.md](references/environment-and-install.md) and run:

   ```bash
   python scripts/check_env.py --repo-root <pysot-checkout>
   ```

   Add a config/model construction smoke only when the user has a config:

   ```bash
   python scripts/check_env.py --repo-root <pysot-checkout> --config <config.yaml> --model-smoke
   ```

4. If the current repository version may differ from this skill, read [references/repo-provenance.md](references/repo-provenance.md) before acting.

## Route map

### Configs, models, trackers, and model zoo

Read [sub-skills/configuration-models/SKILL.md](sub-skills/configuration-models/SKILL.md) when the user asks to:

- edit or validate an experiment YAML;
- choose a SiamRPN/SiamMask/long-term/AlexNet/ResNet/MobileNetV2 config;
- understand `cfg`, `META_ARC`, `BACKBONE`, `RPN`, `MASK`, `REFINE`, `TRACK`, or `ANCHOR` keys;
- instantiate `ModelBuilder()` or `build_tracker(model)` safely;
- diagnose config merge, unsupported component type, anchor-count, output-size, or snapshot/config mismatch errors.

### Tracking inference, demo, and benchmark test commands

Read [sub-skills/tracking-inference/SKILL.md](sub-skills/tracking-inference/SKILL.md) when the user asks to:

- run a webcam/video/image-folder demo;
- validate config/snapshot/video/dataset inputs before tracking;
- use `tracker.init(img, bbox)` and `tracker.track(img)` programmatically;
- construct a `tools/test.py` benchmark run and understand result output paths;
- debug OpenCV GUI/video, missing snapshot, CUDA, bbox/mask output, or tracker API failures.

### Training data and distributed training setup

Read [sub-skills/training-data/SKILL.md](sub-skills/training-data/SKILL.md) when the user asks to:

- prepare VID, YouTube-BB, DET, or COCO training data;
- understand crop image names, `train.json`, `SubDataset`, or `TrkDataset` expectations;
- validate training config/data paths;
- construct distributed `tools/train.py` commands, pretrained backbone paths, resume settings, logs, or snapshots;
- debug `size not match!`, missing annotations/images, distributed launch, or training CUDA issues.

### Evaluation toolkit, result layouts, metrics, and hp-search

Read [sub-skills/evaluation-toolkit/SKILL.md](sub-skills/evaluation-toolkit/SKILL.md) when the user asks to:

- validate tracker result trees before `eval.py`;
- evaluate OTB, UAV, NFS, LaSOT, VOT short-term, or VOT2018-LT results;
- choose OPE, accuracy/robustness, EAO, or F1 metric flows;
- diagnose `tracker_prefix`, missing tracker directories, JSON sidecars, region extension, multiprocessing, or result-file naming;
- plan or interpret `hp_search.py` outputs.

## Cross-cutting guidance

- PySOT's `setup.py` declares the `toolkit` distribution and Cython region extension. The main `pysot` package is normally imported from a checkout/PYTHONPATH or equivalent editable-development context.
- If `toolkit.utils.region` fails to import, build the extension with a compatible Cython version; [references/troubleshooting.md](references/troubleshooting.md) gives the recovery path.
- Do not run full training, benchmark testing, hyperparameter search, dataset crop generation, or metric evaluation as default smoke tests. Use the bundled validators first.
- Keep config/model edits and command construction tied to explicit user-provided paths. Do not silently download model snapshots or benchmark/training datasets.
- Treat CUDA as required for unmodified source training/test/hp-search paths that call `.cuda()` directly. CPU-safe model construction does not prove those paths are runnable.

## Root references and helper

- [references/environment-and-install.md](references/environment-and-install.md) — install/import model, dependencies, legacy PyTorch/CUDA expectations, and safe versus full workflow boundaries.
- [references/troubleshooting.md](references/troubleshooting.md) — cross-cutting import, extension, dependency, backend, and asset failures.
- [references/repo-provenance.md](references/repo-provenance.md) — source commit, package metadata, evidence paths, and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) — structured router metadata for managed repo-skill import.
- [scripts/check_env.py](scripts/check_env.py) — safe environment/config/model preflight helper.
