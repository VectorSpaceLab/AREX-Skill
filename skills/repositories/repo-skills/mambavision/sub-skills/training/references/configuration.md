# MambaVision training configuration

The bundled YAML presets are loaded by `--config` / `-c`. The config file sets parser defaults first, then command-line arguments override those values.

## Shared defaults

Most 1K presets share the same training recipe:

- `input_size: [3, 224, 224]`
- `batch_size: 128`
- `lr: 0.005`
- `sched: cosine`
- `epochs: 310`
- `amp: true`
- `channels_last: true`
- `model_ema: true`
- `mixup: 0.8`
- `cutmix: 1.0`
- `reprob: 0.25`
- `workers: 8`
- `seed: 31`
- `data_len: 1281167`
- `train_split: train`
- `val_split: validation`
- `opt: lamb`
- `warmup_lr: 1e-6`
- `min_lr: 5e-6`

In distributed runs, treat `batch_size` as per GPU / per process; the effective global batch is `batch_size × world_size`.

`data_len` matters because the cosine scheduler computes iterations per epoch from it. If you change dataset scale or train on a subset, update it.

`drop_path` is not fixed in the YAMLs. Keep it explicit on the command line when you want the published launch recipe.

The historical `train.sh` launcher also forces a `crop_pct` override of `0.875`. When you are matching that shell recipe, pass the override explicitly even if the YAML preset uses `1.0`.

## Preset matrix

| Preset | YAML name | Backbone | Crop pct | Weight decay | Warmup epochs | MESA | Tag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tiny | `mambavision_tiny_1k.yaml` | `mamba_vision_T` | `1.0` | `0.05` | `20` | `0.5` | `mambavision_tiny_1k` |
| tiny2 | `mambavision_tiny2_1k.yaml` | `mamba_vision_T2` | `1.0` | `0.05` | `20` | `0.75` | `mambavision_tiny2_1k` |
| small | `mambavision_small_1k.yaml` | `mamba_vision_S` | `0.875` | `0.05` | `20` | `1.0` | `mambavision_small_1k` |
| base | `mambavision_base_1k.yaml` | `mamba_vision_B` | `1.0` | `0.075` | `35` | `1.0` | `mambavision_base_1k` |
| large | `mambavision_large_1k.yaml` | `mamba_vision_L` | `1.0` | `0.12` | `20` | `6.0` | `mambavision_large_1k` |
| large2 | `mambavision_large2_1k.yaml` | `mamba_vision_L2` | `1.0` | `0.12` | `20` | `6.0` | `mambavision_large2_1k` |

## How to choose a preset

- Use **tiny** or **tiny2** when you want the fastest turn-around or a lower-memory baseline.
- Use **small** when you want the 1K recipe with a more conservative validation crop (`0.875`).
- Use **base** when you want the published larger 1K checkpoint with a longer warmup.
- Use **large** or **large2** when you need the heavier capacity recipes and are prepared to budget more memory and time.

## CLI overrides that are commonly changed

| Override | Typical reason |
| --- | --- |
| `--data_dir` | Point at the local dataset root. |
| `--output` | Send checkpoints and logs to a chosen writable root. |
| `--tag` | Separate multiple experiments under the same output root. |
| `--batch-size` | Fit the model into GPU memory. |
| `--validation-batch-size` | Keep evaluation from OOMing. |
| `--crop-pct` | Match the validation crop recipe or the shell launcher override. |
| `--lr` | Tune the optimization schedule for a different batch size. |
| `--weight-decay` | Match the backbone size or fine-tune regime. |
| `--drop-path` | Control stochastic depth for a new training run. |
| `--resume` | Continue an interrupted training run. |
| `--initial-checkpoint` | Start from pretrained weights only. |
| `--model-ema` | Keep EMA weights for evaluation or MESA. |
| `--mesa` | Enable the memory-efficient sharpness objective. |
| `--channels-last` | Try a memory-format optimization on CUDA. |
| `--workers` | Reduce dataloader pressure on the host. |
| `--data_len` | Fix schedule length after dataset changes. |

## Preset-specific notes

- `small` is the only 1K preset with `crop_pct=0.875`.
- `base` has the longest warmup among the 1K presets.
- `large` and `large2` use the strongest MESA coefficient (`6.0`) and the highest weight decay (`0.12`).
- The YAML files already set `amp=true`, `channels_last=true`, and `model_ema=true`; only disable those if you are debugging a backend issue.
- If you enable `--mesa`, keep `--model-ema` on so the teacher branch exists.

## Scheduler interaction

The training script's scheduler factory supports `cosine`, `step`, `multistep`, `plateau`, `poly`, and `tanh`.
For the bundled 1K recipes, `cosine` is the intended choice.

If you change `--batch-size` or `--world-size`, the effective number of iterations per epoch changes, so verify that the scheduler still matches your intended training length.
