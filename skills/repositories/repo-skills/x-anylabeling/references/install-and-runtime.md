# Install and Runtime Reference

Use this reference when a task needs to install X-AnyLabeling, choose a backend
extra, launch the CLI/GUI, set a config/work directory, or run a safe runtime
check before using a deeper sub-skill.

## Package identity

- Distribution: `x-anylabeling-cvhub`.
- Import name: `anylabeling`.
- CLI: `xanylabeling`.
- Baseline version for this skill: `4.0.2`.
- Supported Python: `>=3.11`; Python `3.12` is the documented recommended
  environment for ordinary use.

## Install variants

Install exactly one backend extra in a single environment:

| Use case | Command |
|---|---|
| CPU annotation, conversion, and ONNX Runtime CPU inference | `python -m pip install "x-anylabeling-cvhub[cpu]"` |
| CUDA 12.x ONNX Runtime GPU | `python -m pip install "x-anylabeling-cvhub[gpu]"` |
| CUDA 11.x ONNX Runtime GPU | `python -m pip install "x-anylabeling-cvhub[gpu-cu11]"` |
| CUDA 13.x ONNX Runtime GPU | `python -m pip install "x-anylabeling-cvhub[gpu-cu13]"` |
| Editable source work | `python -m pip install -e ".[cpu]"` or exactly one GPU extra |

Do not install `onnxruntime` and `onnxruntime-gpu` together. If a GPU install
falls back to CPU or imports the wrong provider, create a clean environment and
install only the matching extra.

Developer tools such as `pytest`, `pyinstaller`, formatting tools, and PySide6
are in the `dev` extra. Do not install `dev` for normal annotation/conversion
unless the task is repository development.

## Minimal checks

```bash
xanylabeling version
xanylabeling --help
xanylabeling convert
python -c "import anylabeling, anylabeling.app_info as info; print(info.__version__)"
```

For a structured check with optional JSON output:

```bash
python scripts/check_xanylabeling_env.py --json
python scripts/check_xanylabeling_env.py --show-model-registry --json
```

The checker imports the package, verifies `xanylabeling`, reports ONNX Runtime
providers when available, and can inspect the model registry without loading or
downloading model weights.

## CLI command groups

`xanylabeling` launches the GUI when no utility subcommand is supplied. Utility
subcommands:

| Command | Purpose |
|---|---|
| `xanylabeling help` or `xanylabeling --help` | Show CLI help. |
| `xanylabeling checks` | Print system/package information. |
| `xanylabeling version` | Print application version. |
| `xanylabeling config` | Print active `.xanylabelingrc` path. |
| `xanylabeling convert` | List or run conversion tasks. Route details to `sub-skills/conversion-cli/SKILL.md`. |
| `xanylabeling train-worker` | Hidden worker entry for the GUI training integration. Route details to `sub-skills/developer-workflows/SKILL.md`. |

## GUI launch options

Important top-level launch flags:

| Option | Use |
|---|---|
| positional `filename` | Image file, label file, or image directory to open. |
| `--output`, `-O`, `-o` | Label output file or directory. Values ending in `.json` are treated as a single file; directories are preferred for autosave. |
| `--config` | Path to YAML config or inline YAML mapping. |
| `--work-dir` | Directory for `.xanylabelingrc` and X-AnyLabeling data/cache folders. |
| `--reset-config` | Clear persisted Qt UI settings. |
| `--logger-level` | `debug`, `info`, `warning`, `fatal`, or `error`. |
| `--no-auto-update-check` | Disable startup update check. |
| `--qt-platform` | Force a Qt platform plugin such as `xcb` or `wayland`. |
| `--qt-image-allocation-limit` | Override Qt image allocation limit in MB; `0` disables it. |
| `--nodata` | Keep top-level `imageData` null to avoid base64 bloat. |
| `--autosave` | Enable automatic saving. |
| `--labels` and `--validatelabel exact` | Enforce a fixed label list. Exact validation requires labels. |

For annotation details, load `sub-skills/annotation-ui/SKILL.md`.

## Model data and work directory

The configured work directory affects:

- `.xanylabelingrc` location.
- Model/data cache directories used by model loading.
- Training integration cache/output roots.
- Chatbot/VQA/provider configuration files.

Use `--work-dir` for project-specific or disposable runs to avoid mixing GUI
preferences and model caches between projects.

## Backend and hardware notes

- CPU conversion and model-free annotation do not require CUDA.
- GPU ONNX Runtime extras require a compatible NVIDIA driver, CUDA generation,
  cuDNN runtime, and matching `onnxruntime-gpu` package.
- TensorRT is not part of the default extras. TensorRT engine configs need
  `tensorrt`, `cuda-python`, matching GPU architecture, and a compatible
  `.engine` file.
- Remote/API-backed models need reachable services and tokens; do not test them
  with dummy credentials.
- GUI operation needs a functioning Qt display stack. Headless environments can
  run CLI/conversion checks, but launching the full GUI may require X11/Wayland
  or a platform plugin such as `xcb`.

## Choosing the next reference

- Install/import/Qt/backend symptoms: `references/troubleshooting.md`.
- GUI operation and XLABEL schema: `sub-skills/annotation-ui/SKILL.md`.
- Conversion commands/API: `sub-skills/conversion-cli/SKILL.md`.
- Built-in/custom model configs and downloads: `sub-skills/auto-labeling-models/SKILL.md`.
- Training/build/localization/developer checks: `sub-skills/developer-workflows/SKILL.md`.
