# MedSegDiff API reference

Read this when a task needs live module names, signatures, tensor contracts, or
model/diffusion factory settings. These facts were checked against the source
baseline recorded in `repo-provenance.md` and a private Python 3.11 inspection
environment; private environment details are intentionally omitted.

## Public source modules

The repository exposes a top-level `guided_diffusion` package without a formal
distribution configuration. Important modules are:

- `guided_diffusion.script_util`: model/diffusion defaults, factories, parser
  helpers, and strict boolean conversion.
- `guided_diffusion.gaussian_diffusion`: beta schedules, diffusion enums, and
  sampling/training mechanics.
- `guided_diffusion.dpm_solver`: `NoiseScheduleVP`, `model_wrapper`, and
  `DPM_Solver` used by the accelerated sampling branch.
- `guided_diffusion.isicloader`, `bratsloader`, and
  `custom_dataset_loader`: dataset classes documented in the data-preparation
  route.
- `guided_diffusion.train_util`: `TrainLoop` and checkpoint/logging helpers.
- `guided_diffusion.dist_util`: device setup, distributed setup, and state-dict
  loading.

## Factory contracts

`model_and_diffusion_defaults()` returns defaults for `create_model_and_diffusion`.
At the inspected revision, important defaults are:

```text
image_size=64, num_channels=128, num_res_blocks=2, num_heads=4,
in_ch=5, attention_resolutions="16,8", class_cond=False,
use_scale_shift_norm=True, use_fp16=False, version="new",
learn_sigma=False, diffusion_steps=1000, noise_schedule="linear",
timestep_respacing="", use_kl=False, predict_xstart=False,
rescale_timesteps=False, rescale_learned_sigmas=False, dpm_solver=False
```

The full factory signature is:

```python
create_model_and_diffusion(
    image_size, class_cond, learn_sigma, num_channels, num_res_blocks,
    channel_mult, in_ch, num_heads, num_head_channels, num_heads_upsample,
    attention_resolutions, dropout, diffusion_steps, noise_schedule,
    timestep_respacing, use_kl, predict_xstart, rescale_timesteps,
    rescale_learned_sigmas, use_checkpoint, use_scale_shift_norm,
    resblock_updown, use_fp16, use_new_attention_order, dpm_solver, version
)
```

`create_model` automatically derives channel multipliers only for image sizes
64, 128, 256, and 512 when `channel_mult=""`; unsupported sizes raise
`ValueError`. `attention_resolutions` is a comma-separated string converted by
integer division from `image_size`. The model emits two channels in the
inspected segmentation implementation, and the diffusion loss reduces the
segmentation target to the final input channel.

`create_gaussian_diffusion` accepts keyword arguments including `steps`,
`learn_sigma`, `noise_schedule`, `use_kl`, `predict_xstart`, `dpm_solver`,
`rescale_timesteps`, `rescale_learned_sigmas`, and `timestep_respacing`.
Supported named schedules are `linear` and `cosine`; an unknown name raises
`NotImplementedError`.

## Parser helpers

- `add_dict_to_argparser(parser, default_dict)` creates one `--key` argument
  per default. Boolean defaults use `str2bool`, so a boolean requires an
  explicit token.
- `args_to_dict(args, keys)` returns `{key: getattr(args, key)}`.
- `str2bool(value)` accepts `yes`, `true`, `t`, `y`, `1`, `no`, `false`, `f`,
  and `0`, case-insensitively; other values raise
  `argparse.ArgumentTypeError`.

## Device and checkpoint facts

`dist_util.dev()` chooses CUDA when available and otherwise CPU. The training
and sampling launchers then add their own CUDA assumptions. `load_state_dict`
loads through `blobfile`, so local paths and supported blobfile paths may be
accepted by the runtime. The sampler strips one `module.` prefix from
DataParallel keys before strict model loading; verify architecture, `version`,
input channels, and tensor shapes before loading an unfamiliar checkpoint.

## Inspection boundary

Do not infer full workflow success from an import or tiny factory construction.
A CPU factory smoke verifies Python/API wiring only. Actual training and
sampling need real image/volume data, a compatible checkpoint for sampling,
and a CUDA-capable runtime for the source launchers.
