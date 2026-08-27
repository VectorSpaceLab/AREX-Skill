# Validation Workflows

This reference explains how to construct ImageNet/ImageFolder validation commands from the MambaVision classification scripts. The full validation scripts are intentionally not bundled here because they are large, dataset-bound, and timm-derived; use these commands when you have a MambaVision source distribution or the installed package module that includes the validation entry point.

## Validation prerequisites

Before running a validation command, verify:

- A CUDA-capable environment is available for GPU validation, unless you intentionally pass `--device cpu` for a slow/debug-only run.
- `torch`, `timm`, `mamba-ssm`, `einops`, `Pillow`, and `requests` import successfully.
- Dataset root is an ImageFolder-compatible directory with class subdirectories. For ImageNet-style data this is usually either:
  - `DATA_ROOT/val/<class_name_or_wnid>/*.JPEG`, then pass `--data-dir DATA_ROOT --split val`; or
  - `VAL_DIR/<class_name_or_wnid>/*.JPEG`, then pass `--data-dir VAL_DIR`.
- A local checkpoint exists if using `validate.py --checkpoint ...`; otherwise `validate.py` and `validate_pip_model.py` may try to use pretrained weights.
- The output directory for `--results-file` already exists. The validation scripts write files but do not create parent directories.
- Use the dashed option `--data-dir`. Some informal snippets use an underscore spelling, but the parser defines `--data-dir`.

## Script choice

| Entry point | Best for | Weight behavior | Notes |
| --- | --- | --- | --- |
| `validate.py` | Source-style validation of a local checkpoint or a directory of checkpoints | If `--checkpoint` is present, constructs with `pretrained=False`, then loads the checkpoint. If no checkpoint is present, it treats the run as pretrained. | Run it as a script file, for example `python <validation-entrypoint> ...`, so its local model imports resolve. |
| `python -m mambavision.validate_pip_model` | Installed-package validation of the pip/Hugging Face pretrained family | The script creates `mambavision.create_model(..., pretrained=True, model_path=<script default>)`; if the cache file is absent it can download. If `--checkpoint` is also supplied, it loads that checkpoint after the pretrained load. | Good for online pretrained package validation; not ideal for strictly offline custom-checkpoint validation because the model-path is not exposed as a CLI option. |

For an offline custom checkpoint, prefer `validate.py` with `--checkpoint`.
For an installed-package pretrained validation where download/cache is acceptable, prefer `python -m mambavision.validate_pip_model`.

## Custom ImageFolder + checkpoint + JSON results

Use this pattern for the difficult usability case: a user has a custom ImageFolder validation tree and a local MambaVision checkpoint, and wants JSON output.

```bash
mkdir -p ./results
python <validation-entrypoint> \
  --model mamba_vision_T \
  --checkpoint ./checkpoints/mambavision_tiny_1k.pth.tar \
  --data-dir ./data/custom_imagenet \
  --split val \
  --batch-size 64 \
  --input-size 3 224 224 \
  --device cuda \
  --results-file ./results/mambavision_T_custom_val.json \
  --results-format json
```

Expected behavior:

- Logs model creation and parameter count.
- Builds a timm ImageDataset/ImageFolder loader from `./data/custom_imagenet/val` if that split folder exists, otherwise from `./data/custom_imagenet`.
- Prints a final `--result` delimiter followed by JSON on stdout.
- Writes JSON to `./results/mambavision_T_custom_val.json`.

CSV output uses the same command with:

```bash
  --results-file ./results/mambavision_T_custom_val.csv \
  --results-format csv
```

If the validation tree is directly the class-folder directory, omit `--split val` or leave the default; timm falls back to the root when no split child is found.

## Source validation against published 1K checkpoint

```bash
python <validation-entrypoint> \
  --model mamba_vision_T \
  --checkpoint ./checkpoints/mambavision_tiny_1k.pth.tar \
  --data-dir ./data/imagenet \
  --split val \
  --batch-size 128 \
  --input-size 3 224 224 \
  --device cuda \
  --results-file ./results/mambavision_T_imagenet.csv \
  --results-format csv
```

Recommended starting batch sizes:

| Family | Initial batch size suggestion |
| --- | ---: |
| `mamba_vision_T`, `mamba_vision_T2` | 128 |
| `mamba_vision_S` | 96 |
| `mamba_vision_B` | 64 |
| `mamba_vision_L`, `mamba_vision_L2` | 16-32 |
| 512-resolution 21K/L3 families | 1-8 |

Use `--retry` to let the script reduce batch size after recognized OOM errors:

```bash
python <validation-entrypoint> \
  --model mamba_vision_B \
  --checkpoint ./checkpoints/mambavision_base_1k.pth.tar \
  --data-dir ./data/imagenet \
  --split val \
  --batch-size 64 \
  --input-size 3 224 224 \
  --device cuda \
  --retry
```

## Installed package pretrained validation

When an online pretrained load is acceptable:

```bash
python -m mambavision.validate_pip_model \
  --model mamba_vision_T \
  --data-dir ./data/imagenet \
  --split val \
  --batch-size 128 \
  --input-size 3 224 224 \
  --device cuda \
  --results-file ./results/mambavision_T_pip.json \
  --results-format json
```

Caveats:

- This entry point creates the model with `pretrained=True` internally.
- It may download the model if the script's cache destination is absent.
- `--checkpoint` is parsed and loaded after pretrained creation; it does not prevent the initial pretrained creation.
- For no-download validation of a local checkpoint, use `validate.py` instead.

## 512-resolution 21K validation

Use the model's default input size/crop behavior for 512-resolution families:

```bash
python <validation-entrypoint> \
  --model mamba_vision_L2_512_21k \
  --checkpoint ./checkpoints/mambavision_L2_21k_240m_512.pth.tar \
  --data-dir ./data/imagenet \
  --split val \
  --batch-size 4 \
  --input-size 3 512 512 \
  --crop-mode squash \
  --crop-pct 0.93 \
  --device cuda \
  --results-file ./results/mambavision_L2_512_21k.json \
  --results-format json
```

For `mamba_vision_L3_512_21k`, start with batch size 1-2 and increase only after checking memory.

## Useful validation options

| Option | Use |
| --- | --- |
| `--model` | Factory name such as `mamba_vision_T`. |
| `--checkpoint` | Local `.pth` or `.pth.tar` checkpoint. A directory triggers bulk validation over checkpoint files. |
| `--data-dir` | Dataset root or validation split root. |
| `--split` | Split name searched under `--data-dir`, usually `val` or `validation`. |
| `--dataset` | Optional timm dataset name. Leave empty for folder-based datasets. |
| `--batch-size` | Per-run batch size before DataParallel multiplication. |
| `--input-size 3 H W` | Explicit channel/height/width. Use published default resolution for accuracy comparisons. |
| `--device cuda` | GPU validation. `--device cpu` is slow and not a replacement for CUDA proof. |
| `--amp --amp-impl native --amp-dtype float16` | Native AMP validation on CUDA. Disable if numerical or compatibility issues appear. |
| `--channels-last` | Can improve throughput on some CUDA systems. |
| `--num-gpu N` | Wraps model in `torch.nn.DataParallel`; for rigorous distributed evaluation, adapt a proper distributed launcher instead. |
| `--results-file PATH --results-format json` | Save summary in JSON. Use `csv` for spreadsheet output. |
| `--real-labels PATH` | Use ImageNet real labels JSON. |
| `--valid-labels PATH` | Restrict output logits to selected label indices. |
| `--retry` | Decay batch size after recognized OOM errors. |

## Expected validation signals

A successful validation run should produce:

- Per-batch log lines with loss, Acc@1, Acc@5, and images/second.
- A final summary similar to `Acc@1 ... Acc@5 ...`.
- stdout containing `--result` followed by JSON.
- Optional results file containing `model`, `top1`, `top1_err`, `top5`, `top5_err`, `param_count`, `img_size`, `crop_pct`, and `interpolation` fields.

If the script exits before data loading, inspect package imports and checkpoint paths. If it exits during the first forward pass, inspect CUDA, `mamba-ssm`, input shape, AMP, and batch size.

## Throughput vs validation

Validation images/second is not the same as the published throughput table. Validation includes data loading and preprocessing. For synthetic throughput, use the bundled `scripts/benchmark_mambavision.py` helper, note the exact GPU, batch size, precision, layout, and resolution, and treat results as local measurements only.
