# InternVideo-Next pretraining workflows

InternVideo-Next is the repo generation for visual foundation models trained without video-text supervision. The inspected code exposes stage1 and stage2 pretraining entry points, model architecture files, diffusion/JEPA components, dataset loaders, and a small model zoo.

## Model zoo and variant names

The model zoo lists released stage2 checkpoints for:

- `InternVideo-Next_s2-Large`: `revliter/internvideo_next_large_p14_res224_f16`.
- `InternVideo-Next_s2-Base`: `revliter/internvideo_next_base_p14_res224_f16`.

Timm-registered model factories in the code include:

| Family | Factory names | Notes |
|---|---|---|
| Generic backbone | `internvideo_next_base_patch14_224`, `internvideo_next_large_patch14_224` | Core 3D ViT-style backbone with cross-attention pooling/projection. |
| Stage1 | `internvideo_next_stage1_base`, `internvideo_next_stage1_large`, `internvideo_next_stage1_1b` | Adds recovery/diffusion loss components for stage1 pretraining. |
| Stage2 | `internvideo_next_stage2_base`, `internvideo_next_stage2_large`, `internvideo_next_stage2_1b` | Used with target-encoder self-distillation / JEPA-style masking. |
| Teacher | `teacher_siglip2_1b_once4all_mm_umt_res256`, `teacher_siglip2_1b_once4all_mm_umt_res384` | SigLIP2 teacher tower options used by stage workflows. |

## Architecture boundaries

- Core files define 3D patch embedding over `(C, T, H, W)`, 3D sin-cos positional embeddings, cross-attention, attentive pooling, LayerScale, ViT blocks, and projector heads.
- Attention can use a FlashAttention wrapper around `flash_attn_varlen_qkvpacked_func`; FusedMLP and DropoutAddRMSNorm are imported from FlashAttention packages.
- Stage1 model code imports `DiffLoss`, uses diffusion reconstruction/recovery losses, and returns CLIP-aligned middle/final features plus reconstruction loss.
- Stage2 model code keeps the same visual backbone shape but adds self-distillation pathways, a target encoder, and mask-token reconstruction behavior.
- Diffusion utilities are adapted from OpenAI/DiT-style Gaussian diffusion: named beta schedules (`linear`, `cosine`), spaced timesteps, MSE/KL variants, and a `DiffLoss` MLP with adaptive layer-norm conditioning.
- JEPA masking uses two mask collators with different spatial block scales and max context size; stage2 samples two masks and aligns student outputs to a frozen/momentum target encoder.

## Stage1 pretraining

Stage1 entry point: `main_stage1.py`.

Command shape:

```bash
torchrun --nproc_per_node=<gpus-per-node> --nnodes=<nodes> --node_rank=<rank> \
  --master_addr=<master-addr> --master_port=<master-port> \
  main_stage1.py \
  --model internvideo_next_stage1_large \
  --data_path <pretraining-list.txt> \
  --prefix <media-root-or-prefix> \
  --split ' ' \
  --num_frames 16 \
  --sampling_rate 4 \
  --clip_teacher teacher_siglip2_1b_once4all_mm_umt_res256 \
  --clip_input_resolution 256 \
  --clip_return_attn \
  --mask_type attention \
  --mask_ratio 0.8 \
  --clip_loss_ratio 1 1 1 \
  --output_dir <checkpoint-dir> \
  --log_dir <tensorboard-dir> \
  --bf16 \
  --enable_deepspeed
```

Important stage1 behavior:

- The entry point builds `build_multi_pretraining_dataset(args)` by default, not the single pretraining dataset path.
- It creates the selected student model, then creates a CLIP/SigLIP teacher from `--clip_teacher`.
- If `--mask_type attention`, the teacher attention map is used to choose visible/masked patches. Other choices are `tube` and `random`.
- Loss combines middle-feature alignment, final-feature alignment, and diffusion loss according to `--clip_loss_ratio`.
- `--diffusion_loss_only`, `--umt_loss_only`, and `--wo_middle_loss` are switches for ablations/debugging; do not use them in production unless the user asks for those ablations.
- With DeepSpeed enabled, the code asserts DeepSpeed gradient accumulation equals `--update_freq`.

## Stage2 pretraining

Stage2 entry point: `main_stage2.py`.

Command shape:

```bash
torchrun --nproc_per_node=<gpus-per-node> --nnodes=<nodes> --node_rank=<rank> \
  --master_addr=<master-addr> --master_port=<master-port> \
  main_stage2.py \
  --model internvideo_next_stage2_large \
  --stage1_checkpoint <stage1-checkpoint.pth> \
  --data_path <pretraining-list.txt> \
  --prefix <media-root-or-prefix> \
  --split ' ' \
  --num_frames 16 \
  --sampling_rate 4 \
  --mask_type attention \
  --mask_ratio 0.8 \
  --momentum 0.998 \
  --clip_loss_ratio 1 1 1 \
  --output_dir <checkpoint-dir> \
  --log_dir <tensorboard-dir> \
  --bf16 \
  --enable_deepspeed
```

Important stage2 behavior:

- `--stage1_checkpoint` is optional syntactically but required for the intended stage1-to-stage2 recipe.
- The loader expects the checkpoint to contain a `module` state dict. If a checkpoint was saved without that wrapper, remap it before loading.
- A `target_encoder` is created by deep-copying the student and setting all target parameters `requires_grad=False`.
- Stage2 training samples JEPA-style masks and updates the target encoder by momentum: target parameters become `momentum * target + (1 - momentum) * student`.
- The stage2 engine aligns student masked outputs to normalized target features; it no longer creates an external CLIP teacher in the same way stage1 does.

## Data-list formats

The entry points pass `--data_path` to pretraining dataset loaders. Use the `datasets` sub-skill for validation, but preserve these expectations:

| Loader | Line format | When used |
|---|---|---|
| VideoMAE single video list | `<video-path> <label>` when decoding video files | Single-stream pretraining/finetuning-style loaders. |
| VideoMAE frame-folder list | `<frame-folder> <total-frame-count> <label>` when `use_decord=False` | Frame-folder mode; less relevant to current multi loader. |
| Multi pretraining list | `<source> <video-path> <total_time> <start_time> <end_time> <label>` | Default `build_multi_pretraining_dataset` path for stage1/stage2. |

For multi pretraining lists, `source == ssv2` chooses the SSV2-specific transform without horizontal flip. `total_time`, `start_time`, and `end_time` can gate clip sampling; sentinel `-1` values skip clip-time adjustment.

## Runtime checklist

1. Verify FlashAttention, FusedMLP, and fused RMSNorm imports in the target GPU environment.
2. Verify teacher model weights/config are available for stage1.
3. Validate the data list and sample media paths with the `datasets` sub-skill.
4. Decide stage1 versus stage2 and select a matching model factory.
5. Decide DDP versus DeepSpeed; if DeepSpeed, confirm `--update_freq` and generated DeepSpeed config behavior.
6. Run only a tiny approved GPU dry run before scheduling full pretraining.
