# Maestro installation and CLI reference

Read this when selecting package extras, checking CLI routes, or turning a user request into a safe Maestro command. Model-specific training details live in the model sub-skills.

## Package identity

- Distribution name: `maestro`
- Import package: `maestro`
- Console command: `maestro`
- Supported Python versions from package metadata: `>=3.9,<3.13`
- Version captured during skill creation: `1.1.0rc3`

## Install variants

Use a dedicated environment for each real model-training family when possible:

```bash
pip install maestro
pip install "maestro[florence_2]"
pip install "maestro[paligemma_2]"
pip install "maestro[qwen_2_5_vl]"
```

Why separate environments help:

- Florence-2 extra includes PEFT, Transformers, PyTorch, and `flash-attn` on non-Darwin platforms. `flash-attn` can be compiler/CUDA-sensitive.
- PaliGemma 2 extra includes PEFT, Transformers, PyTorch, and `bitsandbytes` for QLoRA.
- Qwen2.5-VL extra includes Accelerate, PEFT, PyTorch, TorchVision, Transformers, `bitsandbytes`, and `qwen-vl-utils`.
- Qwen support has historically depended on recent or source-built Transformers; if Qwen classes are missing, upgrade or install a compatible Transformers build.
- For this source version, Qwen detection formatting matched `qwen-vl-utils==0.0.8`; newer `qwen-vl-utils` releases may require a pin if `smart_resize(...)` errors appear.

## Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `ROBOFLOW_API_KEY` | common dataset resolver | Required when `dataset` is a Roboflow identifier rather than an existing local path. |
| `HF_TOKEN` | model access outside Maestro code | Useful for gated/private Hugging Face models. Authenticate before running model downloads. |
| `DISABLE_RECIPE_IMPORTS_WARNINGS` | CLI recipe discovery | Set to `True` to suppress warnings when optional model dependencies are missing and some CLI subcommands cannot import. |
| `MAESTRO_LIGHTNING_LOG_LEVEL` | logging utilities | Controls PyTorch Lightning logging level, e.g. `INFO`, `WARNING`, `DEBUG`. |
| `MAESTRO_TRANSFORMERS_PROGRESS` | logging utilities | Set to `1` to enable Transformers progress bars; unset or another value disables them through Maestro logging helpers. |

## Root CLI map

```bash
maestro --help
maestro info
maestro version
maestro florence_2 train --help
maestro paligemma_2 train --help
maestro qwen_2_5_vl train --help
```

If model-specific optional dependencies are not installed, the CLI may print recipe-import warnings and hide subcommands. Install the relevant extra or set `DISABLE_RECIPE_IMPORTS_WARNINGS=True` only when you intentionally want root command probing without model routes.

## Model train command families

### Florence-2

```bash
maestro florence_2 train \
  --dataset ./dataset \
  --model_id microsoft/Florence-2-base-ft \
  --revision refs/pr/20 \
  --device auto \
  --optimization_strategy lora \
  --epochs 10 \
  --batch_size 4 \
  --accumulate_grad_batches 8 \
  --metrics edit_distance
```

Supported optimization strategies: `lora`, `freeze`, `none`. Route to [Florence-2](../sub-skills/florence-2/SKILL.md) for details and detection formatting.

### PaliGemma 2

```bash
maestro paligemma_2 train \
  --dataset ./dataset \
  --model_id google/paligemma2-3b-pt-224 \
  --revision refs/heads/main \
  --device auto \
  --optimization_strategy lora \
  --epochs 10 \
  --batch_size 4 \
  --metrics edit_distance \
  --metrics bleu \
  --peft_advanced_params '{}'
```

Supported optimization strategies: `lora`, `qlora`, `freeze`, `none`. Route to [PaliGemma 2](../sub-skills/paligemma-2/SKILL.md) for JSON extraction and checkpoint details.

### Qwen2.5-VL

```bash
maestro qwen_2_5_vl train \
  --dataset ./dataset \
  --model_id Qwen/Qwen2.5-VL-3B-Instruct \
  --revision refs/heads/main \
  --device auto \
  --optimization_strategy qlora \
  --epochs 10 \
  --batch_size 4 \
  --lr 2e-4 \
  --metrics edit_distance \
  --system_message "Return only valid JSON." \
  --min_pixels 200704 \
  --max_pixels 1003520
```

Supported optimization strategies: `lora`, `qlora`, `none`. Route to [Qwen2.5-VL](../sub-skills/qwen-2-5-vl/SKILL.md) for chat, pixel, and detection-format guidance.

## Safe bundled probes

From the generated Maestro skill tree:

```bash
python scripts/check_maestro_environment.py --models all --json
python scripts/maestro_cli_probe.py --include-model-help --json
```

These probes check imports, package versions, backend visibility, and help text. They do not download models, contact Roboflow, or train.

## Command construction cautions

- The current Typer CLI exposes underscore option names such as `--batch_size`, not hyphenated aliases.
- Some model entrypoints parse `--peft_advanced_params` into a local variable only when the option is provided. If the CLI raises an unbound local variable error, pass `--peft_advanced_params '{}'` or use the Python API.
- `--metrics` is repeatable; use one flag per metric.
- A local dataset path takes precedence over Roboflow resolution. If the path does not exist and the string parses as `workspace/project[/version]`, Maestro may try Roboflow and require `ROBOFLOW_API_KEY`.
