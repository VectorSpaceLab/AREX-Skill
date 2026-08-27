# TIAToolbox CLI Troubleshooting

Use this reference for console startup, install validation, CLI argument parsing, configuration quoting, and cross-cutting runtime failures. Route workflow-specific diagnosis to the owning sub-skill after the CLI layer is understood.

## `tiatoolbox: command not found`

Likely causes:

- The package is installed in a different Python environment from the active shell.
- The environment's script directory is not on `PATH`.
- The install failed before creating the console entry point.

Safe checks:

```bash
python - <<'PY'
import shutil
import tiatoolbox
print("import ok", tiatoolbox.__version__)
print("console", shutil.which("tiatoolbox"))
PY
python -m pip show tiatoolbox
python - <<'PY'
from tiatoolbox.cli import main
main(args=["--help"])
PY
```

If `import tiatoolbox` works but `shutil.which("tiatoolbox")` is `None`, tell the user to run the command from the same activated environment or use the full script path reported by their package manager. Avoid hard-coding environment paths in reusable instructions.

## Import Errors After Install

First separate package import from optional workflow dependencies:

```bash
python - <<'PY'
import tiatoolbox
print(tiatoolbox.__version__)
PY
```

Common causes include unsupported Python versions, partial dependency installs, incompatible PyTorch builds, or missing native libraries for image/WSI formats. TIAToolbox package metadata targets Python 3.11 through 3.14. If the package import itself fails, fix the environment before debugging CLI arguments.

## Missing Native Libraries or Codecs

Symptoms include failures importing or using OpenSlide, JPEG2000/OpenJPEG, SQLite-backed annotation stores, DICOM/WSI readers, or image codecs.

Safe probes:

```bash
python - <<'PY'
for name in ["openslide", "glymur", "imagecodecs", "sqlite3", "torch"]:
    try:
        module = __import__(name)
        print(name, "ok", getattr(module, "__version__", ""))
    except Exception as exc:
        print(name, "failed", type(exc).__name__, exc)
PY
```

Install platform-native prerequisites through the user's package manager or a conda/mamba environment. For WSI format support and reader selection, route to `wsi-io`.

## CPU, CUDA, and MPS Problems

Model commands accept `--device cpu`, `--device cuda`, and `--device mps`, but the string does not guarantee backend availability.

- Use `--device cpu` for portable CLI examples and smoke checks.
- Check `torch.cuda.is_available()` before suggesting `--device cuda`.
- Check `torch.backends.mps.is_available()` before suggesting `--device mps`.
- If CUDA is unavailable, do not fix it by changing TIAToolbox arguments alone; the user needs a compatible PyTorch build, driver/runtime, and hardware.

## Hugging Face or Model Download Failures

Pretrained model commands may download weights or metadata. Failures can come from offline environments, proxy/TLS issues, missing cache permissions, or interrupted downloads.

Mitigations:

- Use `--weights` with a local weights file when the user has one.
- Keep `--device cpu` and a small `--batch-size` for first-run validation.
- Confirm the environment can reach the model host before launching large WSI inference.
- Route model registry, supported model names, and custom weight compatibility to `model-inference`.

## JSON and Boolean Parsing Errors

`--class-dict`, `--input-resolutions`, and `--output-resolutions` expect JSON, not Python literals. Use double quotes inside JSON and shell quoting outside it:

```bash
--input-resolutions '[{"units":"mpp","resolution":0.5}]'
--class-dict '{"0":"background","1":"tumour"}'
```

Resolution options require a JSON list of dictionaries; a single dictionary is rejected. Boolean options in the Click CLI take explicit values such as `True` or `False`. `--return-predictions` takes a comma-separated boolean list such as `true,false`.

## Output Path and Extension Errors

Model commands reject an existing `--output-path` before running inference. Use a new output directory or intentionally pass `--overwrite True` where supported. If the user expected `--output-file` to be a path, clarify that it is the output filename paired with `--output-path`.

For output format questions:

- `--output-type` supports `zarr` or `AnnotationStore` on model commands that expose it.
- File extensions and storage details are model/workflow-specific; route interpretation to `model-inference` or `annotation-visualization` as appropriate.

## Visualization Port Conflicts

`visualize` launches a tile server and Bokeh server. `--port` controls the Bokeh port; the tile server reads `TIATOOLBOX_TILESERVER_PORT` and defaults to `5000`.

If a port is in use:

```bash
TIATOOLBOX_TILESERVER_PORT=5010 tiatoolbox visualize --base-path viewer_data --port 5011 --noshow
```

Use `--noshow` in remote/headless sessions. Route layer names, overlays, color maps, and browser behavior to `annotation-visualization`.

## Broad Install vs CPU Requirements

Full TIAToolbox installs include model, visualization, WSI, and image-processing dependencies. For CPU-only model usage, install CPU PyTorch wheels in the environment before installing or resolving TIAToolbox dependencies when appropriate. For conda/mamba environments, include native packages such as OpenJPEG and SQLite up front to reduce binary compatibility surprises.

Do not advise installing every optional or development dependency unless the user explicitly needs full development/test coverage.

## Fast Decision Tree

1. Does `python -c "import tiatoolbox"` work? If no, fix installation.
2. Does `tiatoolbox --help` work? If no, fix console entry point or environment activation.
3. Does `tiatoolbox <command> --help` work? If no, check command spelling and package version.
4. Does parsing fail before work starts? Check JSON, boolean, `nargs`, and mode choices.
5. Does work fail after parsing? Route to the workflow owner: `wsi-io`, `image-preprocessing`, `model-inference`, or `annotation-visualization`.
