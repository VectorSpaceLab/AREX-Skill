# Training CLI Reference

This reference distills Pyramid-Flow training sources from relative repository paths only: `train/train_pyramid_flow.py`, `train/train_video_vae.py`, `scripts/train_pyramid_flow.sh`, `scripts/train_pyramid_flow_without_ar.sh`, `scripts/train_causal_video_vae.sh`, `docs/DiT.md`, `docs/VAE.md`, `trainer_misc/utils.py`, `trainer_misc/fsdp_trainer.py`, `trainer_misc/vae_ddp_trainer.py`, `trainer_misc/sp_utils.py`, and `README.md` training sections.

Live inspection imported the training entry points and helper modules, confirmed `torch.distributed` availability, and saw CUDA with 8 visible GPUs on the verification host. Full training still remains dataset/checkpoint/time gated.

## Covered launchers

| Source launcher | Training entry point | Published workflow | Command helper subcommand |
| --- | --- | --- | --- |
| `scripts/train_pyramid_flow.sh` | `train/train_pyramid_flow.py` | AR temporal-pyramid text-to-video DiT fine-tuning. | `pyramid-flow-ar` |
| `scripts/train_pyramid_flow_without_ar.sh` | `train/train_pyramid_flow.py` | Published non-AR/full-sequence text-to-image DiT fine-tuning. | `pyramid-flow-no-ar` |
| `scripts/train_causal_video_vae.sh` | `train/train_video_vae.py` | Causal Video VAE stage-1 mixed image/video training and stage-2 context-parallel video training. | `causal-video-vae` |

Use the bundled builder for command construction instead of copying the shell scripts blindly:

```bash
python PATH_TO_SKILL/sub-skills/training-workflows/scripts/build_training_commands.py --help
```

The builder prints commands only; it does not invoke `torchrun`.

## `train/train_pyramid_flow.py` DiT CLI

`get_args()` is a zero-argument parser factory that returns `argparse.Namespace`. The source parser uses `add_help=False`, so the bundled CLI reference and command builder are the practical user-facing help surface.

### Model, data, and launcher flags

| Flag | Verified default | Choices / source behavior | Training use |
| --- | --- | --- | --- |
| `--task` | `t2v` | `t2v` or `t2i` | Selects `LengthGroupedVideoTextDataset` for video or `ImageTextDataset` for image training. Published AR launcher fixes `t2v`; published non-AR launcher fixes `t2i`. |
| `--model_name` | `pyramid_flux` | `pyramid_flux`, `pyramid_mmdit` | Must match the checkpoint family and `model_path`. |
| `--model_path` | empty | Path string | Checkpoint/model directory. Source launchers use a placeholder; replace before launch. |
| `--model_variant` | `diffusion_transformer_384p` | `diffusion_transformer_768p`, `diffusion_transformer_384p`, `diffusion_transformer_image` | Video variants for `t2v`; `diffusion_transformer_image` for the published non-AR `t2i` launcher. |
| `--model_dtype` | `bf16` | `bf16`, `fp16` | Passed to the Pyramid DiT wrapper and Accelerate mixed precision. |
| `--anno_file` | empty | Path string | Training JSONL. Video DiT code currently expects precomputed VAE latents; image DiT expects `image` + `text` rows. |
| `--resolution` | `384p` | `384p`, `768p` | Controls image sizes and latent-shape assertions. 768p training should plan gradient checkpointing. |
| `--max_frames` | `16` | positive int | Video latent/frame count passed into the runner and dataset. AR docs require a multiple of `VIDEO_SYNC_GROUP`. |
| `--batch_size` | `4` | positive int | Per-device batch size. DiT code asserts it is divisible by 4 because `sample_ratios=[1, 2, 1]`. |
| `--num_workers` | `10` parser, `8` launchers | positive int | Dataloader workers. Source training launchers use `8`. |
| `--output_dir` | empty | Path string | Checkpoint/log output root. Training entry point creates it when set. |
| `--logging_dir` | `log` | Path string | Tensorboard/Accelerate log subdirectory under `output_dir`. |

### Temporal, FSDP, and parallel flags

| Flag | Verified default | Source behavior |
| --- | --- | --- |
| `--use_fsdp` | false | Published DiT launchers enable it. `build_fsdp_plugin()` maps `zero2` to `SHARD_GRAD_OP` and `zero3` to `FULL_SHARD`. |
| `--fsdp_shard_strategy` | `zero2` | `zero2` or `zero3`; shell scripts use `zero2`. |
| `--use_flash_attn` | false | Published non-AR launcher enables it. |
| `--use_temporal_causal` | true | Passed to `PyramidDiTForVideoGeneration`; source parser makes the flag true by default. |
| `--interp_condition_pos` | true | Passed to the runner; source parser makes the flag true by default. |
| `--use_temporal_pyramid` | false | Published AR launcher enables it. Controls AR temporal-pyramid training behavior in `train_one_epoch_with_fsdp`. |
| `--sync_video_input` | false | Published AR launcher enables it. Adds assertions over `sp_proc_num`, `video_sync_group`, and `max_frames`. |
| `--video_sync_group` | `8` | Docs recommend `4`, `8`, or `16`; require `NUM_FRAMES % VIDEO_SYNC_GROUP == 0` and `GPUS % VIDEO_SYNC_GROUP == 0`. |
| `--use_sequence_parallel` | false | Optional advanced path; requires initialized distributed mode and `--sp_group_size > 1`. |
| `--sp_group_size` | `1` | Sequence-parallel group size. If enabled, `sp_proc_num % sp_group_size == 0`. |
| `--sp_proc_num` | `-1` | `-1` means all processes after Accelerate startup. AR sync also requires `sp_proc_num % video_sync_group == 0`. |
| `--gradient_checkpointing` | false | Docs say to add for 768p DiT training to reduce memory pressure. |
| `--gradient_checkpointing_ratio` | `0.75` | Fraction of transformer blocks using checkpointing. |

### Optimizer, schedule, resume, and logging flags

| Flag | Verified default | Launcher value / note |
| --- | --- | --- |
| `--gradient_accumulation_steps` | `1` | AR launcher uses `2`; non-AR launcher uses `1`. |
| `--lr_scheduler` | `constant_with_warmup` | Source code implements `cosine` and `constant_with_warmup`; other names in the help string are not implemented in this file. |
| `--lr` | `5e-5` | AR launcher uses `5e-5`; non-AR launcher uses `1e-4`. |
| `--min_lr` | `1e-5` | Used by cosine schedule. |
| `--warmup_steps` | `-1` | Launchers set `1000`. |
| `--warmup_epochs` | `1` | Used when `warmup_steps <= 0`. |
| `--opt` | `adamw` | Training helpers support common `torch.optim` names through `create_optimizer`. |
| `--opt_beta1`, `--opt_beta2` | `0.9`, `0.999` | Launchers override `opt_beta2` to `0.95`. |
| `--weight_decay` | `1e-4` | Same as launchers. |
| `--clip_grad` | `None` | Launchers set `1.0`. |
| `--epochs` | `100` | Launchers set `20`. |
| `--iters_per_epoch` | `2000` | Same as launchers. |
| `--print_freq` | `20` | Launchers set `40`. |
| `--save_ckpt_freq` | `20` | Launchers set `1`. |
| `--report_to` | `tensorboard` | `wandb` requires the package to be importable. |
| `--resume` | empty | Explicit checkpoint state path for Accelerate resume. |
| `--auto_resume` | true | If no explicit resume is given, tries newest `checkpoint-*` under `output_dir`. |
| `--ema_update` | false | Enables an EMA DiT copy; `--ema_decay` default is `0.9999`. |

## `train/train_video_vae.py` Causal VAE CLI

`get_args()` is also a zero-argument parser factory. The VAE entry point uses `torchrun` + DDP, not the DiT Accelerate/FSDP path.

### Model, data, loss, and stage flags

| Flag | Verified default | Launcher value / note |
| --- | --- | --- |
| `--model_path` | empty | Required VAE model/checkpoint directory in the shell script. |
| `--model_dtype` | `bf16` | Used for autocast/loss-scaler decisions; the training wrapper itself is constructed in fp32 in source. |
| `--lpips_ckpt` | user-local source default | Must be overridden with a real VGG LPIPS checkpoint file before any VAE training launch. |
| `--pretrained_vae_weight` | empty | Stage-2 uses the stage-1 checkpoint path. |
| `--image_anno` | empty | Stage-1 image JSONL for mixed training. |
| `--video_anno` | empty | Stage-1 and stage-2 video JSONL. |
| `--use_image_video_mixed_training` | false | Stage-1 enables it. |
| `--image_mix_ratio` | `0.1` | Stage-1 uses `0.1`; stage-2 uses `0.0`. |
| `--resolution` | `256` | Docs state 256 is enough for VAE training. |
| `--max_frames` | `24` | Stage-1 launcher uses `17`; stage-2 launcher uses `33` for `context_size=2`. |
| `--batch_size` | `64` parser, `2` launcher | Per-device VAE batch size. |
| `--use_context_parallel` | false | Stage-2 enables it to distribute long video frames. |
| `--context_size` | `2` | Stage-2 requires `GPUS % CONTEXT_SIZE == 0`. The source launcher uses `NUM_FRAMES=33` for `CONTEXT_SIZE=2`, i.e. `(17 - 1) * CONTEXT_SIZE + 1`. |
| `--add_discriminator` | false | Optional GAN discriminator path; shell script does not enable the flag explicitly. |
| `--freeze_encoder` | false | Optional partial fine-tuning path. |

### VAE loss and optimization defaults

| Flag | Verified default | Launcher value / note |
| --- | --- | --- |
| `--disc_start` | `0` | Launcher sets `250000`. |
| `--kl_weight` | `1e-6` | Launcher sets `1e-12`. |
| `--pixelloss_weight` | `1.0` | Launcher sets `10.0`. |
| `--perceptual_weight` | `1.0` | Same as launcher. |
| `--disc_weight` | `0.1` | Launcher sets `0.5`. |
| `--lr` | `5e-5` | Launcher sets `1e-4`. |
| `--lr_disc` | `1e-5` | Launcher sets `1e-4`. |
| `--warmup_epochs` | `5` | Launcher sets `1`. |
| `--warmup_steps` | `-1` | If positive, overrides warmup epochs. |
| `--opt` | `adamw` | Same as launcher. |
| `--opt_betas` | `None` | Launcher passes `0.9 0.95`. |
| `--weight_decay` | `1e-4` | Launcher sets `1e-3`. |
| `--clip_grad` | `None` | Launcher sets `1.0`. |
| `--epochs` | `100` | Same as launcher. |
| `--iters_per_epoch` | `2000` | Same as launcher. |
| `--save_ckpt_freq` | `20` | Launcher sets `1`. |
| `--auto_resume` | true | Source also has `--no_auto_resume` to disable it. |
| `--pin_mem` | true | Source also has `--no_pin_mem`. |

## Distributed helper signatures

Live inspection confirmed these callable signatures and import paths:

| Helper | Signature | Workflow note |
| --- | --- | --- |
| `trainer_misc.init_distributed_mode` | `(args, init_pytorch_ddp=True)` | Reads OpenMPI or torchrun-style `RANK`, `WORLD_SIZE`, and `LOCAL_RANK`; uses NCCL when initializing DDP. DiT calls it with `init_pytorch_ddp=False` because Accelerate initializes later. |
| `trainer_misc.create_optimizer` | `(args, model, get_num_layer=None, get_layer_scale=None, filter_bias_and_bn=True, skip_list=None, **kwargs)` | Consumes `args.opt`, LR, weight decay, and beta/epsilon fields. |
| `trainer_misc.cosine_scheduler` | `(base_value, final_value, epochs, niter_per_ep, warmup_epochs=0, start_warmup_value=0, warmup_steps=-1)` | Used by VAE and optional DiT cosine schedule. |
| `trainer_misc.constant_scheduler` | `(base_value, epochs, niter_per_ep, warmup_epochs=0, start_warmup_value=1e-06, warmup_steps=-1)` | Used by DiT `constant_with_warmup`. |
| `trainer_misc.init_sequence_parallel_group` | `(args)` | Requires DDP already initialized; reads `sp_group_size` and `sp_proc_num`. |
| `trainer_misc.init_sync_input_group` | `(args)` | Groups ranks for synchronized inputs; AR DiT instead builds synchronized dataloaders around `video_sync_group`. |
| `trainer_misc.train_one_epoch_with_fsdp` | `(runner, model_ema, accelerator, model_dtype, data_loader, optimizer, lr_schedule_values, device, epoch, clip_grad=1.0, start_steps=None, args=None, print_freq=20, iters_per_epoch=2000, ema_decay=0.9999, use_temporal_pyramid=True)` | DiT training loop called after Accelerate preparation. |
| `trainer_misc.train_one_epoch` | `(model, model_dtype, data_loader, optimizer, optimizer_disc, device, epoch, loss_scaler, loss_scaler_disc, clip_grad=0, log_writer=None, lr_scheduler=None, start_steps=None, lr_schedule_values=None, lr_schedule_values_disc=None, args=None, print_freq=20, iters_per_epoch=2000)` | VAE DDP training loop. |
| `utils.initialize_context_parallel` | `(context_parallel_size)` | Top-level VAE helper used only when `--use_context_parallel` is enabled. |

## Pre-launch invariant summary

| Invariant | Applies to | Why to check early |
| --- | --- | --- |
| `GPUS >= 8` for published full training | DiT and VAE docs | Docs require at least 8 A100-class GPUs for full training. Smaller setups may import or dry-run but are not faithful full runs. |
| `BATCH_SIZE % 4 == 0` | DiT | Source asserts this before building the Pyramid DiT runner. |
| `NUM_FRAMES % VIDEO_SYNC_GROUP == 0` | AR DiT | Source asserts this when `--sync_video_input` is enabled. |
| `GPUS % VIDEO_SYNC_GROUP == 0` | AR DiT | Needed because synced video inputs group ranks evenly. |
| `sp_group_size > 1` and `sp_proc_num % sp_group_size == 0` | Optional DiT sequence parallel | `trainer_misc.sp_utils` asserts these when sequence parallel is initialized. |
| `GPUS % CONTEXT_SIZE == 0` | VAE stage-2 | Context-parallel groups must divide the process count. |
| `NUM_FRAMES = (17 - 1) * CONTEXT_SIZE + 1` | VAE stage-2 | Matches the source stage-2 launcher value `33` when `CONTEXT_SIZE=2`; docs/comment shorthand around this value is inconsistent, so prefer the executable launcher pattern. |
| real `LPIPS_CKPT` file | VAE stages | The source parser default is not portable; missing LPIPS causes loss-wrapper construction failure. |
