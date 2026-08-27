# Training API reference

This reference records the callable contracts in the training path. Names and defaults below are from the supplied repository evidence; the training launcher adds its own runtime defaults on top of `model_and_diffusion_defaults()`.

## CLI-to-factory defaults

`segmentation_train.py` constructs a parser from a training-default dictionary, then calls `defaults.update(model_and_diffusion_defaults())`. The effective parser defaults are:

| option | effective default | notes |
|---|---:|---|
| `--data_name` | `BRATS` | Exact `ISIC` and `BRATS` strings select dedicated branches. |
| `--data_dir` | `../dataset/brats2020/training` | Relative path is interpreted by the process working directory. |
| `--schedule_sampler` | `uniform` | Passed to `create_named_schedule_sampler`. |
| `--lr` | `1e-4` | AdamW learning rate. |
| `--weight_decay` | `0.0` | AdamW weight decay. |
| `--lr_anneal_steps` | `0` | Zero means no step-based termination or annealing. |
| `--batch_size` | `1` | Also the DataLoader batch size and TrainLoop global-batch basis. |
| `--microbatch` | `-1` | Non-positive means use the full `batch_size`. |
| `--ema_rate` | `"0.9999"` | Comma-separated rates are accepted by `TrainLoop`. |
| `--log_interval` | `100` | Logger dump cadence in loop steps. |
| `--save_interval` | `5000` | Checkpoint cadence in loop steps. |
| `--resume_checkpoint` | `None` | CLI value is a string path when supplied. |
| `--use_fp16` | `False` | The same flag is also a model default. |
| `--fp16_scale_growth` | `1e-3` | Added to the log loss scale after successful fp16 updates. |
| `--gpu_dev` | `"0"` | Single-device selector; also the placement device in the multi-GPU branch. |
| `--multi_gpu` | `None` | A comma-separated string such as `"0,1,2"`. |
| `--out_dir` | `./results/` | Passed to `logger.configure`. |

The merged model/diffusion defaults are:

| option | default | effect |
|---|---:|---|
| `--image_size` | `64` | Factory supports automatic channel multipliers for 64, 128, 256, and 512. |
| `--num_channels` | `128` | Base UNet width. |
| `--num_res_blocks` | `2` | Residual blocks per level. |
| `--num_heads` | `4` | Attention heads. |
| `--in_ch` | `5` | Overwritten by the launcher after branch selection: 4 for ISIC/custom 2-D, 5 for BRATS/custom 3-D. |
| `--num_heads_upsample` | `-1` | Factory lets this follow `num_heads`. |
| `--num_head_channels` | `-1` | Use head count rather than fixed head width. |
| `--attention_resolutions` | `"16,8"` | Comma-separated downsampling divisors. |
| `--channel_mult` | `""` | Empty selects an image-size mapping; otherwise use comma-separated integers. |
| `--dropout` | `0.0` | UNet dropout. |
| `--class_cond` | `False` | If true, the model expects class labels; the segmentation launcher passes an empty condition dict. |
| `--use_checkpoint` | `False` | UNet gradient checkpointing. |
| `--use_scale_shift_norm` | `True` | FiLM-like residual conditioning. |
| `--resblock_updown` | `False` | Use residual blocks for up/downsampling instead of plain sampling layers. |
| `--use_fp16` | `False` | Converts the model torso and uses fp32 master parameters. |
| `--use_new_attention_order` | `False` | Attention layout switch. |
| `--dpm_solver` | `False` | Stored on the diffusion object and consulted by sampling, not by training losses. |
| `--version` | `"new"` | `new` selects `UNetModel_newpreview`; any other value selects the v1 preview branch. `"1"` is the documented legacy value. |
| `--learn_sigma` | `False` | Uses learned-range variance in the diffusion factory when true. |
| `--diffusion_steps` | `1000` | Number of beta/timestep entries. |
| `--noise_schedule` | `"linear"` | Named beta schedule. |
| `--timestep_respacing` | `""` | Empty becomes `[diffusion_steps]` in `create_gaussian_diffusion`. |
| `--use_kl` | `False` | Selects rescaled KL loss type when true. |
| `--predict_xstart` | `False` | Uses epsilon prediction unless enabled. |
| `--rescale_timesteps` | `False` | Controls timestep scaling sent to the model. |
| `--rescale_learned_sigmas` | `False` | Selects rescaled MSE when enabled (unless `use_kl` wins). |

### Boolean parsing

`add_dict_to_argparser` assigns `str2bool` to boolean defaults. Accepted case-insensitive values are `yes`, `true`, `t`, `y`, `1`, `no`, `false`, `f`, and `0`. Every boolean option requires a value, for example `--class_cond False`; `--class_cond` alone is invalid.

## Factory signatures

The segmentation path calls:

```python
create_model_and_diffusion(
    image_size,
    class_cond,
    learn_sigma,
    num_channels,
    num_res_blocks,
    channel_mult,
    in_ch,
    num_heads,
    num_head_channels,
    num_heads_upsample,
    attention_resolutions,
    dropout,
    diffusion_steps,
    noise_schedule,
    timestep_respacing,
    use_kl,
    predict_xstart,
    rescale_timesteps,
    rescale_learned_sigmas,
    use_checkpoint,
    use_scale_shift_norm,
    resblock_updown,
    use_fp16,
    use_new_attention_order,
    dpm_solver,
    version,
)
```

There are no defaults on this wrapper: pass every argument, normally by filtering `args` with `model_and_diffusion_defaults().keys()` via `args_to_dict`. It returns `(model, diffusion)`.

`create_model` has the following verified signature and defaults:

```python
create_model(
    image_size,
    num_channels,
    num_res_blocks,
    channel_mult="",
    learn_sigma=False,
    class_cond=False,
    use_checkpoint=False,
    attention_resolutions="16",
    in_ch=4,
    num_heads=1,
    num_head_channels=-1,
    num_heads_upsample=-1,
    use_scale_shift_norm=False,
    dropout=0,
    resblock_updown=False,
    use_fp16=False,
    use_new_attention_order=False,
    version="new",
)
```

When `channel_mult == ""`, the automatic mappings are 512/256 → `(1, 1, 2, 2, 4, 4)`, 128 → `(1, 1, 2, 3, 4)`, and 64 → `(1, 2, 3, 4)`. Other sizes raise `ValueError("unsupported image size: ...")`. A non-empty `channel_mult` is split on commas and converted to integers. `attention_resolutions` is split on commas and each entry is converted to `image_size // int(entry)`.

The factory creates the repository's preview UNet with `in_channels=in_ch` and hard-coded `out_channels=2`. The segmentation loss then treats the final input channel as the noisy mask and splits the two output channels when learned variance is enabled. `UNetModel_newpreview` is used for `version == "new"`; the alternative branch is `UNetModel_v1preview`.

`create_gaussian_diffusion` is keyword-only:

```python
create_gaussian_diffusion(
    *, steps=1000, learn_sigma=False, sigma_small=False,
    noise_schedule="linear", use_kl=False, predict_xstart=False,
    dpm_solver=False, rescale_timesteps=False,
    rescale_learned_sigmas=False, timestep_respacing="",
)
```

It builds the beta schedule, chooses MSE/rescaled-MSE/rescaled-KL, converts an empty respacing value to `[steps]`, and returns `SpacedDiffusion`. `dpm_solver` is merely recorded for the later sampling branch.

## Schedule sampler

```python
create_named_schedule_sampler(name, diffusion, maxt)
```

Supported names in this source are:

- `uniform`: `UniformSampler(diffusion, maxt)`, with one equal weight per `maxt` timestep.
- `loss-second-moment`: `LossSecondMomentResampler(diffusion)`, which warms up with uniform weights and then adapts from local loss history.

Anything else raises `NotImplementedError`. The launcher passes `maxt=args.diffusion_steps`, so keep sampler length and diffusion step configuration aligned. `TrainLoop` also falls back to `UniformSampler(diffusion)` only if a sampler object is omitted; the launcher normally supplies one.

## TrainLoop contract

```python
TrainLoop(
    *, model, classifier, diffusion, data, dataloader,
    batch_size, microbatch, lr, ema_rate, log_interval,
    save_interval, resume_checkpoint, use_fp16=False,
    fp16_scale_growth=1e-3, schedule_sampler=None,
    weight_decay=0.0, lr_anneal_steps=0,
)
```

The launcher supplies `classifier=None`, the dataset iterator as `data`, and the DataLoader as `dataloader`. Each DataLoader iteration must yield `(batch, cond, name)`. The loop itself reads from the DataLoader iterator; `data` is retained as an attribute but is not used by `run_loop`.

For each step, `run_step` concatenates `batch` and `cond` along the channel dimension, clears model condition kwargs, samples timesteps and importance weights, and computes segmentation losses. `forward_backward` accumulates over microbatches and uses:

```python
loss = (losses["loss"] * weights + losses["loss_cal"] * 10).mean()
```

A non-positive `microbatch` is replaced by `batch_size`. The source does not explicitly normalize gradients by the number of microbatches, so changing microbatch can change gradient scale; treat it as a VRAM control and re-check learning-rate behavior.

`lr_anneal_steps=0` runs until externally stopped. Otherwise the loop stops when `step + resume_step` reaches that value and linearly lowers the learning rate. The DataLoader is restarted on `StopIteration`.

## Distributed/device helpers

`dist_util.setup_dist(args)` sets `CUDA_VISIBLE_DEVICES=args.gpu_dev` only when `multi_gpu` is absent, chooses `nccl` when CUDA is available and `gloo` otherwise, and initializes a one-process environment with `RANK=0` and `WORLD_SIZE=1`. `dist_util.dev()` returns generic `cuda` when CUDA is available, otherwise CPU. With `multi_gpu`, the launcher first wraps the model in `torch.nn.DataParallel` using the integer IDs from the comma-separated string and places it on `cuda:gpu_dev`. The source's later `TrainLoop` CUDA path also constructs a DDP wrapper; do not assume a torchrun-style multi-process topology from this script.

## Mixed precision

`MixedPrecisionTrainer(model, use_fp16=False, fp16_scale_growth=1e-3, initial_lg_loss_scale=20.0)` keeps flattened fp32 master parameters, converts the UNet torso to fp16, scales the loss by `2 ** lg_loss_scale`, and lowers the scale on overflow. It is intended for CUDA. The launcher passes `use_fp16` to both factory and loop.

## Logging and checkpoints

`logger.configure(dir=args.out_dir)` uses the source logger defaults (`stdout,log,csv`). Expect human output plus `log.txt` and `progress.csv` under `out_dir` unless logging environment overrides are supplied. The separate top-level `Visdom(port=8850)` construction is a launcher import side effect; it is not part of the logger or the safe inspector.
