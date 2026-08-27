# Installation and CLI reference

## Purpose

Read this when choosing an AnyLabeling install variant, checking whether an installed package is usable, or mapping CLI/config flags to runtime behavior before routing to a focused sub-skill.

## Package identity

- Distribution: `anylabeling` for the default CPU package.
- Published GPU distribution: `anylabeling-gpu` for Linux/Windows GPU-oriented releases.
- Import root: `anylabeling` for both variants.
- Console entry point: `anylabeling`, implemented by `anylabeling.app:main`.
- Supported Python: 3.11 or newer.

## Install variants

```bash
pip install anylabeling
pip install anylabeling-gpu          # Linux/Windows GPU package
pip install -e .                     # development CPU install inside a checkout
pip install -e ".[gpu]"              # development GPU dependency variant
pip install -e ".[macos]"            # CoreML support after installing PyQt on macOS
pip install -e ".[dev]"              # build/resource/publish developer tools
```

Use the smallest variant that matches the task. The default package already includes ONNX, ONNX Runtime, OpenCV headless, PyQt6 on non-Darwin systems, NumPy, Pillow, PyYAML, imgviz, qimage2ndarray, Hugging Face Hub, and the SAM3 tokenizer dependency.

On macOS, package metadata intentionally excludes PyQt6; install PyQt through Conda or another macOS-compatible path before importing the desktop app. Add `[macos]` only for CoreML-related SAM2.1 workflows.

## Safe checks

Minimal package metadata/import check:

```bash
python -c "import anylabeling; print(anylabeling.__version__)"
```

CLI parser check:

```bash
anylabeling --help
```

Headless startup import check:

```bash
QT_QPA_PLATFORM=offscreen python -c "from anylabeling.views.labeling import label_widget; from anylabeling import app; print('startup imports OK')"
```

Skill-bundled environment check:

```bash
python scripts/check_anylabeling_env.py --startup-import
```

The bundled check script is read-only. It imports package metadata, checks CLI help when requested, lists built-in model catalog counts, and can inspect whether local model-cache folders exist without downloading weights.

## CLI flags

The desktop entry point accepts a positional `filename` plus these notable options:

| Flag | Meaning |
| --- | --- |
| `--reset-config` | Clear saved Qt window/config state and exit. |
| `--logger-level {debug,info,warning,error,fatal}` | Set application logger verbosity. |
| `--config <path-or-yaml>` | Load user config from a file or YAML string. Default user config is `.anylabelingrc` in the user's home directory. |
| `--output`, `-O`, `-o` | Output file if the value ends with `.json`; otherwise output directory. |
| `--nodata` | Do not embed image bytes in saved label JSON. |
| `--autosave` | Save automatically when moving through files. |
| `--nosortlabels` | Preserve label order instead of sorting. |
| `--flags` | Comma-separated flags or a file containing one flag per line. |
| `--labelflags` | YAML or file defining label-specific flag patterns. |
| `--labels` | Comma-separated labels or a file containing labels. |
| `--validatelabel exact` | Restrict labels to the configured label list. |
| `--keep-prev` | Keep previous annotation when moving through images. |
| `--epsilon <float>` | Canvas vertex/edge proximity threshold. |
| `--theme {system,light,dark}` | Override or use system theme. |

## Config behavior

AnyLabeling loads defaults from the packaged config, overlays a user-provided file/YAML when supplied, then overlays CLI arguments. Unknown config keys are skipped with a warning except for recognized `theme` and `ui` additions. Validation covers label duplicates, `validate_label`, `shape_color`, and theme values.

If a task involves detailed label schema, shape behavior, or export, route to `annotation-ui-and-data`. If a task involves `custom_models` or auto-label model selection, route to `auto-labeling-models`.

## Model cache and external assets

Built-in auto-labeling models are cataloged by name and download URL. After first download, weights/configs live in the user's AnyLabeling model cache under a `models/<model-name>/` structure. The helper scripts in this skill can inspect already-present cache folders but do not download or remove model files.

Real ONNX inference checks require external model files. Absence of those files should produce a clean skip or a clear "not downloaded" diagnostic, not a package-install failure.
