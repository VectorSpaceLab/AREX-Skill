---
name: interactive-deep-colorization
description: "Routes agents using Interactive Deep Colorization for local-hints
  image colorization, model setup, GUI/API workflows, and Caffe global histogram
  transfer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# interactive-deep-colorization

Use this repo skill when a task names Interactive Deep Colorization, iDeepColor, the SIGGRAPH 2017 real-time user-guided colorization code, local color hints, ab-mask guided image colorization, the PyQt colorization GUI, converted PyTorch weights, Caffe model artifacts, or global histogram transfer with a reference image.

## Start here

1. Identify whether the user is asking about setup, local-hints colorization, or global histogram transfer.
2. Read the matching sub-skill before giving commands or API guidance.
3. Check [references/troubleshooting.md](references/troubleshooting.md) when the request includes import failures, missing weights, display/Qt errors, Caffe/PyTorch confusion, or stale-checkout questions.
4. Check [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a different checkout or should be refreshed.

## Route map

| User intent | Read |
| --- | --- |
| Install dependencies, choose Caffe/PyTorch/Docker, stage model weights, validate expected artifacts, or diagnose setup blocks | [sub-skills/setup-and-models/SKILL.md](sub-skills/setup-and-models/SKILL.md) |
| Run or explain the local-hints GUI, reproduce the barebones notebook flow, build `input_ab`/`input_mask`, inspect CLI defaults, use color suggestions, or interpret saved output artifacts | [sub-skills/interactive-colorization/SKILL.md](sub-skills/interactive-colorization/SKILL.md) |
| Use a reference image's global color histogram, explain `ColorizeImageCaffeGlobDist`, validate global model assets, or troubleshoot global histogram notebook behavior | [sub-skills/global-histogram-transfer/SKILL.md](sub-skills/global-histogram-transfer/SKILL.md) |

## Quick setup

If you need a fresh inspection environment for the local-hints or setup workflows, create one with the scientific image stack and PyTorch first, then validate the selected workflow with the bundled helpers:

```bash
python3.11 -m venv /path/to/inspection-env
/path/to/inspection-env/bin/python -m pip install numpy scipy scikit-image scikit-learn matplotlib opencv-python-headless torch
/path/to/inspection-env/bin/python sub-skills/interactive-colorization/scripts/smoke_core_helpers.py --repo-root /path/to/checkout --size 8
```

If the task is about missing weights or backend choice, check the bundled artifact and CLI inspectors before attempting a GUI or notebook launch:

```bash
/path/to/inspection-env/bin/python sub-skills/setup-and-models/scripts/check_model_artifacts.py --repo-root /path/to/checkout --workflow all
/path/to/inspection-env/bin/python sub-skills/interactive-colorization/scripts/inspect_cli_defaults.py --variant both --json
```

## Repository shape and install expectations

Interactive Deep Colorization is a research-demo checkout rather than a packaged Python distribution. There is no `setup.py`, `pyproject.toml`, or console entry point. Future agents should treat the repository root as the import root when working with a live checkout, and should prepare dependencies according to the selected workflow rather than installing every historical script.

Minimum conceptual setup:

- Scientific image stack: NumPy, SciPy, scikit-image, scikit-learn, OpenCV, and Matplotlib/notebook tools when using notebook recipes.
- Caffe path: PyCaffe with Python layer support plus Caffe model weights.
- PyTorch path: PyTorch plus `models/pytorch/caffemodel.pth` or another compatible checkpoint.
- GUI path: PyQt4/qdarkstyle for the root script, or PyQt5 through the Docker variant.
- Global histogram transfer: Caffe-only global weights and stats model assets.

## Important limitations

- Training code is not part of this checkout; the README points training to a separate PyTorch reimplementation repository.
- The original Caffe backend and global histogram notebook require PyCaffe and downloaded weights; this generated skill documents them but did not verify native Caffe execution during construction.
- The GUI requires Qt bindings and a display server; use safe bundled inspectors when only parser/API facts are needed.
- Model fetch scripts perform network downloads and are represented here by safe artifact-check helpers rather than automatic download wrappers.

## Safe checks bundled in sub-skills

Use these checks when working with a live checkout or staged artifact tree; replace `/path/to/checkout` with the user's current repository root.

- Model artifact presence: [sub-skills/setup-and-models/scripts/check_model_artifacts.py](sub-skills/setup-and-models/scripts/check_model_artifacts.py)

  ```bash
  python sub-skills/setup-and-models/scripts/check_model_artifacts.py --repo-root /path/to/checkout --workflow all
  ```

- Local-hints CLI defaults without PyQt/Caffe imports: [sub-skills/interactive-colorization/scripts/inspect_cli_defaults.py](sub-skills/interactive-colorization/scripts/inspect_cli_defaults.py)

  ```bash
  python sub-skills/interactive-colorization/scripts/inspect_cli_defaults.py --variant both --json
  ```

- Core source helper smoke without weights/GUI/Caffe: [sub-skills/interactive-colorization/scripts/smoke_core_helpers.py](sub-skills/interactive-colorization/scripts/smoke_core_helpers.py)

  ```bash
  python sub-skills/interactive-colorization/scripts/smoke_core_helpers.py --repo-root /path/to/checkout --size 8
  ```

- Global histogram asset presence without Caffe imports: [sub-skills/global-histogram-transfer/scripts/check_global_histogram_assets.py](sub-skills/global-histogram-transfer/scripts/check_global_histogram_assets.py)

  ```bash
  python sub-skills/global-histogram-transfer/scripts/check_global_histogram_assets.py --repo-root /path/to/checkout
  ```

## Evidence and routing metadata

- Read [references/repo-provenance.md](references/repo-provenance.md) for source commit, dirty-state summary, package/import facts, and evidence paths.
- `references/repo-routing-metadata.json` contains structured scenario metadata for managed repo-skill import tools; it is data, not user-facing guidance.
