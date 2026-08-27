# InternVideo2 Single-Modality Configuration

Use this reference to configure data, checkpoints, model names, launch settings, and validation checks before running or adapting a single-modality workflow.

## Runtime dependency profile

The selected repo-skill verification did not install the full training stack. Actual native runs require a user-prepared environment compatible with the branch requirements:

| Component | Expected role |
|---|---|
| Python >= 3.8 | Base runtime for the single-modality branch |
| PyTorch / torchvision CUDA build | Source requirements pin a CUDA 11.7-era PyTorch 1.13.1 / torchvision 0.14.1 combination |
| `flash_attn` | Model imports use FlashAttention, fused MLP, and fused RMSNorm components |
| `deepspeed` | Source launchers pass `--enable_deepspeed` and generate a DeepSpeed config in the output directory |
| NVIDIA Apex | Listed in requirements; often needed in the historical UMT/VideoMAE training stack |
| `decord`, OpenCV, PIL | Video and raw-frame loading |
| `timm`, `einops`, `fvcore`, `tensorboardX`, `pandas`, `numpy`, `scipy`, `scikit-image` | Model registry, transforms, FLOP/debug utilities, logging, and CSV parsing |

A plain CPU import environment is not sufficient for full training because model modules import CUDA-oriented FlashAttention APIs. Use CPU-only checks only for command construction and static validation.

## Environment variables and path contracts

| Variable / option | Used by | Contract |
|---|---|---|
| `INTERNVIDEO2_DATA_PATH` | source finetuning/probing shell recipes and bundled command helper | Parent directory containing dataset subdirectories such as `k710`, `k400`, `k600`, `k700`, `mit`, `ssv2_frame`, `ucf101`, `hmdb51`, `anet`, or `hacs`. Each finetuning/probing split root should contain `train.csv`, `val.csv`, and `test.csv`. |
| `INTERNVIDEO2_MODEL_PATH` | source finetuning/probing shell recipes; `internvl_clip_vision.py`; `videomae.py`; bundled command helper | Parent directory for checkpoint files. Teacher loaders expect `internvl/internvl_c_13b_224px.pth` and `videomae/vit_g_hybrid_1200e_pre.pth`. Finetuning/probing scripts expect model files such as `1B_pt.pth`, `1B_ft_k710_f8.pth`, or distilled S/B/L checkpoints. |
| `MASTER_PORT` | distributed launcher | Source shell recipes randomize it with a high port. Set explicitly when launching multiple jobs on the same host. |
| `OMP_NUM_THREADS` | data/CPU thread control | Source recipes set `1`; adjust only after validating CPU capacity and dataloader behavior. |
| `--output_dir` / `--log_dir` | all entry points | Destination for checkpoints, generated DeepSpeed config, rank-local prediction files, merged metrics, and `log.txt`. |
| `--prefix` | dataset loaders | Prefix prepended to relative sample paths read from CSV. For Kinetics-style recipes it usually equals `--data_path`; for pretraining it may be the video storage root while `--data_path` points to a CSV. |

Distillation caveat: the inspected teacher registry contains non-portable defaults for some teacher checkpoints. Before distillation, make teacher checkpoint lookup portable in the user's working tree or wrapper. Do not rely on hidden shared-storage paths.

## Dataset and annotation layouts

### Classification split roots

For `run_finetuning.py` and `run_linear_probing.py`, `datasets/build.py` chooses annotation files under `--data_path`:

- training: `train.csv`
- validation: `val.csv`
- final test: `test.csv`

Kinetics-style, sparse Kinetics, UCF101, MiT, ANet, and HACS loaders read CSV rows with at least:

```text
relative_or_absolute_video_path,label
```

Use `--split ','` when CSVs are comma-separated. `--prefix` is prepended to the sample path at loading time. If rows already contain absolute paths or remote URIs, verify whether a prefix should be empty.

### SSV2 and raw-frame datasets

SSV2/HMDB raw-frame recipes use `--no_use_decord` and `--filename_tmpl img_{:05}.jpg` unless overridden. CSV rows typically identify a frame directory and label. The loader constructs frame names by joining the prefix, the row path, and the filename template.

Use raw-frame mode when:

- videos are pre-extracted into frame folders;
- Decord cannot decode the source format reliably;
- a source recipe explicitly passes `--no_use_decord`.

### Pretraining and distillation CSVs

`run_pretraining.py` and `run_distill.py` use `build_multi_pretraining_dataset`, which expects a multi-source K-Mash-style CSV line format:

```text
source path total_time start_time end_time target
```

The delimiter is controlled by `--split` and defaults to a space. Source shell recipes use `train_1.1M.csv` for 1B pretraining/distillation and `train_2M.csv` for 6B pretraining. The loader uses Decord video reading only.

Field meanings:

- `source`: source tag such as a dataset name; SSV2 receives no random horizontal flip in augmentation.
- `path`: video path joined with `--prefix` when loading.
- `total_time`, `start_time`, `end_time`: set all to `-1` if no temporal segment crop is needed; otherwise they define a subclip in seconds.
- `target`: numeric class or placeholder target used by the training pipeline.

## Model and checkpoint selection

### Model registry names

| Family | Registry names | Typical use |
|---|---|---|
| Stage1 pretraining students | `pretrain_internvideo2_1B_patch14_224`, `pretrain_internvideo2_6B_patch14_224` | `run_pretraining.py` |
| Full-tuning classifiers | `internvideo2_small_patch14_224`, `internvideo2_base_patch14_224`, `internvideo2_large_patch14_224`, `internvideo2_1B_patch14_224`, `internvideo2_6B_patch14_224` | Kinetics/MiT/ANet/HACS/UCF/HMDB classification |
| SSV2 linear-probe variants | `internvideo2_cat_small_patch14_224`, `internvideo2_cat_base_patch14_224`, `internvideo2_cat_large_patch14_224`, `internvideo2_cat_1B_patch14_224`, `internvideo2_cat_6B_patch14_224` | SSV2 linear-probing recipes that merge temporal features |
| Attentive-probe variants | `internvideo2_ap_small_patch14_224`, `internvideo2_ap_base_patch14_224`, `internvideo2_ap_large_patch14_224`, `internvideo2_ap_1B_patch14_224`, `internvideo2_ap_6B_patch14_224` | SSV2 attentive probing and AP-style heads |
| Distillation students | `distill_internvideo2_small_patch14_224`, `distill_internvideo2_base_patch14_224`, `distill_internvideo2_large_patch14_224` | `run_distill.py` |
| Distillation teachers | `teacher_internvideo2_1B`, `teacher_internvideo2_stage2_1B`, `teacher_internvideo2_6B` | teacher model loaded by `run_distill.py` |
| Pretraining teachers | `internvl_clip_6b`, `mae_g14_hybrid` | teacher models loaded by `run_pretraining.py` |

### Model-zoo operating choices

| Goal | Prefer | Checkpoint expectation |
|---|---|---|
| Maximum single-modality accuracy with source recipes | 1B or 6B full tuning | large multi-GPU resources and stage checkpoints; 6B rows often have TBD public weights |
| Smaller deployable/backbone model | distilled S14/B14/L14 | distilled stage1 checkpoints, then dataset-specific finetunes |
| K400/K600/K700 finetune after K710 | 1B/6B or distilled S/B/L with K710 checkpoint | K710 head may be sliced/remapped for K400/K600/K700 in `run_finetuning.py` |
| SSV2 action classification | source SSV2 recipes | raw-frame dataset layout and `--no_use_decord`; some variants use `cat` or `ap` model families |
| Lightweight feature evaluation | linear probing | pretrained checkpoint, frozen backbone, optionally `--open_block_num` or `--open_clip_projector` |
| Teacher-student compression | distillation S/B/L | Stage2-1B teacher checkpoint and portable teacher path mapping |

### Checkpoint loading behavior

- `--finetune` loads an external checkpoint before training or eval. The code searches `model|module` by default and strips `backbone.` or `encoder.` prefixes.
- If a loaded head has 710 classes and the requested target has 400 classes, the first 400 rows are used. For 600 or 700 classes, bundled K710-to-K600/K700 label-map JSON files are used by the source code.
- `--delete_head` removes checkpoint classifier head weights and lets the new head initialize from scratch.
- Temporal and spatial position embeddings are interpolated when `num_frames`, `num_segments`, `tubelet_size`, or input size differ. `run_linear_probing.py` exposes `--orig_t_size`; `run_finetuning.py` assumes `orig_t_size=8` for the common checkpoint path.
- `--resume` and auto-resume load experiment checkpoints from `--output_dir`; DeepSpeed mode uses helper-specific latest/best checkpoint loading.

## Launch and optimization settings

| Setting | Source default pattern | Adaptation guidance |
|---|---|---|
| `--enable_deepspeed --bf16 --zero_stage 1` | nearly all large source recipes | Keep for production multi-GPU if DeepSpeed is installed. Remove for plain DDP/single-process debug. |
| `--use_checkpoint --checkpoint_num N` | 1B/6B pretraining/finetuning | Reduces memory by checkpointing early transformer blocks. Increase only after understanding the model depth. |
| `--batch_size` | per-process micro-batch | Lower first for OOM. Effective LR is scaled by world size and repeated samples. |
| `--num_frames`, `--num_segments`, `--sampling_rate` | controls temporal coverage | Model-zoo `#Frame` equals input frames × crops × clips. Verify temporal interpolation when changing frames. |
| `--test_num_segment`, `--test_num_crop` | final multi-view eval | More segments/crops improve coverage and cost more memory/time. |
| `--dist_eval` | distributed eval | Remove for single-process debugging. |
| `--save_ckpt_freq`, `--test_best` | checkpoint/eval lifecycle | Source pretraining uses high save frequency plus `checkpoint-latest`; finetuning evaluates best checkpoint automatically. |

## Pre-run validation checklist

1. `python -V` and CUDA/PyTorch versions match the FlashAttention/DeepSpeed build.
2. The expected Python entry point exists in the user's working project.
3. `INTERNVIDEO2_DATA_PATH` and `INTERNVIDEO2_MODEL_PATH` are set or replaced with explicit paths in the rendered command.
4. Finetuning/probing split root has `train.csv`, `val.csv`, and `test.csv` with the delimiter passed by `--split`.
5. Pretraining/distillation CSV has six fields per row if using `build_multi_pretraining_dataset`.
6. Teacher checkpoints exist before pretraining/distillation.
7. `--nb_classes` matches the selected dataset.
8. `GPUS`, `GPUS_PER_NODE`, `batch_size`, and DeepSpeed flags match available resources.
9. `--output_dir` is unique per experiment to avoid accidental auto-resume from a stale checkpoint.
10. The command has been reviewed as text before submission.
