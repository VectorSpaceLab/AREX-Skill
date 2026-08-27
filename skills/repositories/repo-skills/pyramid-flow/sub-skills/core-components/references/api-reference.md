# Core Components API Reference

This reference distills source evidence and live inspection facts for Pyramid-Flow's reusable model components. Source evidence came from relative repository paths only: `pyramid_dit/pyramid_dit_for_video_gen_pipeline.py`, `video_vae/causal_video_vae_wrapper.py`, `video_vae/modeling_causal_vae.py`, `diffusion_schedulers/scheduling_flow_matching.py`, `diffusion_schedulers/scheduling_cosine_ddpm.py`, `trainer_misc/__init__.py`, `trainer_misc/utils.py`, `trainer_misc/sp_utils.py`, `trainer_misc/fsdp_trainer.py`, `README.md`, `docs/VAE.md`, and `docs/DiT.md`.

## Import surface

| Package/module | Public objects to use | Notes |
| --- | --- | --- |
| `pyramid_dit` | `PyramidDiTForVideoGeneration`, `FluxSingleTransformerBlock`, `FluxTransformerBlock`, `FluxTextEncoderWithMask`, `JointTransformerBlock`, `SD3TextEncoderWithMask` | `PyramidDiTForVideoGeneration` is the high-level runtime/training wrapper. Its source-level builders load Flux and MMDiT model bodies from their implementation modules. |
| `video_vae` | `CausalVideoVAE`, `CausalVideoVAELossWrapper`, `LPIPSWithDiscriminator` | `CausalVideoVAE` is the diffusers-style VAE model. `CausalVideoVAELossWrapper` adds checkpoint/loss/reconstruction helpers for training and demos. |
| `diffusion_schedulers` | `PyramidFlowMatchEulerDiscreteScheduler`, `DDPMCosineScheduler` | Flow-matching scheduler is used by Pyramid-DiT generation/training. Cosine DDPM scheduler is a separate lightweight scheduler implementation. |
| `trainer_misc` | `init_distributed_mode`, rank/world-size helpers, sequence-parallel group helpers, `all_to_all`, `train_one_epoch_with_fsdp`, `train_one_epoch` | These helpers are shared by generation/training code; do not initialize groups unless the process was launched under a distributed runner. |

Pyramid-Flow has no package metadata file in the inspected snapshot. In a normal runtime, make the repository/package root importable via installation, current working directory, or `PYTHONPATH`; do not assume the generated skill directory contains the Pyramid-Flow source code.

## Live dependency facts

The inspection environment successfully imported `pyramid_dit`, `video_vae`, `diffusion_schedulers`, and `trainer_misc`. Observed package versions were:

| Package/import | Observed version or status | Why it matters |
| --- | --- | --- |
| `torch` | `2.9.1+cu128` | Core tensor, CUDA, distributed, and VAE/DiT runtime. Repository docs recommend the older 2.1.x line, so version drift should be considered when debugging. |
| `torchvision` | `0.24.1+cu128` | Image transforms used by inference and data code. |
| `diffusers` | `0.39.0` | Provides `ModelMixin`, config mixins, outputs, and scheduler base classes. |
| `transformers` | `4.39.3` | Text encoder stack for Flux/MMDiT variants. |
| `accelerate` | `1.14.0` | CPU offload and training accelerator integration. |
| `safetensors` | `0.8.0` | Common checkpoint dependency for Hugging Face models. |
| `tokenizers` | `0.15.2` | Text encoder dependency. |
| `tensorboardX` | `2.6.5` | Training logging helper dependency from `trainer_misc.utils`. |
| `timm` | `0.6.13` | VAE/model utility dependency; repo requirements named the 0.6.x line. |
| `einops` | `0.8.2` | Tensor rearrangement throughout model code. |
| `huggingface_hub` | `0.36.0` | Checkpoint snapshot download support used by user workflows. |
| `jsonlines` | `4.0.0` | Data-preparation dependency, included here because imports may transitively touch repo utilities. |
| `cv2` | `4.10.0` | Video/data utility dependency. |
| `PIL` | `11.3.0` | Image-to-video and VAE reconstruction helpers. |
| `imageio` | `2.37.4` | Video export/read support. |
| `sentencepiece` | `0.2.2` | Text encoder/tokenizer dependency. |
| `spacy` | not installed in the inspected environment | Listed by repository requirements; only needed by workflows that import/use it. |
| `torchmetrics` | `1.9.0` | Training metric dependency. |
| `tiktoken` | `0.13.0` | Text/tokenization support. |
| `ftfy` | `6.3.1` | Text cleanup dependency. |
| `contexttimer` | `0.3.3` | Timing utility dependency. |

## `PyramidDiTForVideoGeneration`

### Construction signature

```python
PyramidDiTForVideoGeneration(
    model_path,
    model_dtype='bf16',
    model_name='pyramid_mmdit',
    use_gradient_checkpointing=False,
    return_log=True,
    model_variant='diffusion_transformer_768p',
    timestep_shift=1.0,
    stage_range=[0, 1/3, 2/3, 1],
    sample_ratios=[1, 1, 1],
    scheduler_gamma=1/3,
    use_mixed_training=False,
    use_flash_attn=False,
    load_text_encoder=True,
    load_vae=True,
    max_temporal_length=31,
    frame_per_unit=1,
    use_temporal_causal=True,
    corrupt_ratio=1/3,
    interp_condition_pos=True,
    stages=[1, 2, 4],
    video_sync_group=8,
    gradient_checkpointing_ratio=0.6,
    **kwargs,
)
```

### Constructor behavior and invariants

| Argument/fact | Behavior |
| --- | --- |
| `model_path` | Directory that must contain the requested DiT subdirectory and usually `causal_video_vae/`. The wrapper joins `model_path` with `model_variant` for the DiT and with `causal_video_vae` for the VAE. |
| `model_name` | Must be `pyramid_flux` or `pyramid_mmdit`; any other value raises `NotImplementedError`. |
| `model_dtype` | Maps `bf16` -> `torch.bfloat16`, `fp16` -> `torch.float16`, otherwise `torch.float32`. README snippets recommend `bf16`; fp16 support is not promised for all variants. |
| `model_variant` | Typical public values include `diffusion_transformer_768p` and 384p/image variants from the downloaded checkpoint. The directory must match the selected architecture. |
| `load_text_encoder`, `load_vae` | When true, constructor loads those subcomponents immediately. Set false only for training/precomputed-feature paths that supply embeddings/latents another way. |
| `max_temporal_length`, `frame_per_unit` | `(max_temporal_length - 1) % frame_per_unit == 0` is asserted during construction. |
| `stages`, `stage_range`, `scheduler_gamma` | Passed into `PyramidFlowMatchEulerDiscreteScheduler`; default is three stages. |
| VAE latent scaling | `pyramid_flux`: image shift `-0.04`, image scale `1 / 1.8726`; `pyramid_mmdit`: image shift `0.1490`, image scale `1 / 1.8415`; video frames after the first use shift `-0.2343`, scale `1 / 3.0986`. |
| `downsample` | The wrapper uses spatial latent downsample factor `8`; generation height and width should be divisible by 8 to avoid latent/decode mismatches. |

### Generation method signatures

```python
PyramidDiTForVideoGeneration.generate(
    prompt=None,
    height=None,
    width=None,
    temp=1,
    num_inference_steps=28,
    video_num_inference_steps=28,
    guidance_scale=7.0,
    video_guidance_scale=7.0,
    min_guidance_scale=2.0,
    use_linear_guidance=False,
    alpha=0.5,
    negative_prompt='cartoon style, worst quality, low quality, blurry, absolute black, absolute white, low res, extra limbs, extra digits, misplaced objects, mutated anatomy, monochrome, horror',
    num_images_per_prompt=1,
    generator=None,
    output_type='pil',
    save_memory=True,
    cpu_offloading=False,
    inference_multigpu=False,
    callback=None,
)
```

```python
PyramidDiTForVideoGeneration.generate_i2v(
    prompt='',
    input_image=None,
    temp=1,
    num_inference_steps=28,
    guidance_scale=7.0,
    video_guidance_scale=4.0,
    min_guidance_scale=2.0,
    use_linear_guidance=False,
    alpha=0.5,
    negative_prompt='cartoon style, worst quality, low quality, blurry, absolute black, absolute white, low res, extra limbs, extra digits, misplaced objects, mutated anatomy, monochrome, horror',
    num_images_per_prompt=1,
    generator=None,
    output_type='pil',
    save_memory=True,
    cpu_offloading=False,
    inference_multigpu=False,
    callback=None,
)
```

### Generation semantics to remember

| API | Inputs | Key checks and outputs |
| --- | --- | --- |
| `generate()` | Text prompt(s), `height`, `width`, `temp`, inference-step lists or ints. | Asserts `(temp - 1) % frame_per_unit == 0`. Converts scalar step counts to per-stage lists. Appends a quality suffix to prompts. Returns PIL frames by default, or latents if `output_type='latent'`. |
| `generate_i2v()` | Text prompt(s), `input_image`, `temp`, inference-step list/int. | Uses the input PIL image's size as height/width. Asserts `temp % frame_per_unit == 0`. Encodes the input image as the initial latent. Returns PIL frames by default, or latents if requested. |
| `enable_sequential_cpu_offload()` | No arguments. | Calls Accelerate `cpu_offload()` for text encoder and DiT. Later generation forces `cpu_offloading=True` if sequential offload is enabled. |
| `decode_latent(latents, save_memory=True, inference_multigpu=False)` | Latent tensor shaped like `[B, C, T, H/8, W/8]`. | On nonzero distributed ranks with `inference_multigpu=True`, returns `None`; rank 0 decodes. Uses temporal chunking and VAE tiling-related `tile_sample_min_size`. |
| `device`, `dtype`, `do_classifier_free_guidance` properties | No arguments. | Device/dtype are taken from DiT parameters. Classifier-free guidance is active when `_guidance_scale > 0`. |

## `CausalVideoVAE`

### Construction signature

```python
CausalVideoVAE(
    encoder_in_channels=3,
    encoder_out_channels=4,
    encoder_layers_per_block=(2, 2, 2, 2),
    encoder_down_block_types=(
        'DownEncoderBlockCausal3D',
        'DownEncoderBlockCausal3D',
        'DownEncoderBlockCausal3D',
        'DownEncoderBlockCausal3D',
    ),
    encoder_block_out_channels=(128, 256, 512, 512),
    encoder_spatial_down_sample=(True, True, True, False),
    encoder_temporal_down_sample=(True, True, True, False),
    encoder_block_dropout=(0.0, 0.0, 0.0, 0.0),
    encoder_act_fn='silu',
    encoder_norm_num_groups=32,
    encoder_double_z=True,
    encoder_type='causal_vae_conv',
    decoder_in_channels=4,
    decoder_out_channels=3,
    decoder_layers_per_block=(3, 3, 3, 3),
    decoder_up_block_types=(
        'UpDecoderBlockCausal3D',
        'UpDecoderBlockCausal3D',
        'UpDecoderBlockCausal3D',
        'UpDecoderBlockCausal3D',
    ),
    decoder_block_out_channels=(128, 256, 512, 512),
    decoder_spatial_up_sample=(True, True, True, False),
    decoder_temporal_up_sample=(True, True, True, False),
    decoder_block_dropout=(0.0, 0.0, 0.0, 0.0),
    decoder_act_fn='silu',
    decoder_norm_num_groups=32,
    decoder_type='causal_vae_conv',
    sample_size=256,
    scaling_factor=0.18215,
    add_post_quant_conv=True,
    interpolate=False,
    downsample_scale=8,
)
```

### VAE method signatures

```python
CausalVideoVAE.encode(
    x,
    return_dict=True,
    is_init_image=True,
    temporal_chunk=False,
    window_size=16,
    tile_sample_min_size=256,
)
```

```python
CausalVideoVAE.decode(
    z,
    is_init_image=True,
    temporal_chunk=False,
    return_dict=True,
    window_size=2,
    tile_sample_min_size=256,
)
```

```python
CausalVideoVAE.forward(
    sample,
    sample_posterior=True,
    generator=None,
    freeze_encoder=False,
    is_init_image=True,
    temporal_chunk=False,
)
```

```python
CausalVideoVAE.enable_tiling(use_tiling=True)
CausalVideoVAE.disable_tiling()
```

### VAE tensor contract

| Operation | Input shape | Return shape/objects | Notes |
| --- | --- | --- | --- |
| `encode(x)` | `[B, 3, T, H, W]` float tensor, normally normalized to `[-1, 1]`. | `AutoencoderKLOutput(latent_dist=DiagonalGaussianDistribution)` by default. Use `.latent_dist.mode()` or `.sample()` for latents. | Spatial dimensions should be divisible by `downsample_scale=8` for reliable round-trip shape. `tile_sample_min_size` controls tiling thresholds. |
| `decode(z)` | `[B, 4, T_latent, H/8, W/8]` latent tensor for default config. | `DecoderOutput(sample=tensor)` by default. | `window_size` defaults to `2` for decode and differs from encode default. |
| `forward(sample)` | Same as encode input. | `(posterior, dec)` in normal mode. In context-parallel training, returns global posterior and local decoded chunk. | `sample_posterior=False` uses posterior mode rather than sampling. |
| `temporal_chunk=True` | Input frame count must satisfy the temporal chunk assertions in `chunk_encode`; for default downsample scale, `(num_frames - 1) % 8 == 0` is asserted. | Encodes/decodes frame windows and concatenates outputs. | Used by long-video inference/decode paths. |
| Tiling | Enabled with `enable_tiling()`. | Same output types. | Tiled encode/decode splits spatial dimensions when larger than the tile threshold. |

A live tiny CPU smoke instantiated a reduced-channel `CausalVideoVAE`, encoded a `[1, 3, 1, 16, 16]` tensor to `[1, 4, 1, 2, 2]`, and decoded back to `[1, 3, 1, 16, 16]`.

## `CausalVideoVAELossWrapper`

### Verified signatures

```python
CausalVideoVAELossWrapper(
    model_path,
    model_dtype='fp32',
    disc_start=0,
    logvar_init=0.0,
    kl_weight=1.0,
    pixelloss_weight=1.0,
    perceptual_weight=1.0,
    disc_weight=0.5,
    interpolate=True,
    add_discriminator=True,
    freeze_encoder=False,
    load_loss_module=False,
    lpips_ckpt=None,
    **kwargs,
)
```

```python
forward(x, step, identifier=['video'])
encode(x, sample=False, is_init_image=True, temporal_chunk=False, window_size=16, tile_sample_min_size=256)
decode(x, is_init_image=True, temporal_chunk=False, window_size=2, tile_sample_min_size=256)
reconstruct(x, sample=False, return_latent=False, is_init_image=True, temporal_chunk=False, window_size=16, tile_sample_min_size=256, **kwargs)
encode_latent(x, sample=False, is_init_image=True, temporal_chunk=False, window_size=16, tile_sample_min_size=256)
decode_latent(latent, is_init_image=True, temporal_chunk=False, window_size=2, tile_sample_min_size=256)
```

### Wrapper semantics

| Method/argument | Behavior |
| --- | --- |
| `model_path` | Passed to `CausalVideoVAE.from_pretrained()`. It must identify a valid VAE checkpoint directory. |
| `load_loss_module` | If false, `self.loss` is `None`; use encode/decode/reconstruct helpers but do not call training `forward()` expecting losses. |
| `lpips_ckpt` | Needed when loading LPIPS/discriminator loss for training; docs note that users may need to supply a local LPIPS checkpoint. |
| 4D image input | `encode()`, `decode()`, and `forward()` convert `[B, C, H, W]` images to one-frame video tensors. |
| `identifier` | `forward()` treats entries containing `video` as video. If not video, it reshapes image batches into one-frame video tensors. |
| `reconstruct()` | Requires batch size `1`; returns PIL images, optionally with the encoded latent. |
| `device`, `dtype` properties | Read from wrapper parameters. |

## Diffusion schedulers

### `PyramidFlowMatchEulerDiscreteScheduler`

```python
PyramidFlowMatchEulerDiscreteScheduler(
    num_train_timesteps=1000,
    shift=1.0,
    stages=3,
    stage_range=[0, 1/3, 2/3, 1],
    gamma=1/3,
)
```

```python
set_timesteps(num_inference_steps, stage_index, device=None)
step(model_output, timestep, sample, generator=None, return_dict=True)
```

| Concept | Semantics |
| --- | --- |
| Stage initialization | Constructor builds `timesteps_per_stage`, `sigmas_per_stage`, `start_sigmas`, `end_sigmas`, and `ori_start_sigmas` dictionaries keyed by stage index. For default stages, valid stage indexes are `0`, `1`, and `2`. |
| `stage_range` | Must have `stages + 1` values. It maps training timestep intervals to each pyramid stage. |
| `set_timesteps()` | Must be called before iterative inference for each stage. It selects the per-stage timestep/sigma schedule and resets `_step_index`. |
| `step()` | Rejects integer timestep indexes; pass a value from `scheduler.timesteps`. It computes `prev_sample = sample + (sigma_next - sigma) * model_output`, increments `step_index`, and returns `FlowMatchEulerDiscreteSchedulerOutput(prev_sample=...)` unless `return_dict=False`. |
| Out-of-range stage | Native behavior is a `KeyError` from the stage dictionaries. The bundled smoke script wraps this into a clearer validity message for negative-case checks. |

A live CPU smoke built a three-stage scheduler, selected stage `1`, stepped a `[2, 4, 1, 4, 4]` sample, and preserved the tensor shape.

### `DDPMCosineScheduler`

```python
DDPMCosineScheduler(scaler=1.0, s=0.008)
set_timesteps(num_inference_steps=None, timesteps=None, device=None)
step(model_output, timestep, sample, generator=None, return_dict=True)
add_noise(original_samples, noise, timesteps)
```

| Concept | Semantics |
| --- | --- |
| Timesteps | If no custom timesteps are supplied, `set_timesteps()` creates a linear tensor from `1.0` to `0.0` with `num_inference_steps + 1` points. |
| `step()` | Expects batched float timestep tensor(s), computes the previous timestep internally, samples Gaussian noise with `randn_tensor`, and returns `DDPMSchedulerOutput(prev_sample=...)` unless `return_dict=False`. |
| `add_noise()` | Applies the cosine alpha-cumprod schedule to produce noisy samples. |

A live CPU smoke stepped a `[1, 4, 2, 2]` sample and preserved shape.

## Distributed helper APIs

### Verified signatures

```python
init_distributed_mode(args, init_pytorch_ddp=True)
init_sequence_parallel_group(args)
init_sync_input_group(args)
train_one_epoch_with_fsdp(
    runner,
    model_ema,
    accelerator,
    model_dtype,
    data_loader,
    optimizer,
    lr_schedule_values,
    device,
    epoch,
    clip_grad=1.0,
    start_steps=None,
    args=None,
    print_freq=20,
    iters_per_epoch=2000,
    ema_decay=0.9999,
    use_temporal_pyramid=True,
)
```

### Helper behavior

| Helper | Behavior and safe-use notes |
| --- | --- |
| `init_distributed_mode(args, init_pytorch_ddp=True)` | Reads OpenMPI variables or `RANK`/`WORLD_SIZE`/`LOCAL_RANK`. If not present, prints `Not using distributed mode`, sets `args.distributed=False`, and returns. If distributed and `init_pytorch_ddp=True`, sets CUDA device and initializes NCCL DDP with `env://`. |
| `is_dist_avail_and_initialized()` | True only when `torch.distributed` is both available and initialized. Use before barriers/all-reduces. |
| `get_world_size()`, `get_rank()`, `is_main_process()` | Return safe single-process defaults `1`, `0`, and `True` when distributed is not initialized. |
| `setup_for_distributed(is_master)` | Overrides builtin `print` so non-master ranks are quiet unless `force=True`; only call inside launcher-controlled code. |
| `init_sequence_parallel_group(args)` | Requires DDP to be initialized. Reads `args.sp_group_size` and `args.sp_proc_num`; asserts the selected process count is divisible by group size. Creates rank groups and records globals. |
| `get_sequence_parallel_group()`, `get_sequence_parallel_world_size()`, `get_sequence_parallel_rank()`, `get_sequence_parallel_group_rank()` | Assert if sequence parallel was not initialized. Check `is_sequence_parallel_initialized()` first in reusable code. |
| `init_sync_input_group(args)` | Requires DDP initialized. Groups ranks by `args.max_frames` for input synchronization. |
| `all_to_all` | Distributed tensor exchange helper used by sequence-parallel latent logic. Requires an initialized process group. |
| `train_one_epoch_with_fsdp()` | Accelerate/FSDP DiT epoch loop; belongs to training workflows for launch details, but core agents may need its signature to understand runner/model expectations. |

## Minimal safe usage snippets

### Scheduler CPU step

```python
import torch
from diffusion_schedulers import PyramidFlowMatchEulerDiscreteScheduler

scheduler = PyramidFlowMatchEulerDiscreteScheduler(num_train_timesteps=8, stages=3)
scheduler.set_timesteps(num_inference_steps=4, stage_index=1, device='cpu')
sample = torch.zeros(2, 4, 1, 4, 4)
model_output = torch.ones_like(sample) * 0.25
out = scheduler.step(model_output, scheduler.timesteps[0], sample)
assert out.prev_sample.shape == sample.shape
```

### Tiny VAE round-trip shape check

```python
import torch
from video_vae.modeling_causal_vae import CausalVideoVAE

vae = CausalVideoVAE(
    encoder_layers_per_block=(1, 1, 1, 1),
    decoder_layers_per_block=(1, 1, 1, 1),
    encoder_block_out_channels=(8, 8, 8, 8),
    decoder_block_out_channels=(8, 8, 8, 8),
    encoder_norm_num_groups=4,
    decoder_norm_num_groups=4,
    sample_size=16,
    encoder_spatial_down_sample=(True, True, True, False),
    decoder_spatial_up_sample=(True, True, True, False),
    encoder_temporal_down_sample=(False, False, False, False),
    decoder_temporal_up_sample=(False, False, False, False),
    downsample_scale=8,
).eval()

x = torch.zeros(1, 3, 1, 16, 16)
with torch.no_grad():
    z = vae.encode(x).latent_dist.mode()
    y = vae.decode(z).sample
assert z.shape == (1, 4, 1, 2, 2)
assert y.shape == x.shape
```
