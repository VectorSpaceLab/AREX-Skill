---
name: training-data-configs
description: "Plan Sana training data schemas, config overrides, launch
  commands, and safe validation for image, video, LoRA, Sprint, WM, Streaming,
  and Sol-RL workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Sana training data and config planner

Use this sub-skill when a user asks how to prepare data, choose a training recipe, plan config overrides, or draft a safe launch command for Sana training or post-training. It covers image-text training, multi-scale WIDS/WebDataset data, DDP/FSDP image training, Sprint sCM/LADD, DreamBooth LoRA, SANA-Video, LongSANA, SANA-WM Stage-1 and distillation, SANA-Streaming V2V, Sol-RL, and the boundary to Cosmos-RL.

Do not use this sub-skill for inference-only requests. Route image inference to the image-generation sub-skill, video/world/streaming inference to the video-world-streaming sub-skill, and metrics, conversion, or deployment requests to the evaluation-conversion-deployment sub-skill.

## Fast operating path

1. Classify the request into one training family:
   - image: SanaImgDataset image-text pairs or SanaWebDatasetMS WIDS/WebDataset shards.
   - sprint: one-step Sana-Sprint sCM plus LADD training.
   - lora: DreamBooth LoRA over a diffusers Sana base model.
   - video: SANA-Video 480p WanVAE or 720p LTX2 VAE training.
   - longsana: LongSANA ODE, self-forcing, or long-video stage.
   - wm-stage1: SANA-WM bidirectional or chunk-causal Stage-1 teacher.
   - wm-distill: SANA-WM ODE, T43 self-forcing, or T121 self-forcing/DMD distillation.
   - streaming-v2v: SANA-Streaming bidirectional short V2V or long V2V fine-tuning.
   - sol-rl: in-repo reinforcement-learning post-training launchers.
   - cosmos-rl: external Cosmos-RL SFT/RL integration boundary.
2. Identify the data schema and verify it before planning training. Use the bundled validator when the user gives a local data path:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/my_sana_data \
  --mode auto \
  --max-samples 20
```

3. Generate a safe command plan instead of launching training. Use the bundled planner for a first draft:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/plan_training_command.py \
  --family image \
  --data-dir data/my_sana_data \
  --data-type SanaImgDataset \
  --work-dir output/my_sana_run \
  --gpus 2 \
  --batch-size 8 \
  --num-workers 4
```

4. Explain what the plan can and cannot verify locally. Dataset shape and manifest checks are safe; actual model loading, HF downloads, CUDA kernels, FSDP, CP, VAE encoding, reward services, and quality convergence are not verified by these helpers.
5. When a command depends on external assets, call out the asset explicitly: HF model or dataset repo id, local checkpoint, reward checkpoint, VAE cache, WIDS metadata, wandb login, or distributed rendezvous settings.

## Bundled references

- `references/data-and-configs.md`: dataset layouts, WIDS/WebDataset conversion planning, config override syntax, and preflight checks.
- `references/training-workflows.md`: command templates for image, FSDP, Sprint, video, LongSANA, SANA-WM, SANA-Streaming, checkpoints, and native test candidates.
- `references/lora-and-post-training.md`: DreamBooth LoRA, Sol-RL, Cosmos-RL boundaries, rewards, and logging.
- `references/troubleshooting.md`: data, cache, VAE/text-feature, torchrun, FSDP, OOM, HF, wandb, resume, and license failure modes.

## Source evidence labels

This sub-skill was distilled from Sana documentation, config classes, dataset loaders, train launchers, and training smoke tests. Evidence labels include `docs/sana.md`, `docs/sana_sprint.md`, `docs/sana_lora_dreambooth.md`, `docs/sana_video.md`, `docs/longsana.md`, `docs/sana_wm.md`, `docs/sana_streaming.md`, `docs/sol_rl.md`, `docs/sana_cosmos_rl.md`, `diffusion/utils/config.py`, `diffusion/data/`, `train_scripts/`, `train_video_scripts/`, `configs/`, and `tests/bash/training/`.
