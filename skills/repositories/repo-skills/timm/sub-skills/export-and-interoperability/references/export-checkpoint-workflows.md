# Export and Checkpoint Workflows

This reference covers timm's ONNX export/validation scripts and checkpoint publication tools. Keep commands explicit, dry-run where possible, and verify optional dependencies before promising execution.

## ONNX Export

`timm` exports through a repository-root `onnx_export.py` script that creates a model with `exportable=True` and calls `timm.utils.onnx.onnx_export`. When `--checkpoint` is absent, the script sets `pretrained=True`; when `--checkpoint` is present, it sets `pretrained=False` and loads the checkpoint path into the created model.

| Option | Purpose | Guidance |
| --- | --- | --- |
| `output` | Destination ONNX filename | Use a new or explicitly replaceable file path. |
| `--model`, `-m` | timm architecture/tag | Prefer exact model names from model-library discovery. |
| `--checkpoint` | Local checkpoint path | Use for fine-tuned weights; disables default pretrained download. |
| `--opset` | ONNX opset | Leave unset first unless deployment requires a specific opset. |
| `--input-size C H W` | Full input shape without batch | Prefer over `--img-size` when channels or rectangular inputs matter. |
| `--img-size N` | Square image size shortcut | Uses `(3, N, N)`. |
| `--batch-size` | Export batch dimension | Default is `1`; align with deployment if batch is fixed. |
| `--dynamic-size` | Dynamic width/height axes | Useful for variable image sizes, but not recommended for TensorFlow-style SAME padding models. |
| `--check-forward` | Compare PyTorch and ONNX forward outputs | Requires ONNX validation stack; use after the command exports successfully. |
| `--keep-init` | Keep initializers as graph inputs | Mainly for Caffe2 compatibility with newer PyTorch/ONNX. |
| `--aten-fallback` | Allow ATEN fallback ops | Mainly for Caffe2 or unsupported op workarounds. |
| `--reparam` | Reparameterize model before export | Use for families that support deploy-time reparameterization. |
| `--training` | Export in training mode | Rare for inference deployment; default is eval. |
| `--verbose` | Extra export output | Useful when diagnosing graph export problems. |
| `--dynamo` | Use Torch Dynamo export path | Try when the classic exporter fails, but expect version-sensitive behavior. |

Example static export command:

```bash
python onnx_export.py resnet18.onnx --model resnet18 --input-size 3 224 224 --batch-size 1
```

Example dynamic export command with forward check:

```bash
python onnx_export.py convnext_tiny.onnx --model convnext_tiny --input-size 3 224 224 --dynamic-size --check-forward
```

When adapting a command for an agent, include the model name, output path, shape, and checkpoint behavior in the answer. Avoid claiming that every timm architecture exports cleanly; ONNX behavior is sensitive to PyTorch, ONNX, ONNX Runtime, opset, and model internals.

## ONNX Runtime Validation

`timm` validates exported ONNX models with `onnx_validate.py`, which creates an ONNX Runtime session, builds a timm data loader, runs inference, and reports top-1/top-5 metrics.

| Option | Purpose | Guidance |
| --- | --- | --- |
| `data` | Dataset directory | Usually the validation image split. |
| `--onnx-input` | ONNX model file | Required for meaningful validation. |
| `--onnx-output-opt` | Write optimized ONNX graph | Optional; useful for inspecting ORT graph optimization output. |
| `--profile` | Enable ORT profiler | Use for runtime analysis, not basic correctness. |
| `--batch-size` | Validation batch size | Lower when CPU or memory constrained. |
| `--workers` | Data loading workers | Use `0` or `1` for constrained/debug hosts. |
| `--img-size` | Override image size | Match export shape unless dynamic export is intentional. |
| `--mean`, `--std` | Override normalization | Match the model pretrained config. |
| `--crop-pct` | Override crop percentage | Match the model pretrained config. |
| `--interpolation` | Resize interpolation | Match model/data pipeline. |
| `--print-freq` | Logging cadence | Increase for large datasets to reduce output. |

Example validation command:

```bash
python onnx_validate.py /data/imagenet/val --onnx-input resnet18.onnx --batch-size 64 --workers 4
```

Validation depends on `onnxruntime`, `numpy`, timm data transforms, and a real labeled dataset. For quick export smoke tests without a dataset, use `--check-forward` on export if optional ONNX packages are installed.

## Checkpoint Cleaning

`timm`'s checkpoint cleaner loads a checkpoint on CPU via timm state-dict loading, chooses EMA weights by default when present, strips wrapper keys, removes `module.` prefixes, optionally drops SplitBN `aux_bn` keys, then writes a state dict with a SHA256-based filename unless hashing is disabled.

| Option | Purpose | Guidance |
| --- | --- | --- |
| `--checkpoint` | Input checkpoint | Must be a trusted local file. |
| `--output` | Output path or base path | The original script refuses to overwrite existing files. |
| `--no-use-ema` | Do not prefer EMA weights | Use when the user needs raw model weights. |
| `--no-hash` | Do not append SHA256 prefix | Use only when deterministic naming matters more than model-zoo style names. |
| `--clean-aux-bn` | Remove auxiliary SplitBN keys | Use when loading into a normal BatchNorm model. |
| `--safetensors` | Save as safetensors | Preferred for sharing if `safetensors` is installed. |

Example clean command:

```bash
python clean_checkpoint.py --checkpoint train-output/model_best.pth.tar --output model_best_clean.pth --safetensors
```

Cleaned checkpoints contain model weights only. They do not preserve optimizer state, epoch counters, scaler state, or training arguments.

## Checkpoint Averaging

`timm`'s averaging script selects checkpoint files with a glob, optionally sorts by stored metric, loads state dicts with EMA by default, accumulates tensors in float64, divides by per-key counts, clamps to float32 range, and saves float32 averaged weights.

| Option | Purpose | Guidance |
| --- | --- | --- |
| `--input` | Folder containing checkpoints | Combine with `--filter`. |
| `--filter` | Glob pattern | Default is `*.pth.tar`; can include recursive patterns. |
| `-n` | Number of top metric checkpoints | Used only when sorting by metric. |
| `--no-sort` | Average every matched file without metric sorting | Use when checkpoints lack metrics or ordering is manual. |
| `--no-use-ema` | Average raw weights instead of EMA | Keep consistent with training/eval target. |
| `--output` | Output checkpoint | Refuses overwrite; defaults to `.safetensors` when `--safetensors` is set and output remains default. |
| `--safetensors` | Save as safetensors | Preferred for distribution when available. |

Example average command:

```bash
python avg_checkpoints.py --input train-output --filter 'checkpoint-*.pth.tar' -n 5 --output averaged.safetensors --safetensors
```

Only average checkpoints from the same architecture and compatible training lineage. Averaging unrelated checkpoints or mismatched heads produces unusable or partially averaged weights.

## Helper Script Usage

The bundled ONNX command builder mirrors the option names above without importing timm:

```bash
python scripts/timm_onnx_command_builder.py export \
  --output model.onnx --model resnet18 --input-size 3 224 224 --dynamic-size
```

The checkpoint helper supports self-contained inspection plus safe command construction for cleaning and averaging:

```bash
python scripts/timm_checkpoint_tools.py clean-command \
  --checkpoint model_best.pth.tar --output model_best_clean.safetensors --safetensors
```

`clean-command` prints a command for a trusted timm script checkout or copied `clean_checkpoint.py`; the bundled helper does not import checkout-local cleaning code. Its `average` subcommand is self-contained when `torch`, `timm`, and optional `safetensors` are installed, and it refuses to overwrite existing outputs.
