# Training workflow command patterns

These commands are planning templates. They are not executed by the bundled helper scripts. Always adapt data paths, output directories, GPU counts, batch sizes, and checkpoint sources before running.

## Image training and fine-tuning

### Image pairs with `SanaImgDataset`

Scratch-style image training:

```bash
bash train_scripts/train.sh \
  configs/sana_config/512ms/Sana_600M_img512.yaml \
  --np=2 \
  --data.data_dir="[data/my_pairs]" \
  --data.type=SanaImgDataset \
  --model.multi_scale=false \
  --data.load_vae_feat=false \
  --work_dir=output/sana_image_pairs \
  --train.train_batch_size=32 \
  --train.num_workers=4
```

Fine-tune from a native Sana checkpoint:

```bash
bash train_scripts/train.sh \
  configs/sana_config/1024ms/Sana_1600M_img1024.yaml \
  --np=2 \
  --data.data_dir="[data/my_pairs]" \
  --data.type=SanaImgDataset \
  --model.load_from=hf://Efficient-Large-Model/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth \
  --model.multi_scale=false \
  --data.load_vae_feat=false \
  --work_dir=output/sana_image_finetune \
  --train.train_batch_size=8 \
  --train.num_workers=4
```

Notes:

- `train_scripts/train.sh` runs `torchrun` and defaults to `--resume_from=latest`, `--report_to=tensorboard`, and `--debug=true`.
- Use a unique `--work_dir` for every experiment, or remove/override resume state deliberately.
- Training loads the VAE and text encoder unless `data.load_vae_feat` or `data.load_text_feat` is true.

### Multi-scale WIDS/WebDataset

DDP-style multi-scale training:

```bash
bash train_scripts/train.sh \
  configs/sana1-5_config/1024ms/Sana_1600M_1024px_allqknorm_bf16_lr2e5.yaml \
  --np=8 \
  --data.data_dir="[data/my_wids]" \
  --data.type=SanaWebDatasetMS \
  --model.multi_scale=true \
  --data.load_vae_feat=true \
  --work_dir=output/sana_wids_ddp \
  --train.train_batch_size=2 \
  --train.num_workers=8
```

FSDP training:

```bash
bash train_scripts/train.sh \
  configs/sana1-5_config/1024ms/Sana_1600M_1024px_AdamW_fsdp.yaml \
  --np=8 \
  --data.data_dir="[data/my_wids]" \
  --data.type=SanaWebDatasetMS \
  --model.multi_scale=true \
  --data.load_vae_feat=true \
  --train.use_fsdp=true \
  --work_dir=output/sana_wids_fsdp \
  --train.train_batch_size=2 \
  --train.num_workers=8
```

Readiness checks before launch:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/my_wids --mode wids --max-samples 5
```

Confirm `wids-meta.json` exists and points to tar names that exist in the same directory, then check that sample JSON includes `prompt`, `width`, and `height`.

## Sprint sCM/LADD training

Sprint uses the `train_scm_ladd.sh` wrapper and the `SanaSprint_*_scm_ladd.yaml` config family.

```bash
bash train_scripts/train_scm_ladd.sh \
  configs/sana_sprint_config/1024ms/SanaSprint_1600M_1024px_allqknorm_bf16_scm_ladd.yaml \
  --np=8 \
  --data.data_dir="[data/my_wids]" \
  --data.type=SanaWebDatasetMS \
  --model.multi_scale=true \
  --data.load_vae_feat=true \
  --work_dir=output/sana_sprint_scm_ladd \
  --train.train_batch_size=2 \
  --train.num_workers=8
```

Planning notes:

- The public Sprint docs use toy WIDS data with precomputed VAE features.
- The wrapper also injects `--resume_from=latest`, `--report_to=tensorboard`, and `--debug=true`.
- Sprint training uses discriminator/adversarial components; checkpoint resume may include both model and discriminator checkpoint files with a suffix.
- Keep batch size conservative first. If OOM occurs, lower `--train.train_batch_size`, use fewer workers, or enable/check gradient checkpointing in config.

## SANA-Video training

### 480p WanVAE family

```bash
bash train_video_scripts/train_video_ivjoint.sh \
  configs/sana_video_config/Sana_2000M_480px_AdamW_fsdp.yaml \
  --np=8 \
  --data.data_dir='{"my_video":"data/my_video_zips"}' \
  --work_dir=output/sana_video_480p \
  --train.train_batch_size=1 \
  --train.num_workers=8 \
  --train.visualize=true
```

### 720p LTX2 VAE family

```bash
bash train_video_scripts/train_video_ivjoint.sh \
  configs/sana_video_config/Sana_2000M_720px_ltx2vae_AdamW_fsdp.yaml \
  --np=8 \
  --data.data_dir='{"my_video":"data/my_video_zips"}' \
  --work_dir=output/sana_video_720p_ltx2 \
  --train.train_batch_size=1 \
  --train.num_workers=8 \
  --train.visualize=true
```

Key 720p differences:

- VAE is `LTX2VAE_diffusers`, with 128 latent channels and 32x spatial compression.
- Model uses a patch-size-1 SANA video model because LTX2 VAE already compresses spatially.
- Aspect ratio type should keep dimensions divisible by 32, for example `ASPECT_RATIO_VIDEO_720_MS_DIV32`.
- Initialization may remove incompatible input/output keys when loading from lower-resolution checkpoints.

Planning notes:

- The video wrapper exports `DISABLE_XFORMERS=1` and `DEBUG_MODE=1`, then invokes `torchrun`.
- If you do not want image joint training, use `--train.joint_training_interval=0`.
- Video data should be zip shards with matching `.json` metadata. Validate with `--mode sana-zip-video`.
- `tests/bash/training/test_training_video.sh` is a final native candidate but requires CUDA and HF downloads.

## LongSANA training

LongSANA uses `train_video_scripts/train_longsana.py`, not the video wrapper. Public docs describe three stages:

1. ODE initialization.
2. Self-forcing training.
3. LongSANA training.

Example command shape:

```bash
torchrun --nnodes=8 --nproc_per_node=8 --rdzv_id=5235 \
  --rdzv_backend=c10d \
  --rdzv_endpoint "$MASTER_ADDR" \
  train_video_scripts/train_longsana.py \
  --config_path configs/sana_video_config/longsana/480ms/self_forcing.yaml \
  --wandb_name debug_480p_self_forcing \
  --logdir output/debug_480p_self_forcing
```

For single-node smoke planning:

```bash
torchrun --nproc_per_node=2 \
  train_video_scripts/train_longsana.py \
  --config_path configs/sana_video_config/longsana/480ms/self_forcing.yaml \
  --logdir output/debug_480p_self_forcing \
  --disable-wandb \
  --max_iters=10
```

Data notes:

- The docs mention downloading Self-Forcing prompts into `data/longsana`.
- ODE stage requires generated trajectory/data-pair paths configured in YAML.
- Multi-node commands need `MASTER_ADDR` and rendezvous settings.
- `--no-auto-resume` can disable automatic latest-checkpoint resume.

## SANA-WM Stage-1 teacher training

The public SANA-WM Stage-1 recipes use CP2/FSDP2 and the `SanaWMZipLatentDataset` loader. The public HF example dataset is large and noncommercial research only.

Bidirectional teacher:

```bash
torchrun --nproc_per_node=8 --master_port=29500 \
  train_video_scripts/train_sana_wm_stage1.py \
  --config_path configs/sana_wm/stage1/sana_wm_stage1_sekai_bidirectional_cp2_fsdp2.yaml
```

Chunk-causal teacher:

```bash
torchrun --nproc_per_node=8 --master_port=29500 \
  train_video_scripts/train_sana_wm_stage1.py \
  --config_path configs/sana_wm/stage1/sana_wm_stage1_sekai_chunk_causal_cp2_fsdp2.yaml
```

Important config distinctions:

- Bidirectional recipe: `task: ti2v`, `attn_type: BidirectionalGDNTriton`, `camctrl_type: BidirectionalGDNUCPESinglePathLiteLABothTriton`, `train.cp_size: 2`, and `train.ltx_image_condition_prob: 0.9`.
- Chunk-causal recipe: `task: df`, `attn_type: ChunkCausalGDNTriton`, `camctrl_type: ChunkCausalGDNUCPESinglePathLiteLABothTriton`, `ffn_type: ChunkGLUMBConvTemp`, `model.chunk_size: 3`, and an incremental chunk timestep mixture.
- Dataset config includes `hf_dataset_repo`, `hf_dataset_revision`, `data.hf_dataset_local_dir`, `data.data_dir`, and `data.vae_cache_dir`. Set `data.hf_dataset_local_dir` to a shared filesystem path when training on a cluster.

Local validation only checks zip/latent metadata; it does not prove camera-control semantics:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/sekai_game_train_961frames_16fps_ovl640 \
  --vae-cache-dir data/vae_cache/LTX2VAE_diffusers_704x1280/sekai_game_train_961frames_16fps_ovl640 \
  --mode wm-zip-latent
```

## SANA-WM ODE and self-forcing distillation

The WM distillation chain also uses `train_video_scripts/train_longsana.py` and has three public configs:

```bash
# T43 ODE regression; set data_path first in a copied YAML.
torchrun --nproc_per_node=8 \
  train_video_scripts/train_longsana.py \
  --config_path configs/sana_wm/distill/ode_t43.yaml \
  --disable-wandb

# T43 self-forcing warmup; CP4 / DP2 on 8 GPUs.
torchrun --nproc_per_node=8 \
  train_video_scripts/train_longsana.py \
  --config_path configs/sana_wm/distill/self_forcing_t43.yaml \
  --disable-wandb

# T121 self-forcing plus DMD; CP4 / DP2 on 8 GPUs.
torchrun --nproc_per_node=8 \
  train_video_scripts/train_longsana.py \
  --config_path configs/sana_wm/distill/self_forcing_t121.yaml \
  --disable-wandb
```

Planning notes:

- ODE config uses `trainer: wm_ode`, `data_path`, `model_path`, and `num_latent_frames: 43`.
- Self-forcing configs use `trainer: wm_self_forcing`, `SanaWMZipLatentDataset`, `train.cp_size: 4`, and public checkpoint chaining.
- T121 enables `num_cached_blocks: 2` and `sink_token: true`.
- For custom smoke tests, copy the YAML and reduce `train.max_steps`, `train.save_model_steps`, and frame counts deliberately; do not mutate release configs in place.

## SANA-Streaming V2V training

### Bidirectional short V2V

```bash
torchrun --nproc_per_node=8 --master_port=29500 \
  train_video_scripts/train_video_ivjoint_chunk.py \
  --config_path=configs/sana_streaming/train/sana_streaming_bidirectional_2b_720p.yaml
```

Data and model notes:

- Loader is `SanaV2VPairDataset`.
- Default data path is the 1k example dataset layout with `manifest.jsonl`, checksums, and zipped pair members.
- The model loads the released bidirectional V2V DiT and sets `model.additional_inchannels: 128` because source latents are concatenated with noisy target latents.
- Image joint training is disabled in the recipe.

### Long V2V 441 then 969

Before launch, download the two released checkpoints locally:

```bash
hf download Efficient-Large-Model/SANA-Streaming \
  --include dit/sana_streaming_ar.pth \
  --local-dir checkpoints/sana_streaming

hf download Efficient-Large-Model/SANA-Streaming_bidirectional \
  --include dit/sana_bidirectional_short.pth \
  --local-dir checkpoints/sana_streaming_bidirectional
```

Stage 441:

```bash
DISABLE_XFORMERS=1 torchrun --nproc_per_node=8 --master_port=29500 \
  train_video_scripts/train_longsana.py \
  --config_path configs/sana_streaming/train/sana_streaming_long_441_2b_720p.yaml \
  --logdir output/sana_streaming_long_441_2b_720p \
  --disable-wandb \
  --max_iters 5000
```

Stage 969:

```bash
DISABLE_XFORMERS=1 torchrun --nproc_per_node=8 --master_port=29500 \
  train_video_scripts/train_longsana.py \
  --config_path configs/sana_streaming/train/sana_streaming_long_969_2b_720p.yaml \
  --logdir output/sana_streaming_long_969_2b_720p \
  --disable-wandb \
  --max_iters 10000
```

The 969 recipe initializes generator and fake score from the 441-stage step-5000 checkpoint; do not skip the 441 stage unless you edit the config to point at another compatible checkpoint.

## SLURM and multi-GPU readiness

Before turning a local command into a cluster job:

- Set `--nnodes`, `--nproc_per_node`, `--rdzv_backend=c10d`, and `--rdzv_endpoint` or use SLURM-provided `MASTER_ADDR`/`MASTER_PORT` consistently.
- Ensure all nodes see the same data, cache, checkpoints, and output directories.
- Set `NCCL_DEBUG=INFO` for first distributed runs.
- Keep `HF_HOME`, dataset cache, WIDS cache, VAE cache, and wandb directories on storage with enough quota.
- For CP/FSDP2 recipes, confirm GPU count is divisible by CP size and expected data-parallel size.

## Native training candidates for final verification

The repository's `tests/bash/training/*.sh` scripts are strong final candidates, but most require CUDA, HF downloads, and sometimes multi-GPU distributed execution:

- `test_training_all.sh`: broad integrated chain.
- `test_training_fsdp.sh`: Sprint and FSDP image training on toy data.
- `test_training_vae.sh`: offline and online VAE image training.
- `test_training_video.sh`: FSDP video training.
- `test_training_longsana.sh`: Streaming helper tests plus LongSANA smoke launches.
- `test_training_sana_streaming.sh`: CPU-level helper tests for streaming datasets/pipelines and config invariants.
- `test_training_sana_wm_stage1.sh`: WM Stage-1 CP/FSDP2 smoke test.
- `test_training_sana_wm_distill.sh`: WM ODE and self-forcing chain.
- `test_training_sol_rl.sh`: tiny Sol-RL real launcher paths for Sana, SD3, and FLUX.1.

The bundled validator checks are safe and tiny, but they are not substitutes for these native candidates when GPU training verification is required.
