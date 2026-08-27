# Configuration Reference

The repo uses JSON-with-comments configs. They are parsed by `core.logger.parse`, which strips `//` comments line by line before `json.loads` runs.

## Config family map

| Config | Family | Primary script | Task shape | Key traits |
| --- | --- | --- | --- | --- |
| `config/sr_sr3_16_128.json` | SR3 conditional SR | `sr.py` | 16×16 → 128×128 | `which_model_G=sr3`, `conditional=true`, `in_channel=6`, LMDB data, `mode=LRHR` on validation |
| `config/sr_ddpm_16_128.json` | DDPM conditional SR | `sr.py` | 16×16 → 128×128 | `which_model_G=ddpm`, `conditional=true`, `in_channel=6`, LMDB data, `mode=LRHR` on validation |
| `config/sr_sr3_64_512.json` | SR3 conditional SR | `sr.py` | 64×64 → 512×512 | `which_model_G=sr3`, `conditional=true`, `in_channel=6`, `img` directories, `gpu_ids=[0,1]`, `norm_groups=16`, lighter blocks |
| `config/sample_sr3_128.json` | SR3 unconditional generation | `sample.py` | 128×128 face sampling | `which_model_G=sr3`, `conditional=false`, `in_channel=3`, HR-only data |
| `config/sample_ddpm_128.json` | DDPM unconditional generation | `sample.py` | 128×128 face sampling | `which_model_G=ddpm`, `conditional=false`, `in_channel=3`, HR-only data |

## Top-level fields

| Field | Meaning | Code effect |
| --- | --- | --- |
| `name` | Experiment name prefix. | `core.logger.parse` creates `experiments/<name>_<timestamp>/` and nests logs, TensorBoard, results, and checkpoints below it. |
| `phase` | Stored default phase. | The CLI `-p/--phase` value overwrites it at runtime. The scripts then choose the train or validation noise schedule from this effective phase. |
| `gpu_ids` | List of GPU ids in the config. | `core.logger.parse` exports `CUDA_VISIBLE_DEVICES` from the CLI override or this list, and marks the run distributed when more than one GPU id is active. |
| `path.log` | Log directory name. | Rewritten under the experiment root and passed to the logger helper. |
| `path.tb_logger` | TensorBoard directory name. | Rewritten under the experiment root and passed to `SummaryWriter`. |
| `path.results` | Result directory name. | Rewritten under the experiment root and used for images and validation outputs. |
| `path.checkpoint` | Checkpoint directory name. | Rewritten under the experiment root and used by `save_network`. |
| `path.resume_state` | Checkpoint stem or null. | Left untouched by the path rewriter; `load_network` appends `_gen.pth` and `_opt.pth`. |
| `datasets.train` | Training dataset config. | Used by `data.create_dataset` and `data.create_dataloader` for train runs. |
| `datasets.val` | Validation dataset config. | Used by `data.create_dataset` and `data.create_dataloader` for validation and sampling previews. |
| `model.which_model_G` | Model family selector. | `networks.define_G` imports `model/ddpm_modules/*` for `ddpm` and `model/sr3_modules/*` for `sr3`. |
| `model.finetune_norm` | Norm fine-tuning switch. | If enabled, the wrapper freezes most weights and only leaves matching `transformer` parameters trainable. |
| `model.unet.*` | UNet architecture knobs. | Build the denoiser depth, widths, attention placements, normalization groups, and dropout. |
| `model.beta_schedule.train` / `val` | Noise schedule for each phase. | Passed to `set_new_noise_schedule` before train/val use. |
| `model.diffusion.*` | Diffusion runtime shape and conditioning. | Defines image size, sample channels, and whether the denoiser concatenates a conditioning tensor. |
| `train.*` | Optimizer, iteration, logging, EMA, and checkpoint cadence. | Consumed by `sr.py`, `sample.py`, and the model wrapper. |
| `wandb.project` | W&B project name. | Used only when `-enable_wandb` is passed. |

## Dataset field meanings

| Field | Typical values in this repo | Meaning |
| --- | --- | --- |
| `datasets.*.mode` | `HR` or `LRHR` | `HR` means the dataset returns HR/SR pairs only; `LRHR` also returns LR inputs for conditional super-resolution visuals. |
| `datasets.*.datatype` | `lmdb` or `img` | `lmdb` opens the dataset root as an LMDB store; `img` expects `sr_<L>_<R>`, `hr_<R>`, and optionally `lr_<L>` directories. |
| `datasets.*.dataroot` | Example dataset roots | Root path for the selected datatype. |
| `datasets.*.l_resolution` | `16`, `64` | Low-resolution side of the pair. |
| `datasets.*.r_resolution` | `128`, `512` | High-resolution side of the pair. |
| `datasets.train.batch_size` | `4`, `12`, `2` | Train loader batch size. |
| `datasets.train.num_workers` | `8` | Train loader worker count. |
| `datasets.train.use_shuffle` | `true` | Train loader shuffle flag. |
| `datasets.*.data_len` | `-1`, `3`, `10`, `50` | Dataset length cap; `-1` means use the full dataset. |

## Model field meanings

| Field | Accepted or observed values | Meaning |
| --- | --- | --- |
| `which_model_G` | `ddpm`, `sr3` | Selects the corresponding diffusion and UNet modules. |
| `conditional` | `true`, `false` | `true` means the denoiser receives a conditioning tensor; `false` means unconditional generation. |
| `unet.in_channel` | `3` or `6` in current configs | Must match the conditioning mode: 6 for conditional SR, 3 for unconditional generation. |
| `unet.out_channel` | `3` in current configs | The denoiser predicts the sample channels, which match `diffusion.channels`. |
| `unet.inner_channel` | `64` | Base width used for every stage. |
| `unet.channel_multiplier` | Lists such as `[1, 2, 4, 8, 8]` | Per-stage width multipliers for downsampling and upsampling. |
| `unet.attn_res` | `[16]` or `[]` | Resolutions at which attention blocks are inserted. |
| `unet.res_blocks` | `1` or `2` | Number of residual blocks per resolution stage. |
| `unet.dropout` | `0`, `0.2` | Dropout inside residual blocks. |
| `unet.norm_groups` | `16` or omitted | GroupNorm group count. Omitted values default to `32` in `networks.define_G`. |
| `beta_schedule.*.schedule` | `linear` in current configs | Schedule name accepted by `make_beta_schedule`: `quad`, `linear`, `warmup10`, `warmup50`, `const`, `jsd`, `cosine`. |
| `beta_schedule.*.n_timestep` | `2000` | Number of diffusion steps for the schedule. |
| `beta_schedule.*.linear_start` / `linear_end` | `1e-4 → 2e-2` for DDPM; `1e-6 → 1e-2` for SR3 | Start and end betas for the linear schedule. |
| `diffusion.image_size` | `128`, `512` | Square size used for sampling and model shape checks. |
| `diffusion.channels` | `3` | Number of image channels the diffusion model predicts and samples. |
| `diffusion.conditional` | `true`, `false` | Passed into `GaussianDiffusion`; governs conditional concatenation in `p_losses` and sampling. |

## Backend and runtime fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `gpu_ids` | GPU ids for the run. | `-gpu` on the CLI overrides the config. The runtime sets `CUDA_VISIBLE_DEVICES` from the effective ids. |
| `path.resume_state` | Checkpoint stem to resume from. | Do not add `_gen.pth` or `_opt.pth`; the loader appends those suffixes. |
| `wandb.project` | W&B project namespace. | The JSON field is inert until `-enable_wandb` is present. |
| `log_wandb_ckpt` / `log_eval` / `log_infer` | CLI-only W&B toggles. | These are not stored in the JSON file, but `core.logger.parse` copies them into the runtime options when present. |

## Safe edit recipes

### Switch SR3 ↔ DDPM

Change `model.which_model_G` and keep the rest of the config aligned with the chosen family. If you change families, reload a matching checkpoint rather than reusing an unrelated one.

### Switch conditional ↔ unconditional

Change `model.diffusion.conditional` together with `model.unet.in_channel`:

- `conditional=true` → `in_channel=6`
- `conditional=false` → `in_channel=3`

Keep `model.diffusion.channels=3` unless you have a code change that alters the sample channel count.

### Resume from a checkpoint

Set `path.resume_state` to the checkpoint stem, for example `.../checkpoint/I640000_E37`. The loader appends `_gen.pth` and `_opt.pth` automatically.

### Move to another resolution

Update `datasets.*.l_resolution`, `datasets.*.r_resolution`, and `model.diffusion.image_size` together. If the image-size change also changes channel layout or memory pressure, revisit `unet.channel_multiplier`, `unet.attn_res`, `unet.res_blocks`, `batch_size`, and `norm_groups`.

### Enable multi-GPU

Use a comma-separated GPU list and confirm the resulting `CUDA_VISIBLE_DEVICES` string. Multi-GPU runs are wrapped in `nn.DataParallel` by `networks.define_G`.
