# LoRA Training Workflows

## Purpose

Read this when you need the canonical LoRA training flow or want to understand the launcher defaults that the repo uses in practice.

## 1) Canonical single-node run

The repo’s shell launcher sets a large bundle of defaults and then runs one DeepSpeed process on localhost.

Important defaults from the inspected script:

- `--lr 1e-4`
- `--warmup-num-steps 500`
- `--global-seed 1024`
- `--tensorboard`
- `--zero-stage 2`
- `--vae 884-16c-hy`
- `--vae-precision fp16`
- `--vae-tiling`
- `--denoise-type flow`
- `--flow-reverse`
- `--flow-shift 7.0`
- `--i2v-mode`
- `--model HYVideo-T/2`
- `--video-micro-batch-size 1`
- `--gradient-checkpoint`
- `--ckpt-every 500`
- `--embedded-cfg-scale 6.0`
- `--use-lora`
- `--lora-rank 64`

Training-specific data defaults:

- `--data-type video`
- `--data-jsons-path ./assets/demo/i2v_lora/train_dataset/processed_data/json_path`
- `--sample-n-frames 129`
- `--sample-stride 1`
- `--num-workers 8`
- `--uncond-p 0.1`
- `--sematic-cond-drop-p 0.1`

Text encoder defaults:

- `--text-encoder llm-i2v`
- `--text-encoder-precision fp16`
- `--text-states-dim 4096`
- `--text-len 256`
- `--tokenizer llm-i2v`
- `--prompt-template dit-llm-encode-i2v`
- `--prompt-template-video dit-llm-encode-video-i2v`
- `--hidden-state-skip-layer 2`
- `--text-encoder-2 clipL`
- `--text-states-dim-2 768`
- `--tokenizer-2 clipL`
- `--text-len-2 77`

## 2) Resume or restart

The training script supports `--resume` and `--init-from`.

- Use `--resume <experiment-dir-or-index>` to continue from the latest checkpoint in an existing run directory.
- Use `--init-from <checkpoint>` to seed a new run from a specific checkpoint.
- Use `--output-dir` and `--task-flag` to control the new experiment directory.

## 3) Inspecting the output directory

The training code writes the run under `output-dir` with an experiment index prefix. The directory should contain:

- `args.json`
- tarred code snapshot
- `train.log`
- `val.log`
- checkpoints under `checkpoints/`

The final LoRA weight file is expected under a checkpoint directory named like:

```text
.../checkpoints/global_step*/pytorch_lora_kohaya_weights.safetensors
```

## 4) Safe wrapper usage

Run from the real checkout root. `$SKILL_ROOT` is the generated skill directory; `--repo-root` must be the checkout containing `train_image2video_lora.py`:

```bash
cd "$CHECKOUT_ROOT"
python "$SKILL_ROOT/sub-skills/lora-training/scripts/run_lora_training.py" \
  --repo-root "$CHECKOUT_ROOT" \
  --data-jsons-path "$CHECKOUT_ROOT/assets/demo/i2v_lora/train_dataset/processed_data/json_path" \
  --output-dir "$CHECKOUT_ROOT/log_EXP" \
  --task-flag demo_effect \
  --dry-run
```

Only add `--execute` once the dataset layout, checkpoint tree, optional DeepSpeed dependency, and GPU memory look correct. The wrapper does not create checkpoints or LoRA weights.
