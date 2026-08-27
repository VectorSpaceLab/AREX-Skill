# Inference and Sampling Troubleshooting

## Checkpoint and `resume_state` problems

### `resume_state` is still `null`

Pretrained inference and pretrained sample generation require `path.resume_state` in the config. The repository scripts do not expose a CLI flag for this field; edit the config or create a run-specific config copy before running.

Use the bundled builders with `--require-resume-state` to catch this before launching a model run.

### The checkpoint path ends in `_gen.pth`

`model/model.py` appends suffixes internally:

- generator weights: `<resume_state>_gen.pth`;
- optimizer state for training resume: `<resume_state>_opt.pth`.

Therefore the config value should be the checkpoint stem, for example `experiments/name/checkpoint/I830000_E32`, not `experiments/name/checkpoint/I830000_E32_gen.pth`. If the full file path is used, the script will look for a doubled name such as `I830000_E32_gen.pth_gen.pth`.

### Validation generation loads only generator weights

For `infer.py` and `sample.py -p val`, only the generator file is loaded. For `sample.py -p train` with a non-null resume stem, the optimizer file is also loaded; missing `_opt.pth` blocks training resume even when `_gen.pth` exists.

### Checkpoint architecture mismatch

A checkpoint must match the config's `which_model_G`, `unet` channels, channel multipliers, attention resolutions, target `image_size`, and conditional flag. Common mismatches are:

- using an unconditional `sample_*` checkpoint with `infer.py`;
- using `sr_sr3_64_512.json` with a 16→128 checkpoint;
- setting `conditional: true` while leaving `unet.in_channel: 3`, or setting `conditional: false` with `unet.in_channel: 6`.

## Config parsing and phase surprises

### Standard JSON tools fail on the config

The repo configs contain `//` comments. The repo logger strips those comments before `json.loads`. Use the bundled command builders or a JSONC-aware parser instead of plain `json.load` when inspecting configs.

### The config says `"phase": "train"` but the command is validation

The logger parser overwrites `opt['phase']` from the CLI `-p/--phase` argument. For inference, `infer.py` only accepts `val`. For sample generation, pass `sample.py -p val` explicitly because the script default is `train`.

### Debug mode changes more than log names

`-debug/-d` prefixes the experiment name with `debug_` and shrinks training frequencies, timesteps, batch/data lengths through the shared logger parser. Use it only when those behavior changes are intended.

## Data-layout failures

### `infer.py` cannot construct the validation dataset

For `datatype: img`, check the validation `dataroot` layout. A 64→512 inference config with `mode: LRHR` expects directories like:

```text
<dataroot>/lr_64
<dataroot>/sr_64_512
<dataroot>/hr_512
```

`infer.py` uses `SR` as the model conditioning input and saves it as `_inf.png`; the shared dataset class may still load `LR` when `mode: LRHR`. If true HR images are unavailable, the README says the HR directory can mirror the ready-to-super-resolve images so the dataset object can still be built.

### `sample.py -p val` appears to ignore dataset paths

This is expected. Validation-mode unconditional sampling does not create a validation dataloader. It uses only `datasets.val.data_len` as the number of samples to draw.

### `sample.py -p train` still asks for `sr_*` data

The repository reuses the same dataset class for unconditional training. Even with `mode: HR` and `conditional: false`, the dataset implementation loads both `hr_<R>` and `sr_<L>_<R>` image directories for `datatype: img`.

### LMDB paths fail with missing keys

For `datatype: lmdb`, the dataset expects a `length` key plus keys such as `hr_<R>_<index>` and `sr_<L>_<R>_<index>`, with zero-padded five-digit indexes. Use the data-preparation sub-skill for LMDB construction and validation.

## CUDA, runtime, and memory failures

### No CPU-only path in stock commands

The stock configs and logger path assume GPU ids are available. If `-gpu` is omitted, `gpu_ids` from the config are used and `CUDA_VISIBLE_DEVICES` is set. A reliable CPU-only run requires code/config changes outside this sub-skill's command-building scope.

### CUDA out of memory

The 64→512 SR config is heavy and uses 2000 reverse steps. Reduce workload only through an intentional config copy, for example by lowering validation `data_len`, using debug mode for smoke checks, choosing a smaller resolution config, or running on a GPU with more memory. Do not present a reduced-timestep result as equivalent to the pretrained full config.

### Runs look stalled

Reverse diffusion is iterative and slow. Inference/generation may spend a long time per image, especially for 512×512 outputs and process-grid saving. Confirm GPU utilization and output directory timestamps before interrupting.

## W&B and logging failures

### W&B import or login errors

`-enable_wandb` initializes the repository's `WandbLogger`. Install and authenticate W&B before using it. For offline/local-only runs, omit `-enable_wandb`, `-log_infer`, and `-log_wandb_ckpt`.

### `-log_infer` does nothing

`infer.py` logs inference tables only when both `-enable_wandb` and `-log_infer` are set. `sample.py` does not have `-log_infer`; validation sample images are logged when W&B is enabled.

### Results are not in plain `results/`

The logger rewrites configured paths into a timestamped experiment directory. Look under `experiments/<name>_<timestamp>/results`, not the literal `results` path in the JSON file.

## Output interpretation issues

### `_inf.png` is not the generated result

`infer.py` writes `_inf.png` for the prepared input/conditioning image. The final SR result is `_sr.png`; `_sr_process.png` is the reverse-diffusion process grid.

### `sample.py` training validation writes `_sr.png`

During training validation, `sample.py` names unconditional validation outputs with `_sr.png`. Treat these as sample images produced during the unconditional training loop, not supervised super-resolution predictions.
