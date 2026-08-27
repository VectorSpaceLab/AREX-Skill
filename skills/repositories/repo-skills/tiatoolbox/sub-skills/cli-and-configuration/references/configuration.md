# TIAToolbox CLI Configuration Notes

This reference covers CLI-facing configuration only: JSON strings, YAML IO config paths, device selection, output handling, and safe command assembly. Route deeper model IO semantics to `model-inference` and WSI resolution decisions to `wsi-io`.

## JSON Arguments

Several model commands parse JSON values through Click callbacks:

- `--input-resolutions`: JSON list of dictionaries, for example `[{"units":"mpp","resolution":0.5}]`.
- `--output-resolutions`: JSON list of dictionaries, for example `[{"units":"mpp","resolution":0.5}]`.
- `--class-dict`: JSON object mapping class ids to names, for example `{"0":"background","1":"tumour"}`. Numeric string keys are converted to integer keys internally when possible.

Invalid JSON fails before inference with an `Invalid JSON` Click error. Passing a JSON object to `--input-resolutions` or `--output-resolutions` fails because those options require a JSON list of dictionaries.

## Shell Quoting Recipes

On POSIX shells, wrap JSON in single quotes so JSON double quotes survive:

```bash
tiatoolbox semantic-segmentor \
  --img-input slides \
  --output-path semantic_out \
  --input-resolutions '[{"units":"mpp","resolution":0.5}]' \
  --output-resolutions '[{"units":"mpp","resolution":0.5}]' \
  --class-dict '{"0":"background","1":"tumour"}' \
  --device cpu
```

In PowerShell, single quotes also pass the JSON content literally:

```powershell
tiatoolbox semantic-segmentor --img-input slides --output-path semantic_out --input-resolutions '[{"units":"mpp","resolution":0.5}]' --class-dict '{"0":"background","1":"tumour"}' --device cpu
```

When building commands from Python, avoid manual shell strings. Use `json.dumps` and pass an argument list:

```python
import json
import subprocess

cmd = [
    "tiatoolbox", "semantic-segmentor",
    "--img-input", "slides",
    "--output-path", "semantic_out",
    "--input-resolutions", json.dumps([{"units": "mpp", "resolution": 0.5}]),
    "--class-dict", json.dumps({"0": "background", "1": "tumour"}),
    "--device", "cpu",
]
subprocess.run(cmd, check=True)
```

## YAML IO Config

Model commands expose `--yaml-config-path` for an IO configuration file. Use it when providing custom weights or when the default pretrained model IO configuration is not appropriate. Keep the path as a normal file path token; do not inline YAML on the command line.

Practical notes:

- YAML loading is handled with `yaml.safe_load` before constructing the model IO config object.
- The YAML schema is model-engine specific; route details to `model-inference`.
- If a command uses pretrained model defaults, the IO config is normally inferred and `--yaml-config-path` can be omitted.
- When providing custom `--weights`, provide a matching `--yaml-config-path` if the model cannot infer input/output patch sizes, resolutions, or heads from the default registry.

## Device and Backend Selection

The model commands accept `--device` values such as `cpu`, `cuda`, and `mps`. Device availability depends on the installed PyTorch build and hardware:

- `cpu` is the safest portable default and is appropriate for smoke tests and examples.
- `cuda` requires a CUDA-capable PyTorch installation and compatible drivers.
- `mps` is for Apple Silicon builds where PyTorch reports MPS availability.

Safe backend probes:

```bash
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
print("mps", hasattr(torch.backends, "mps") and torch.backends.mps.is_available())
PY
```

If a user asks for performance tuning, route batch size, worker count, memory threshold, and model-specific trade-offs to `model-inference`.

## Install and Import Validation

A minimal install validation does not need a source checkout:

```bash
python - <<'PY'
import tiatoolbox
print(tiatoolbox.__version__)
PY
tiatoolbox --version
tiatoolbox --help
```

TIAToolbox targets Python 3.11 through 3.14 in package metadata and CI. Full installs include image, WSI, model, visualization, and data dependencies. CPU-only torch installs can use a CPU PyTorch index before installing TIAToolbox dependencies when GPU support is not required.

Native/library dependencies matter for WSI and codecs. Typical prerequisites include OpenJPEG, SQLite, OpenSlide Python bindings/binaries, image codecs, and PyTorch. If imports succeed but specific WSI formats fail, route format-specific diagnosis to `wsi-io` after checking native libraries.

## Output Path and File Handling

- Model commands use `prepare_model_cli`, which raises `FileExistsError` when `--output-path` already exists. Pick a fresh output directory or pass `--overwrite True` only when the command supports and the user intends overwriting.
- Utility commands using save mode generally create output directories with parent directories as needed.
- `--output-file` is a filename, not the output directory. Pair it with `--output-path` when a model command supports a single named result.
- `--file-types` is parsed as a comma-separated set of glob patterns. Use quotes around values containing spaces after commas.
- Mask directories are scanned for supported mask file types; a single mask file is treated as a one-item mask list.

## Safe Command Builder Pattern

For agents generating shell commands:

1. Represent structured values as Python objects.
2. Serialize JSON arguments with `json.dumps(..., separators=(",", ":"))`.
3. Store all CLI tokens in a list.
4. Validate with `tiatoolbox <command> --help` before expensive inference.
5. Convert to a shell string only for presentation, using `shlex.join` on POSIX-like shells.

Example semantic-segmentor token list:

```python
import json
import shlex

cmd = [
    "tiatoolbox", "semantic-segmentor",
    "--img-input", "slides",
    "--output-path", "semantic_out",
    "--input-resolutions", json.dumps([{"units": "mpp", "resolution": 0.5}], separators=(",", ":")),
    "--output-resolutions", json.dumps([{"units": "mpp", "resolution": 0.5}], separators=(",", ":")),
    "--class-dict", json.dumps({"0": "background", "1": "tumour"}, separators=(",", ":")),
    "--device", "cpu",
    "--batch-size", "4",
]
print(shlex.join(cmd))
```
