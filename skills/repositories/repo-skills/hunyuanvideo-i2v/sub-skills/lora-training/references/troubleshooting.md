# LoRA Training Troubleshooting

## Purpose

Read this when the training launcher, dataset, DeepSpeed init, or LoRA checkpoint handling fails.

## Missing or Invalid Required Inputs

**Symptoms**

- `--task-flag` missing
- `--output-dir` missing
- `--data-jsons-path` missing or pointing to the wrong directory

**Fix**

- Use the bundled wrapper in `--dry-run` mode first.
- Confirm the processed latent directory exists and contains JSON + `.npy` pairs.

## Checkpoint Tree Failures

**Symptoms**

- `No model weights found`
- `AssertionError: VAE checkpoint not found`
- text encoder/tokenizer paths missing
**Fix**

- Validate the tree from the real checkout root with `python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode train`.
- Read [`../../../references/checkpoints.md`](../../../references/checkpoints.md); the repository does not ship placeholder weights.

## DeepSpeed / Distributed Setup Problems

**Symptoms**

- `deepspeed.init_distributed()` errors
- batch-size divisibility assertions
- the launcher hangs before the first training log line

**Fix**

- Use the single-node launcher first.
- Keep `--video-micro-batch-size 1` unless you know the memory headroom.
- Confirm the world size matches the include list passed to DeepSpeed.

## Dataset Schema Errors

**Symptoms**

- `TypeError` or `KeyError` while loading the processed latent JSONs
- missing `.npy` files
- cached latents with the wrong temporal length

**Fix**

- Run the data-preparation checker on the processed JSON directory.
- Regenerate the latents if the output metadata and the `.npy` file disagree.

## LoRA Weight Loading Problems

**Symptoms**

- `load_lora` fails to map keys
- the effect is trained but not applied during inference

**Fix**

- Confirm the weight is in Kohya-format `.safetensors`.
- Verify the LoRA file path and scale passed to both training and inference.
- Keep the same model family and text-encoder setup between train and infer.

## Memory Pressure

**Symptoms**

- CUDA OOM before the first epoch finishes
- training is much slower than expected

**Fix**

- Keep the batch size at the launcher defaults.
- Use gradient checkpointing.
- The README’s 360p training memory note is large; 40GB GPUs may still be insufficient for full-scale training.

## Debug Order

Run from `$CHECKOUT_ROOT`; `$SKILL_ROOT` is the generated-skill directory:

1. `python "$SKILL_ROOT/scripts/check_runtime.py" --repo-root "$CHECKOUT_ROOT" --check-imports --check-decord --check-omegaconf`
2. `python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode train`
3. `python "$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py" --mode processed --json-dir ...`
4. `python "$SKILL_ROOT/sub-skills/lora-training/scripts/run_lora_training.py" --repo-root "$CHECKOUT_ROOT" --dry-run ...`
