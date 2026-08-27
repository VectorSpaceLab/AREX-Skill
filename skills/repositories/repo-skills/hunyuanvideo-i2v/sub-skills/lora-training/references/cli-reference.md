# LoRA Training CLI Reference

## Purpose

Use this for the verified training flags and their main defaults. The values come from `hyvideo/config.py`, the training script, and the repo launcher.

## Required Launcher Inputs

| Flag | Notes |
| --- | --- |
| `--task-flag` | Required; drives the experiment directory name |
| `--output-dir` | Required; base directory for logs and checkpoints |
| `--data-jsons-path` | Required for the video dataset path |

## Frequently Used Defaults

| Flag | Default | Notes |
| --- | --- | --- |
| `--model` | `HYVideo-T/2` in the launcher | Backbone used by the effect-training example |
| `--precision` | `bf16` in config, launcher sets training precision through args | Main model precision |
| `--vae` | `884-16c-hy` | VAE model name |
| `--vae-precision` | `fp16` | VAE precision |
| `--vae-tiling` | on | Memory-saving VAE mode |
| `--i2v-mode` | on | Training is configured for image-to-video |
| `--flow-shift` | `7.0` | Flow-matching shift used by the launcher |
| `--zero-stage` | `2` | DeepSpeed ZeRO stage |
| `--video-micro-batch-size` | `1` | Per-device video batch size |
| `--sample-n-frames` | `129` | Training video length in the launcher |
| `--sample-stride` | `1` | Frame stride |
| `--lora-rank` | `64` | LoRA rank |
| `--gradient-checkpoint` | on | Memory-saving training mode |
| `--ckpt-every` | `500` | Save interval in steps |
| `--tensorboard` | on | Enable TensorBoard logging |

## Data and Encoder Flags

The launcher also sets these flags because the effect-training workflow depends on the I2V text-encoder path:

- `--text-encoder llm-i2v`
- `--tokenizer llm-i2v`
- `--text-encoder-2 clipL`
- `--tokenizer-2 clipL`
- `--prompt-template dit-llm-encode-i2v`
- `--prompt-template-video dit-llm-encode-video-i2v`

## Helpful Runtime Flags

- `--resume` — continue from an experiment index or path
- `--init-from` — initialize from a checkpoint
- `--final-save` / `--no-final-save` — control the final checkpoint save
- `--warmup-num-steps` — enable the warmup scheduler
- `--global-batch-size` / `--micro-batch-size` / `--gradient-accumulation-steps` — batch-size accounting

## Output Contract

The training script logs the resolved args, code snapshot, and experiment path before the first update. The final LoRA weights are written under a checkpoint directory in the experiment tree.
