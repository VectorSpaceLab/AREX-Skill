# Workflows

## Launcher contract

The training source uses a `src` layout nested below the checkout's `train/` directory. The bundled helper resolves configs from `train/train/config/`, runs with `cwd=<checkout>/train`, and puts that training root on `PYTHONPATH`:

```bash
export XFL_CONFIG=<checkout>/train/train/config/<config>.yaml
export TOKENIZERS_PARALLELISM=true
export PYTHONPATH=<checkout>/train
CUDA_VISIBLE_DEVICES=2 accelerate launch --main_process_port <PORT> -m src.train.train
```

The MoE command uses `-m src.train.train_moe`; its source prepends the checkout-vendored `icedit/` package. That fork and all training source/configs are checkout dependencies, not part of the standalone helper. The helper defaults to dry-run and refuses `--execute` when obvious local assets are missing.

## Normal LoRA workflow

1. Use the bundled helper with `--mode normal`.
2. Load the normal LoRA config.
3. `train.train` reads `XFL_CONFIG`, seeds the RNGs, calls `torch.cuda.set_device(rank)`, and builds `OminiModel`.
4. Rank 0 optionally initializes wandb, then the code loads MagicBrush plus the parquet shards, creates the Lightning trainer, and starts fitting.
5. `TrainingCallback` writes LoRA weights and sample images under `save_path/<run_name>/`.

## MoE LoRA workflow

1. Use the bundled helper with `--mode moe`.
2. Load the MoE LoRA config.
3. `train.train_moe` prepends the repo-root `icedit/` directory to `sys.path` so the vendored diffusers / peft fork is used before the installed packages.
4. The training loop is otherwise the same, but the config adds MoE-specific LoRA fields.

## Training loop facts

- `torch.cuda.set_device(rank)` runs before config loading, so CUDA must be available.
- `enable_checkpointing=False` disables Lightning `.ckpt` files.
- The only saved artifacts are the config snapshot and the callback-driven LoRA exports / sample images.
- `model.use_sep` also saves `t5_embedding.pth` and `clip_embedding.pth`.
- Wandb logging happens only on the main process and only if `WANDB_API_KEY` is present.

## Safe local validation

These checks are informative and do not start a full run:

- YAML syntax and required keys.
- Whether the config points at a real parquet glob.
- Whether `WANDB_API_KEY` is present.
- Whether the resolved `accelerate` command matches the intended GPU mapping and port.
- Whether the repo-root `icedit/` vendored package is present for MoE launches.

## Too expensive for a dry run

- Downloading datasets or model weights.
- Running `accelerate launch` with real GPUs.
- Repeated sampling or long training sweeps.
