---
name: anylabeling
description: "Operate AnyLabeling desktop annotation, auto-labeling model,
  dataset export, install, packaging, and release workflows for the PyQt6/ONNX
  image-labeling package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# AnyLabeling repo skill

Use this repo skill when a task involves AnyLabeling, the `anylabeling` or `anylabeling-gpu` Python packages, the desktop image-annotation app, AnyLabeling label JSON, auto-labeling with YOLO/SAM-family ONNX or CoreML models, or package build/release maintenance.

## Start here

- Install/use the app from PyPI with `pip install anylabeling` for the CPU package. Use `anylabeling-gpu` only when the task explicitly targets the published GPU variant on Linux/Windows.
- Development installs use `pip install -e .`; add only the focused extra needed by the task, such as `.[gpu]`, `.[macos]`, or `.[dev]`.
- Run the desktop app with `anylabeling` or `python -m anylabeling.app` when working from an installed package. For headless import checks, set `QT_QPA_PLATFORM=offscreen`.
- Minimal import smoke:
  ```bash
  python -c "import anylabeling; print(anylabeling.__version__)"
  ```
- Startup smoke for UI dependencies:
  ```bash
  QT_QPA_PLATFORM=offscreen python -c "from anylabeling.views.labeling import label_widget; from anylabeling import app; print('startup imports OK')"
  ```

## Route by task

| Task signal | Read |
| --- | --- |
| Manual annotation, opening images/folders, label JSON, flags/labels validation, canvas shape editing, output path behavior, or YOLO/VOC/COCO/CreateML export | [sub-skills/annotation-ui-and-data/SKILL.md](sub-skills/annotation-ui-and-data/SKILL.md) |
| Built-in model catalog, custom model YAML, model downloads/cache, `ModelRegistry`, `ModelManager`, YOLOv5/v8, Segment Anything, MobileSAM, SAM2, SAM3 text prompts, CoreML, or real-inference diagnostics | [sub-skills/auto-labeling-models/SKILL.md](sub-skills/auto-labeling-models/SKILL.md) |
| Fresh install gates, Python version support, CPU/GPU/macOS package variants, PyPI wheels, PyInstaller executables, translations/resources, CI, or release preparation | [sub-skills/packaging-release/SKILL.md](sub-skills/packaging-release/SKILL.md) |

## Shared references and helpers

- [references/installation-and-cli.md](references/installation-and-cli.md) summarizes install variants, CLI flags, config file behavior, and safe smoke checks.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install/import, Qt, dependency, config, and backend triage before routing to a focused sub-skill.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot used to build this skill; read it before deciding whether to refresh the skill for a newer checkout.
- [scripts/check_anylabeling_env.py](scripts/check_anylabeling_env.py) performs a safe installed-package, CLI, catalog, optional Qt startup, and optional backend/model-cache inspection.

## Decision rules

- Prefer package-level checks before GUI actions: import, CLI help, config load, then startup smoke.
- Do not install broad extras by default. GPU, CoreML, developer tooling, and real-model downloads are optional unless the user explicitly asks for those workflows.
- Treat external model weights as user cache artifacts. Built-in auto-labeling models can download on first use, but diagnostic scripts in this skill avoid downloads unless a task explicitly requests them.
- For repository maintenance tasks, run focused native tests after reading the matching sub-skill; for ordinary package use, rely on smoke checks and bundled helpers.
- If a task asks for generic computer vision modeling, model training, or non-AnyLabeling annotation tools without AnyLabeling/API/config signals, use a more specific vision or annotation-platform skill instead.
