---
name: "inference"
description: "Routes HunyuanVideo-I2V image-to-video generation tasks, including
  stable/dynamic motion recipes, LoRA-augmented sampling, xDiT multi-GPU
  inference, and the checkpoint checks needed before a real render."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Inference

Use this sub-skill when the user wants to turn a single image into a video, compare stable versus dynamic motion, run LoRA-augmented sampling, or understand the xDiT parallel inference path.

## What Belongs Here

- Single-image I2V generation commands.
- Stable vs dynamic motion settings (`--i2v-stability`, `--flow-shift`).
- LoRA inference (`--use-lora`, `--lora-path`, `--lora-scale`).
- xDiT/sequence-parallel generation (`--ulysses-degree`, `--ring-degree`, `ALLOW_RESIZE_FOR_SP`).
- Output naming, save-path handling, and sampler-level constraints.

## What Does Not Belong Here

- Training a new LoRA model. Use [`../lora-training/SKILL.md`](../lora-training/SKILL.md).
- Building the latent dataset from raw videos. Use [`../data-preparation/SKILL.md`](../data-preparation/SKILL.md).
- Downloading checkpoints or validating the asset tree. Use [`../../references/checkpoints.md`](../../references/checkpoints.md) and [`../../scripts/check_checkpoint_layout.py`](../../scripts/check_checkpoint_layout.py).

## Read First

- [`references/workflows.md`](references/workflows.md) for stable, dynamic, LoRA, and xDiT command patterns.
- [`references/cli-reference.md`](references/cli-reference.md) for the verified CLI flags and their main defaults.
- [`references/api-reference.md`](references/api-reference.md) for the sampler class, `predict()` signature, and load helpers.
- [`references/troubleshooting.md`](references/troubleshooting.md) for CUDA, flash-attn, checkpoint, memory, and xDiT failures.

## Bundled Scripts

- [`scripts/run_sample_image2video.py`](scripts/run_sample_image2video.py) — build or execute the canonical inference command safely. This helper is under `$SKILL_ROOT`; run it from `$CHECKOUT_ROOT` with `--repo-root "$CHECKOUT_ROOT"`. Run with `--dry-run` first, then add `--execute` only after checkpoint and GPU checks pass.

## Typical Workflow

Commands run from the real checkout root. `$SKILL_ROOT` is the generated skill directory, not the checkout:

1. Confirm the checkpoint tree with `$SKILL_ROOT/scripts/check_checkpoint_layout.py --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode inference`.
2. Decide whether the request is stable, dynamic, LoRA-augmented, or xDiT parallel inference.
3. Use `$SKILL_ROOT/sub-skills/inference/scripts/run_sample_image2video.py --repo-root "$CHECKOUT_ROOT"` to print the exact command.
4. If the user approves execution, rerun the wrapper with `--execute`.
5. Inspect the mp4 files written under the chosen `--save-path`.

## Constraints to Remember

- `video_length - 1` must be a multiple of 4.
- `i2v_resolution` is limited to `360p`, `540p`, or `720p`.
- The code aligns height and width to 16.
- The inspected model path uses flash-attn by default.
- xDiT needs `ring_degree * ulysses_degree` to equal the active GPU count.
- The README documents large-memory requirements for full 720p runs; use `--use-cpu-offload` or a lower resolution if the host cannot fit the model.
