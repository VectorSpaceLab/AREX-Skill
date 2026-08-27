# Training Workflows

Pyramid-Flow training is expensive. Treat every command as a launch plan until the bundled checks pass and all external artifacts are present. The helper scripts in this sub-skill print and validate command shapes only; they never start a long training run.

## Preflight order

1. Prepare datasets, annotations, VAE latents, and optional text features with the data-preparation sub-skill.
2. Pick the training workflow below and fill real local paths for checkpoints, annotations, LPIPS weights, and output directories.
3. Run `scripts/build_training_commands.py` for a safe command preview.
4. Run `scripts/check_training_prereqs.py` with the same arguments. Use `--validate-annotations` and `--check-referenced-paths` when you want bounded JSONL/path validation.
5. Launch the printed `torchrun` command only after every invariant and prerequisite check passes.

## Autoregressive temporal-pyramid DiT video training

Source launcher: `scripts/train_pyramid_flow.sh`.

Use this path for text-to-video DiT fine-tuning with temporal pyramid and synchronized video inputs.

Key source settings:

- Entry point: `train/train_pyramid_flow.py`.
- `torchrun --nproc_per_node GPUS`, with source default `GPUS=8`.
- `--task t2v`, `--use_fsdp`, `--use_temporal_pyramid`, `--sync_video_input`, `--load_text_encoder`.
- Source defaults: `MODEL_NAME=pyramid_flux`, `VARIANT=diffusion_transformer_384p`, `RESOLUTION=384p`, `NUM_FRAMES=16`, `VIDEO_SYNC_GROUP=8`, `BATCH_SIZE=4`, `GRAD_ACCU_STEPS=2`.
- The video loader currently expects precomputed VAE latents in the training JSONL. The AR launcher computes text features on the fly because it loads the text encoder.

Command preview:

```bash
MODEL_PATH=models/pyramid-flow-miniflux
OUTPUT_DIR=runs/pyramid-flow-ar
ANNO_FILE=annotation/video_text.jsonl

python PATH_TO_SKILL/sub-skills/training-workflows/scripts/build_training_commands.py \
  pyramid-flow-ar \
  --model-path "$MODEL_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --anno-file "$ANNO_FILE" \
  --gpus 8 \
  --num-frames 16 \
  --video-sync-group 8
```

Preflight example:

```bash
python PATH_TO_SKILL/sub-skills/training-workflows/scripts/check_training_prereqs.py \
  pyramid-flow-ar \
  --model-path "$MODEL_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --anno-file "$ANNO_FILE" \
  --gpus 8 \
  --num-frames 16 \
  --video-sync-group 8 \
  --validate-annotations
```

Before launch, verify:

- `NUM_FRAMES % VIDEO_SYNC_GROUP == 0`.
- `GPUS % VIDEO_SYNC_GROUP == 0`.
- `BATCH_SIZE % 4 == 0`.
- `ANNO_FILE` rows expose at least `text` and `latent`; include `video` for provenance and data-preparation compatibility.
- Use `--gradient-checkpointing` if adapting the workflow to 768p.

## Non-AR/full-sequence DiT image training

Source launcher: `scripts/train_pyramid_flow_without_ar.sh`.

Use this path for the published full-sequence non-AR `t2i` training recipe.

Key source settings:

- Entry point: `train/train_pyramid_flow.py`.
- `--task t2i`, `--use_fsdp`, `--use_flash_attn`, `--load_text_encoder`, `--load_vae`.
- Source defaults: `MODEL_NAME=pyramid_flux`, `VARIANT=diffusion_transformer_image`, `RESOLUTION=768p`, `NUM_FRAMES=8`, `BATCH_SIZE=4`, `GRAD_ACCU_STEPS=1`.
- The `t2i` dataset path uses `ImageTextDataset` and expects `image` + `text` JSONL rows.
- Although comments mention `t2v`, the current video dataset path asserts precomputed latent loading and does not match the published non-AR image launcher as-is. Treat non-AR video training as custom code unless the loader/command is intentionally updated.

Command preview:

```bash
MODEL_PATH=models/pyramid-flow-miniflux
OUTPUT_DIR=runs/pyramid-flow-no-ar
ANNO_FILE=annotation/image_text.jsonl

python PATH_TO_SKILL/sub-skills/training-workflows/scripts/build_training_commands.py \
  pyramid-flow-no-ar \
  --model-path "$MODEL_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --anno-file "$ANNO_FILE" \
  --gpus 8 \
  --gradient-checkpointing
```

Preflight example:

```bash
python PATH_TO_SKILL/sub-skills/training-workflows/scripts/check_training_prereqs.py \
  pyramid-flow-no-ar \
  --model-path "$MODEL_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --anno-file "$ANNO_FILE" \
  --gpus 8 \
  --gradient-checkpointing \
  --validate-annotations
```

Before launch, verify:

- `BATCH_SIZE % 4 == 0`.
- `RESOLUTION=768p` and `MODEL_VARIANT=diffusion_transformer_image` match the published image path.
- `--gradient_checkpointing` is planned for 768p memory pressure.
- Image paths in the annotation are readable by the runtime host.

## Causal Video VAE two-stage training

Source launcher: `scripts/train_causal_video_vae.sh`.

The Causal Video VAE is trained in two stages:

1. **Stage-1 mixed image/video training**: `--use_image_video_mixed_training`, `--image_mix_ratio 0.1`, `--max_frames 17`.
2. **Stage-2 context-parallel video training**: load the stage-1 checkpoint with `--pretrained_vae_weight`, enable `--use_context_parallel`, and follow the source launcher pattern `NUM_FRAMES = (17 - 1) * CONTEXT_SIZE + 1` (`33` when `CONTEXT_SIZE=2`).

Both stages require a real LPIPS VGG checkpoint. The source default is not portable; always pass `--lpips-ckpt` explicitly in the helper commands. Stage-2 also requires an already-written stage-1 checkpoint; if training from scratch, preview/check stage-1 first, then generate the stage-2 command after the checkpoint exists.

Two-stage command preview:

```bash
VAE_MODEL_PATH=models/causal-video-vae
LPIPS_CKPT=models/lpips/vgg_lpips.pth
STAGE1_CKPT=runs/causal-vae-stage1/checkpoint-99.pth
OUTPUT_DIR=runs/causal-vae
IMAGE_ANNO=annotation/image_text.jsonl
VIDEO_ANNO=annotation/video_text.jsonl

python PATH_TO_SKILL/sub-skills/training-workflows/scripts/build_training_commands.py \
  causal-video-vae \
  --stage both \
  --vae-model-path "$VAE_MODEL_PATH" \
  --lpips-ckpt "$LPIPS_CKPT" \
  --pretrained-vae-weight "$STAGE1_CKPT" \
  --output-dir "$OUTPUT_DIR" \
  --image-anno "$IMAGE_ANNO" \
  --video-anno "$VIDEO_ANNO" \
  --gpus 8 \
  --context-size 2 \
  --stage2-num-frames 33
```

Stage-specific previews:

```bash
# Stage-1 only.
python PATH_TO_SKILL/sub-skills/training-workflows/scripts/build_training_commands.py \
  causal-video-vae --stage stage1 \
  --vae-model-path "$VAE_MODEL_PATH" --lpips-ckpt "$LPIPS_CKPT" \
  --output-dir "$OUTPUT_DIR" --image-anno "$IMAGE_ANNO" --video-anno "$VIDEO_ANNO"

# Stage-2 only.
python PATH_TO_SKILL/sub-skills/training-workflows/scripts/build_training_commands.py \
  causal-video-vae --stage stage2 \
  --vae-model-path "$VAE_MODEL_PATH" --lpips-ckpt "$LPIPS_CKPT" \
  --pretrained-vae-weight "$STAGE1_CKPT" \
  --output-dir "$OUTPUT_DIR" --video-anno "$VIDEO_ANNO" \
  --context-size 2 --stage2-num-frames 33
```

Preflight example:

```bash
python PATH_TO_SKILL/sub-skills/training-workflows/scripts/check_training_prereqs.py \
  causal-video-vae \
  --stage both \
  --vae-model-path "$VAE_MODEL_PATH" \
  --lpips-ckpt "$LPIPS_CKPT" \
  --pretrained-vae-weight "$STAGE1_CKPT" \
  --output-dir "$OUTPUT_DIR" \
  --image-anno "$IMAGE_ANNO" \
  --video-anno "$VIDEO_ANNO" \
  --gpus 8 \
  --context-size 2 \
  --stage2-num-frames 33 \
  --validate-annotations
```

Before launch, verify:

- `LPIPS_CKPT` exists and is readable on every rank.
- Stage-1 `image_anno` rows expose `image`; stage-1 and stage-2 `video_anno` rows expose `video`.
- Stage-2 `pretrained_vae_weight` points to a stage-1 checkpoint file.
- `GPUS % CONTEXT_SIZE == 0`.
- `NUM_FRAMES = (17 - 1) * CONTEXT_SIZE + 1`; for `CONTEXT_SIZE=2`, use the source launcher value `33` frames.

## Distributed startup model

DiT and VAE launchers share the same outer `torchrun --nproc_per_node GPUS` pattern but initialize training differently:

- DiT calls `trainer_misc.init_distributed_mode(args, init_pytorch_ddp=False)`, then uses `Accelerator(..., fsdp_plugin=...)` when `--use_fsdp` is set.
- Optional DiT sequence parallel calls `trainer_misc.init_sequence_parallel_group(args)` and requires distributed mode to be initialized first.
- AR synchronized video input uses `video_sync_group` to split dataloader ranks; validate group divisibility before launch.
- VAE training calls `trainer_misc.init_distributed_mode(args)` with PyTorch DDP initialization, then wraps the model in `DistributedDataParallel`.
- VAE stage-2 calls top-level `utils.initialize_context_parallel(context_size)` before building datasets and model wrappers.

Use the core-components sub-skill when the task needs low-level method semantics for model wrappers, schedulers, VAE encode/decode, or distributed helper accessors.
