# Packaging and release reference

## Purpose

Read this when a task involves AnyLabeling development installs, package variants, wheel/sdist builds, standalone executables, resource regeneration, or release packaging. Commands here are checkout-relative because maintainer packaging inherently operates inside a repository checkout; do not use them for ordinary package usage unless the user is working on the repository.

## Install variants

AnyLabeling is a Python package with a PyQt6 desktop entry point and an ONNX-based auto-labeling backend.

| Variant | Public install shape | Main effect | Notes |
| --- | --- | --- | --- |
| CPU/default | `pip install anylabeling` or `pip install -e .` | Installs base dependencies and `onnxruntime`. | PyQt6 is excluded by package metadata on Darwin, so macOS users install PyQt through Conda or an equivalent channel first. |
| GPU | `pip install anylabeling-gpu` for published wheels, or `pip install -e ".[gpu]"` in a checkout | Adds/replaces with `onnxruntime-gpu`; release workflow also rewrites package metadata to publish under `anylabeling-gpu`. | The app also uses `__preferred_device__ = "GPU"` to set OpenCV DNN CUDA backend for YOLO classes. |
| macOS CoreML | `pip install -e ".[macos]"` after a macOS PyQt install | Adds `coremltools==8.3.0` for the SAM2.1 CoreML branch. | Linux/Windows environments should not install this extra for routine inspection. |
| Developer tooling | `pip install -e ".[dev]"` | Adds `build`, `twine`, and `PySide6-Essentials` tools used for resources/translations. | Install only for maintainer tasks; base package use does not need these tools. |

Supported Python is 3.11 or newer. The project CI currently exercises Python 3.11, 3.12, and 3.13 on Linux, Windows, and macOS. Use Python 3.12 as a conservative local release-prep choice unless the task specifically targets another supported version.

## CLI and startup smoke

The console script is `anylabeling`, which calls `anylabeling.app:main`. A safe parser check is:

```bash
anylabeling --help
```

For headless import checks, set the Qt platform before importing UI modules:

```bash
QT_QPA_PLATFORM=offscreen python -c "from anylabeling.views.labeling import label_widget; from anylabeling import app; print('startup imports OK')"
```

This path is important because import-time UI dependencies and the label colormap regression surface here before the desktop window is shown.

## CPU and GPU package build behavior

Static metadata is in `pyproject.toml`. The CPU release builds a wheel and sdist for the package named `anylabeling`.

The GPU release is not just `__preferred_device__ = "GPU"`. The current GPU publish workflow rewrites `pyproject.toml` before building so that:

- `name = "anylabeling"` becomes `name = "anylabeling-gpu"`.
- `"onnxruntime>=1.20.0"` becomes `"onnxruntime-gpu>=1.20.0"`.

After a GPU build, inspect wheel metadata rather than assuming a setup shim changed it:

```bash
python -m zipfile -e dist/anylabeling_gpu-*.whl /tmp/anylabeling-wheel-check
python - <<'PY'
from pathlib import Path
meta = next(Path('/tmp/anylabeling-wheel-check').glob('anylabeling_gpu-*.dist-info/METADATA'))
for line in meta.read_text().splitlines():
    if line.startswith(('Name:', 'Requires-Dist: onnxruntime')):
        print(line)
PY
```

Expected GPU metadata includes `Name: anylabeling-gpu` and a dependency on `onnxruntime-gpu`.

## Wheel and sdist builds

Install `build` in the environment used for packaging. Then run:

```bash
python -m build --sdist --wheel --outdir dist/ .
```

For GPU packaging in a checkout, apply the metadata rewrite in a disposable branch or ensure changes are restored before committing unrelated work. Do not run publishing/upload commands unless the user explicitly authorized release credentials and target.

## PyInstaller executable builds

The default executable build delegates to the project spec:

```bash
pyinstaller --noconfirm anylabeling.spec
```

The spec includes package data for configs and the auto-labeling `.ui` file. It also includes a Windows runtime hook that preloads `onnxruntime` DLLs from the bundled `onnxruntime/capi` directory, because PyInstaller may place native DLLs somewhere the Windows loader does not search automatically.

When debugging Windows executable crashes around `onnxruntime_pybind11_state.pyd`, check that both `onnxruntime_providers_shared.dll` and `onnxruntime.dll` were collected and preloaded before the Python import.

## macOS folder-mode build

The macOS folder-mode build creates a directory-style application rather than a single `.app` bundle. It accepts an optional `GPU` argument, mutates the preferred-device flag for the build, creates a temporary PyInstaller spec, installs PyInstaller if missing, and writes output under `dist/AnyLabeling-Folder` or `dist/AnyLabeling-Folder-GPU`.

Run this only on macOS or when explicitly inspecting the script behavior:

```bash
bash scripts/build_macos_folder.sh
bash scripts/build_macos_folder.sh GPU
```

Because the script mutates package files during the build, verify the working tree afterward and restore `__preferred_device__ = "CPU"` unless a GPU release is intentionally being prepared.

## Translation and Qt resource regeneration

Resource and language maintenance uses PyQt6 tools for UI/translation extraction and PySide6-Essentials for Qt6 resource compilation and `.qm` generation. The generated `resources.py` must import PyQt6, so the scripts rewrite generated PySide6 imports to PyQt6.

Before mutating resources, run the bundled checker:

```bash
python scripts/check_language_tools.py
```

Then, inside an intentionally prepared maintainer environment:

```bash
python scripts/compile_languages.py      # compile existing .ts and rebuild resources.py
python scripts/generate_languages.py     # regenerate .ts from source, compile, rebuild resources.py
```

After regeneration, inspect the generated resource module for PyQt6 imports and run the startup import smoke.

## Model zipping and upload scripts

Treat model-zipping and PyPI upload scripts as maintainer-only and potentially stale or destructive. In particular, the historical model zipping helper assumes model fields that do not match the current catalog shape and performs network downloads. Prefer the current model catalog and publish workflows as evidence, and do not use upload commands unless the user explicitly asks to publish.
