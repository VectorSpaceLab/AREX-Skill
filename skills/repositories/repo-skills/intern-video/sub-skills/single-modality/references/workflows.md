# InternVideo2 Single-Modality Workflows

This reference distills the visual-only InternVideo2 training scripts into reusable operating recipes. Commands assume the user is working in a project directory that contains the single-modality Python entry points (`run_pretraining.py`, `run_finetuning.py`, `run_linear_probing.py`, `run_distill.py`). The bundled command builder can render command text without executing training:

```bash
python path/to/this/sub-skill/scripts/build_single_modality_command.py --list-presets
python path/to/this/sub-skill/scripts/build_single_modality_command.py \
  --preset finetune-k400-1b-f8 \
  --data-root "${INTERNVIDEO2_DATA_PATH:?set data root}" \
  --model-root "${INTERNVIDEO2_MODEL_PATH:?set model root}" \
  --partition video \
  --gpus 32 \
  --gpus-per-node 8
```

The helper prints a reviewed launch recipe. It does not import InternVideo, allocate GPUs, or submit jobs.

## Workflow decision checklist

Before building a command, determine:

- **Task family:** pretraining, distillation, full finetuning, linear probing, attentive probing, or eval-only.
- **Model scale:** `S14`, `B14`, `L14`, `1B`, or `6B` where supported.
- **Dataset class and split layout:** Kinetics-style videos, sparse Kinetics/MiT/ANet/HACS videos, SSV2/HMDB raw frames, or K-Mash pretraining CSV.
- **Checkpoint source:** stage1 pretraining, K710 finetune, K400 finetune, distilled model, or existing experiment `checkpoint-best.pth`/`checkpoint-latest.pth`.
- **Launcher:** SLURM `srun` for repo-shaped recipes, `torchrun` for non-SLURM multi-GPU, or plain `python` only for tiny debugging after disabling distributed-only options.
- **Backend:** full workflows expect CUDA, FlashAttention, DeepSpeed, and BF16-capable hardware unless you deliberately remove those flags and reduce batch sizes.

## Pretraining

Entry point: `run_pretraining.py`.

Primary source recipes:

| Preset | Student model | Data recipe | GPUs | Key settings |
|---|---|---:|---:|---|
| `pretrain-1b` | `pretrain_internvideo2_1B_patch14_224` | K-Mash 1.1M CSV | 128 | `num_frames=16`, `num_segments=16`, `sampling_rate=1`, `mask_type=attention`, `mask_ratio=0.8`, `batch_size=32`, DeepSpeed ZeRO-1 BF16 |
| `pretrain-6b` | `pretrain_internvideo2_6B_patch14_224` | K-Mash 2M CSV | 256 | same sampling/masking, `batch_size=8`, `checkpoint_num=48`, higher `drop_path` |

Pretraining uses two teachers by default:

- CLIP-style visual teacher: `internvl_clip_6b`, loaded from the model root under `internvl/internvl_c_13b_224px.pth`.
- MAE teacher: `mae_g14_hybrid`, loaded from the model root under `videomae/vit_g_hybrid_1200e_pre.pth`.

Operational notes:

- Sparse sampling is intentional: the recipe sets `--sampling_rate 1` with `--num_segments 16`.
- The run writes a generated `deepspeed_config.json` inside `--output_dir` when `--enable_deepspeed` is set.
- The latest checkpoint is saved every epoch as `checkpoint-latest.pth`; epoch-numbered checkpoints follow `--save_ckpt_freq`.
- Learning rate is scaled in code by `batch_size * world_size * num_sample / 256`. If you change GPU count or batch size, review the effective LR printed at startup.
- Do not run pretraining until both teacher checkpoint files and the K-Mash CSV/video storage are available.

## Distillation

Entry point: `run_distill.py`.

Distillation trains smaller visual models against an InternVideo2 teacher. The branch uses settings similar to pretraining, with `MLP_Decoder` for better feature alignment.

| Preset | Intended student | Teacher | Data recipe | GPUs | Key settings |
|---|---|---|---|---:|---|
| `distill-s14-stage2` | `distill_internvideo2_small_patch14_224` | `teacher_internvideo2_stage2_1B` | K-Mash 1.1M CSV | 32 | `num_frames=8`, `num_segments=8`, `sampling_rate=1`, `clip_return_layer=6`, `clip_student_decoder=MLP_Decoder`, `batch_size=128` |
| `distill-b14-stage2` | `distill_internvideo2_base_patch14_224` | `teacher_internvideo2_stage2_1B` | K-Mash 1.1M CSV | 32 | same as S14, base student |
| `distill-l14-stage2` | `distill_internvideo2_large_patch14_224` | `teacher_internvideo2_stage2_1B` | K-Mash 1.1M CSV | 32 | same as S14, larger student, lower starting batch size |

Distillation-specific cautions:

- The teacher registry in the inspected branch is not fully environment-variable driven. Patch or wrap teacher checkpoint mapping to portable user-provided paths before launching distillation.
- The source shell files include naming inconsistencies around some distillation/model-zoo rows. Treat the Python model registry name in the reviewed command as authoritative, not the shell filename alone.
- If `clip_teacher_final_dim` is `0`, final AttnPool feature distillation is disabled; source recipes use `768`, so final feature distillation is active.

## Full finetuning and evaluation

Entry point: `run_finetuning.py`.

Typical full-tuning recipe shape:

```bash
python run_finetuning.py \
  --model internvideo2_1B_patch14_224 \
  --data_path "$INTERNVIDEO2_DATA_PATH/k400" \
  --prefix "$INTERNVIDEO2_DATA_PATH/k400" \
  --data_set Kinetics_sparse \
  --split ',' \
  --nb_classes 400 \
  --finetune "$INTERNVIDEO2_MODEL_PATH/1B_ft_k710_f8.pth" \
  --num_frames 8 \
  --sampling_rate 8 \
  --test_num_segment 4 \
  --test_num_crop 3 \
  --enable_deepspeed --bf16 --zero_stage 1 \
  --test_best
```

High-value finetuning routes:

| Target | Dataset class | Classes | Common checkpoint | Notes |
|---|---|---:|---|---|
| K710 | `Kinetics_sparse` | 710 | Stage1 pretrain (`1B_pt.pth`, `6B_pt.pth`, or distilled S/B/L equivalent) | first action-recognition adaptation from K-Mash pretraining |
| K400 | `Kinetics_sparse` | 400 | K710 finetuned checkpoint | source recipes use 8 or 16 input frames, 4 temporal clips, 3 crops |
| K600/K700 | `Kinetics_sparse` | 600/700 | K710 finetuned checkpoint | label-map remapping is applied when a 710-class head is loaded |
| MiT V1 | `mitv1_sparse` | 339 | K710+K400 checkpoint | 6B has an optional 224-to-336 recipe in source scripts |
| SSV1/SSV2 | `SSV2` | 174 | Stage1 pretrain or distilled checkpoint | source recipes use raw-frame loading via `--no_use_decord` |
| ANet/HACS | `ANet`/`HACS` | 200 | K710+K400 checkpoint | source recipes use 6B and attentive/probing-style entry point |

Evaluation behavior:

- `--test_best` triggers automatic evaluation of the best checkpoint after training.
- `--eval` runs evaluation-only and writes rank-local prediction files under `--output_dir`; rank 0 merges them for Top-1/Top-5.
- With DeepSpeed enabled, checkpoint auto-loading prefers `checkpoint-best.pth` for `--test_best --eval`, then `checkpoint-latest.pth`, then numbered checkpoints.
- `--dist_eval` is appropriate for distributed evaluation. Remove it for plain single-process debug commands.

## Linear and attentive probing

Entry point: `run_linear_probing.py`.

Linear probing loads a checkpoint and freezes most of the visual backbone. It trains the classifier head and optionally opens selected blocks/projector components:

- `--open_block_num N` unfreezes the last `N` blocks.
- `--open_clip_projector` keeps the attention-pooling projector trainable; source attentive-probing recipes use this flag.
- `--finetune_extra` merges selected keys from an extra checkpoint whose keys start with `vision_encoder.`.
- `--orig_t_size` controls temporal position-embedding interpolation when loading a checkpoint trained with a different number of frames.

Common recipes:

| Preset | Dataset | Model | Frames | GPUs | Notes |
|---|---|---|---:|---:|---|
| `linear-k400-1b-f16` | K400 / `Kinetics_sparse` | `internvideo2_1B_patch14_224` | 16 | 16 | freezes backbone, uses 1 temporal segment and 3 crops |
| `attentive-k400-1b-f16` | K400 / `Kinetics_sparse` | `internvideo2_1B_patch14_224` | 16 | 16 | adds `--open_clip_projector`, lower LR, short adaptation |
| SSV2 linear/attentive variants | SSV2 raw frames | `internvideo2_cat_*` or `internvideo2_ap_*` | 16 | 16 | use `--no_use_decord` and raw-frame prefix |
| UCF101/HMDB51 variants | UCF101/HMDB51 | `internvideo2_*` | 16 | 8 | HMDB source recipes use `--no_use_decord`; UCF uses video loading unless adapted |

Avoid stale source assumptions: some inspected shell scripts reference nonexistent or mismatched entry points/model names. Start from the command builder presets or from a reviewed command assembled from the Python entry point and registry names.

## Launcher adaptation

### SLURM `srun`

Source recipes use this shape:

```bash
export MASTER_PORT=${MASTER_PORT:-$((12000 + RANDOM % 20000))}
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1}
srun -p "$PARTITION" \
  --gres=gpu:$GPUS_PER_NODE \
  --ntasks=$GPUS \
  --ntasks-per-node=$GPUS_PER_NODE \
  --cpus-per-task=$CPUS_PER_TASK \
  --kill-on-bad-exit=1 \
  python run_finetuning.py ...
```

Review `GPUS`, `GPUS_PER_NODE`, and `batch_size` together; the training scripts scale LR by world size.

### `torchrun`

For non-SLURM clusters, use `torchrun` only after the environment provides NCCL and GPU visibility:

```bash
torchrun --nproc_per_node 8 --master_port "$MASTER_PORT" run_finetuning.py ...
```

If using multiple nodes, add `--nnodes`, `--node_rank`, `--master_addr`, and keep the command line identical after the entry point.

### Plain `python`

Use plain `python` only for help/parser dry runs, tiny local debugging, or deliberate single-GPU experiments. Remove distributed/DeepSpeed-only options unless the user has a one-process DeepSpeed setup:

- remove `--enable_deepspeed` and `--zero_stage`;
- remove `--dist_eval`;
- use small `--batch_size`, `--num_workers`, `--num_frames`, and a tiny fixture dataset;
- do not interpret success as production-readiness.
