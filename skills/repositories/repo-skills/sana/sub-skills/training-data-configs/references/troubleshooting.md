# Training troubleshooting

Use this reference to explain likely failures and safe next checks. Prefer validation and command planning before expensive GPU launches.

## Missing or corrupt data

Symptoms:

- `FileNotFoundError` for `meta_data.json`, `wids-meta.json`, a zip member, or a VAE cache zip.
- Dataset loader retries repeatedly and eventually raises `Too many bad data`.
- Collate errors print batch indices or data info.
- Zip reads fail or samples are skipped as corrupted.

Checks:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/my_data --mode auto --max-samples 20
```

For checksummed streaming data:

```bash
cd data/sana_streaming_1k/data/example_data
sha256sum -c checksums.sha256
cd -
```

Fixes:

- For `SanaImgDataset`, add missing `<basename>.txt` captions and ensure `meta_data.json` lists basenames or existing image filenames.
- For WIDS, regenerate `wids-meta.json` after moving/changing tar shards.
- For zip video data, ensure each `.mp4` or `.npy` sample has a same-basename `.json` with `prompt`, `width`, and `height`.
- For streaming V2V, ensure manifest paths are relative and do not contain `..`.
- For WM, ensure raw zip and latent cache zip basenames match and cache entries contain `z` arrays.

## WebDataset/WIDS versus image-pair confusion

Symptoms:

- `meta path not found` while using image-pair data with `SanaWebDatasetMS`.
- `Load VAE is not supported now` or VAE feature assertions when using `SanaImgDataset` incorrectly.
- Aspect-ratio batch sampler fails because the dataset has no valid aspect-ratio index.

Decision:

- Use `SanaImgDataset` for simple image/text pairs: `--data.type=SanaImgDataset --model.multi_scale=false --data.load_vae_feat=false`.
- Use `SanaWebDatasetMS` for tar shards and WIDS metadata: `--data.type=SanaWebDatasetMS --model.multi_scale=true`.
- Use `SanaWebDatasetMS` with `--data.load_vae_feat=true` only when `.npy` latent entries match expected latent size.

## Cache paths and stale metadata

Sana data loaders use cache directories for WIDS shards, batch samplers, and video zip inventories. Stale caches can make a run appear to ignore data changes.

Common cache classes:

- WIDS shard cache under user cache paths.
- WIDS batch sampler cache keyed by data paths, sort flags, aspect-ratio count, and dataset length.
- Video `json_cache_dir`, defaulting to `output/data_cache`.
- SANA-WM `hf_dataset_local_dir`, which may make relative `data_dir` and `vae_cache_dir` resolve under a chosen dataset root.

Fixes:

- Use a new `work_dir` for a new experiment.
- Delete the specific stale WIDS/video cache after changing shards.
- Set `data.hf_dataset_local_dir` explicitly to a shared stable data location for WM.
- Do not mix old and new shard names under the same cache path without regenerating metadata.

## VAE and text feature flags

Symptoms:

- Shape assertions when `data.load_vae_feat=true`.
- Missing model downloads or high GPU memory when `data.load_vae_feat=false`.
- Text feature `.npz` not found when `data.load_text_feat=true`.

Guidance:

- `load_vae_feat=false`: trainer encodes images/videos online using the configured VAE. Slower and more VRAM, but simpler data.
- `load_vae_feat=true`: data must already contain latent arrays. For image WIDS this is `.npy`; for WM it is `.npz` with key `z` in cache zips.
- `SanaImgDataset` does not support VAE-feature loading.
- `load_text_feat=true` is specialized; avoid unless you have matching caption-feature `.npz` and attention-mask layout.
- For 720p video and WM, LTX2 VAE paths and latent channel counts differ from image DC-AE paths.

## Config override syntax errors

Symptoms:

- CLI parser rejects an override.
- List or dict values are split by the shell.
- Config silently remains at default data path.

Fixes:

- Quote bracketed list overrides: `--data.data_dir="[data/my_wids]"`.
- Prefer copied YAML for dict-valued paths like video `data.data_dir` and WM `data.data_dir`/`vae_cache_dir`.
- Remember top-level `--work_dir=...` controls where image/video/Sprint trainers save.
- LongSANA/WM distillation use `--config_path`, `--logdir`, `--disable-wandb`, `--max_iters`; do not assume all pyrallis overrides are accepted there.

## torchrun, rank, and distributed launch issues

Symptoms:

- `RANK`, `WORLD_SIZE`, or `LOCAL_RANK` missing.
- NCCL timeout or rendezvous failure.
- FSDP or CP hangs at startup.
- `Address already in use` on master port.

Fixes:

- Use the repo wrappers for image, Sprint, and standard video when possible; they call `torchrun` and set a random master port.
- For manual launches, include `torchrun --nproc_per_node=<gpus>` and a free `--master_port`.
- For multi-node, set `--nnodes`, `--rdzv_backend=c10d`, `--rdzv_endpoint=$MASTER_ADDR`, and a stable `--rdzv_id`.
- Ensure all ranks can see the same data, VAE cache, checkpoints, and output paths.
- For SANA-WM CP configs, GPU count must be compatible with `train.cp_size` and the intended DP/CP split.
- First distributed run: set `NCCL_DEBUG=INFO` and reduce `train.num_workers` to isolate data-loader hangs.

## FSDP and resume mismatch

Symptoms:

- Resume loads from incompatible checkpoint format.
- Optimizer or scheduler state fails to load.
- Shape mismatch after changing model size, VAE, or 480p/720p config.

Guidance:

- Use `--model.load_from` for model-only fine-tuning from a compatible base checkpoint.
- Use `--resume_from` only for continuing the same run shape, optimizer, scheduler, FSDP mode, and output directory.
- The wrappers default to `--resume_from=latest`; use a fresh `--work_dir` or direct training command when starting clean.
- FSDP resume may store model, optimizer, scheduler, scaler, and random states differently from non-FSDP checkpoints.
- 720p video configs may use `remove_state_dict_keys` for resolution/channel changes; do not force incompatible full-state resume.

## Out of memory

Likely causes:

- Batch size too high for image size/model size.
- Online VAE/text encoding instead of precomputed features.
- Video/WM sequence length too long.
- Validation visualization enabled.
- Too many dataloader workers causing CPU memory pressure.
- FSDP/CP not enabled for large recipes.

Mitigations:

- Lower `--train.train_batch_size` or LoRA `--train_batch_size`.
- Increase gradient accumulation instead of per-device batch size.
- Set `--train.num_workers=0` for debugging; then raise gradually.
- Disable visualization: `--train.visualize=false`, `--no_visualize`, or no validation prompts.
- Use `--data.load_vae_feat=true` only with valid precomputed features to avoid online VAE memory.
- For DreamBooth LoRA, try `--cache_latents`, `--offload`, `--use_8bit_adam`, and `--gradient_checkpointing`.
- For video/WM, reduce frames in a copied smoke-test config, not the public production config.

## HF downloads and model access

Symptoms:

- `hf://` resolution failure.
- Dataset download stalls or exceeds disk quota.
- Gated model access denied.

Fixes:

- Authenticate with `huggingface-cli login` for gated/private assets.
- Confirm free disk space before large data: SANA-WM example data is about 235 GB; refiner/text encoder assets can be tens of GB.
- Set a shared HF cache on clusters to avoid per-rank duplicate downloads.
- For offline clusters, pre-download checkpoints and pass local paths or copy YAML configs to local paths.
- Sol-RL HPSv2 requires manual reward checkpoint downloads; other rewards auto-download on first use.

## W&B login and offline logging

Symptoms:

- Training blocks waiting for wandb auth.
- W&B writes to unexpected location.
- LoRA trainer rejects `--report_to=wandb` with `--hub_token`.

Fixes:

- Use `wandb login` before wandb runs.
- Use `WANDB_MODE=offline` for cluster/debug runs.
- Use `--report_to=tensorboard` for image/video/Sprint wrapper plans.
- Use `--disable-wandb` for LongSANA/WM distillation plans when tracking is not required.
- Avoid passing HF hub tokens directly to the LoRA script when also reporting to W&B.

## SANA-WM noncommercial Sekai-derived data

The public SANA-WM Stage-1 dataset is Sekai-derived and redistributed for non-commercial research use only. Before training, publishing checkpoints, sharing derivatives, or using in a product, require the user to review the dataset card, `LICENSE`, and `NOTICE.md` from the dataset release.

Operational impact:

- Training plans must mention the noncommercial restriction when they use the public WM example dataset.
- Exact reproduction of released WM weights is not guaranteed from the public data alone because internal training mixed additional data sources.

## Sol-RL reward and quantization issues

Symptoms:

- `transformer-engine` import failure for `naive_quant` or `sol_rl` families.
- HPSv2 reward files missing.
- Run resumes unexpectedly from old `logs/nft_slurm/<name>` directory.

Fixes:

- For NVFP4 families, install Transformer Engine with the same Python interpreter used by `torchrun`.
- For first runs, prefer `diffusionnft_pickscore` to avoid TE/NVFP4 requirements.
- Download HPSv2 reward checkpoints manually under `reward_ckpts/`.
- Override `--config.save_dir`, `--config.resume_from`, `--config.run_name`, and `--config.resume=False` for clean debug runs.

## What cannot be verified by the bundled helpers

The helper scripts do not load large checkpoints, download HF assets, initialize CUDA distributed process groups, run VAE encoding, run reward models, or train models. They can validate local paths, metadata hints, command shape, and common mismatch warnings. Report that limitation clearly when handing off a training plan.
