# Cross-cutting troubleshooting

## Start with a route decision

1. If the failure happens before or during package import, CLI parsing, Qt startup, or dependency installation, stay in this root reference and then route to `packaging-release` if it is a maintainer/package task.
2. If the failure happens while opening/saving labels, validating JSON, drawing shapes, navigating files, or exporting annotations, route to `annotation-ui-and-data`.
3. If the failure happens while selecting/downloading/loading/running an auto-labeling model, route to `auto-labeling-models`.

## Package import fails

Symptoms:
- `ModuleNotFoundError: anylabeling`.
- Missing PyQt6, OpenCV, ONNX Runtime, qimage2ndarray, or imgviz import errors.
- Import succeeds from a checkout but not from a clean environment.

Recovery:
1. Verify the intended environment is active or use the environment's explicit Python.
2. Install the smallest appropriate variant: CPU/default first unless GPU/CoreML is required.
3. Run:
   ```bash
   python -c "import anylabeling; print(anylabeling.__version__)"
   anylabeling --help
   ```
4. On macOS, install PyQt through the documented platform path before blaming AnyLabeling metadata.
5. If this is a release-maintenance task, run the fresh environment checklist in `sub-skills/packaging-release`.

## Startup import fails but plain package import works

Symptoms:
- `import anylabeling` works, but importing UI modules or launching the app fails.
- Qt platform plugin errors in headless Linux.
- NumPy assignment/read-only array failure around label colormap.

Recovery:
1. Use `QT_QPA_PLATFORM=offscreen` for headless checks.
2. Run the startup smoke from [installation-and-cli.md](installation-and-cli.md).
3. If the error mentions colormap mutability, check that the UI code uses a writable copy of `imgviz.label_colormap()` and run the focused colormap regression test in a maintainer checkout.
4. If generated resources were recently changed, verify `resources.py` imports PyQt6, not PySide6.

## Config or CLI behavior is surprising

Symptoms:
- A config key appears ignored.
- Labels are rejected or sorted unexpectedly.
- Output goes to a directory rather than a single JSON file.

Recovery:
- Remember the overlay order: packaged defaults, then `--config` file/YAML, then CLI flags.
- Unknown keys are skipped except recognized additions such as `theme` and `ui`.
- `--output` values ending in `.json` are treated as a single output file; other values are output directories.
- `--validatelabel exact` requires a label list; duplicate configured labels are invalid.
- For label-file/export details, route to `annotation-ui-and-data`.

## Auto-labeling model does not appear or load

Symptoms:
- Model dropdown lacks an expected type.
- `Unknown model type`.
- Missing encoder/decoder/model path.
- Download failure from GitHub or Hugging Face.

Recovery:
1. Route to `auto-labeling-models`.
2. Inspect the model catalog and custom config with bundled scripts before downloading weights.
3. Verify registry import side effects: concrete model modules must be imported so their decorators run.
4. Distinguish built-in catalog pre-download entries from load-ready custom configs; built-ins may rely on downloaded `config.yaml` files to add paths.

## GPU or CoreML expectations are unclear

Symptoms:
- User installed the CPU package but expected GPU acceleration.
- GPU package installed but wheel metadata looks like the CPU package.
- CoreML path fails on non-macOS.

Recovery:
- CPU/default AnyLabeling is the baseline. Do not claim GPU/CoreML verification unless that variant and hardware were explicitly tested.
- GPU publishing requires the `anylabeling-gpu` package metadata and `onnxruntime-gpu` dependency, not merely a runtime flag.
- CoreML support is macOS-specific and uses the `[macos]` extra plus platform PyQt.
- For release/package variant debugging, route to `packaging-release`.

## Real model inference tests skip

Skips in real-inference checks usually mean the user's model cache lacks the required external weights. That is acceptable for package install verification. It is not acceptable evidence for changes to ONNX preprocessing, model loading, SAM3 text prompts, or real inference behavior; download the relevant model assets and rerun the targeted real-inference tests for those tasks.

## Use the bundled root checker

From this skill directory, run:

```bash
python scripts/check_anylabeling_env.py --help
python scripts/check_anylabeling_env.py --startup-import --cli-help --model-cache
```

The checker is safe by default and does not download models, mutate config, or launch the GUI event loop.
