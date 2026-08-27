# Helios API reference

This page captures the live API shape that the generated skill relies on.
It is intentionally narrower than the source repository and focuses on the
objects that matter for generation, training, and backend selection.

## Diffusers-facing generation APIs

### `diffusers.AutoencoderKLWan.from_pretrained`

```python
AutoencoderKLWan.from_pretrained(pretrained_model_name_or_path, **kwargs) -> Self
```

Used to load the Helios VAE from a checkpoint subfolder.

### `diffusers.HeliosScheduler`

```python
HeliosScheduler(
    num_train_timesteps=1000,
    shift=1.0,
    stages=3,
    stage_range=[0, 0.3333333333333333, 0.6666666666666666, 1],
    gamma=0.3333333333333333,
    thresholding=False,
    prediction_type="flow_prediction",
    solver_order=2,
    predict_x0=True,
    solver_type="bh2",
    lower_order_final=True,
    disable_corrector=[],
    solver_p=None,
    use_flow_sigmas=True,
    scheduler_type="unipc",
    use_dynamic_shifting=False,
    time_shift_type="exponential",
)
```

Base-style scheduler used by the non-distilled path.

### `diffusers.HeliosDMDScheduler`

```python
HeliosDMDScheduler(
    num_train_timesteps=1000,
    shift=1.0,
    stages=3,
    stage_range=[0, 0.3333333333333333, 0.6666666666666666, 1],
    gamma=0.3333333333333333,
    prediction_type="flow_prediction",
    use_flow_sigmas=True,
    use_dynamic_shifting=False,
    time_shift_type="linear",
)
```

Distilled scheduler used by the fast inference path.

### `diffusers.HeliosPyramidPipeline.from_pretrained`

```python
HeliosPyramidPipeline.from_pretrained(pretrained_model_name_or_path, **kwargs) -> Self
```

The generated helper loads the VAE and scheduler separately and passes
`is_distilled` when needed.

### `diffusers.HeliosPyramidPipeline.__call__`

```python
HeliosPyramidPipeline.__call__(
    prompt=None,
    negative_prompt=None,
    height=384,
    width=640,
    num_frames=132,
    sigmas=None,
    guidance_scale=5.0,
    num_videos_per_prompt=1,
    generator=None,
    latents=None,
    prompt_embeds=None,
    negative_prompt_embeds=None,
    output_type="np",
    return_dict=True,
    attention_kwargs=None,
    callback_on_step_end=None,
    callback_on_step_end_tensor_inputs=["latents"],
    max_sequence_length=512,
    image=None,
    image_latents=None,
    fake_image_latents=None,
    add_noise_to_image_latents=True,
    image_noise_sigma_min=0.111,
    image_noise_sigma_max=0.135,
    video=None,
    video_latents=None,
    add_noise_to_video_latents=True,
    video_noise_sigma_min=0.111,
    video_noise_sigma_max=0.135,
    history_sizes=[16, 2, 1],
    num_latent_frames_per_chunk=9,
    keep_first_frame=True,
    is_skip_first_chunk=False,
    pyramid_num_inference_steps_list=[10, 10, 10],
    use_zero_init=True,
    zero_steps=1,
    is_amplify_first_chunk=False,
)
```

Key notes:

- `image` and `video` inputs are mutually mode-dependent.
- `history_sizes`, `num_latent_frames_per_chunk`, and the pyramid step list are
  the main long-video control knobs.
- `use_zero_init` defaults to `True` in the live diffusers API.

### Parallelism and offload methods on diffusers model mixins

The Helios models rely on these generic diffusers helpers:

```python
ModelMixin.enable_parallelism(*, config, cp_plan=None)
ModelMixin.enable_group_offload(
    onload_device,
    offload_device=torch.device("cpu"),
    offload_type="block_level",
    num_blocks_per_group=None,
    non_blocking=False,
    use_stream=False,
    record_stream=False,
    low_cpu_mem_usage=False,
    offload_to_disk_path=None,
    block_modules=None,
    exclude_kwargs=None,
)
ModelMixin.set_attention_backend(backend: str) -> None
```

These methods are what the bundled inference helper uses for context
parallelism, low-VRAM mode, and flash-attention backend selection.

## Local source pipeline APIs

The source repository keeps a richer local pipeline for training-oriented and
batch-oriented inference. Its most useful live signatures are:

### `helios.diffusers_version.pipeline_helios_diffusers.HeliosPipeline.__call__`

```python
HeliosPipeline.__call__(
    prompt=None,
    negative_prompt=None,
    height=384,
    width=640,
    num_frames=132,
    num_inference_steps=50,
    sigmas=None,
    guidance_scale=5.0,
    num_videos_per_prompt=1,
    generator=None,
    latents=None,
    prompt_embeds=None,
    negative_prompt_embeds=None,
    output_type="np",
    return_dict=True,
    attention_kwargs=None,
    callback_on_step_end=None,
    callback_on_step_end_tensor_inputs=["latents"],
    max_sequence_length=512,
    image=None,
    image_latents=None,
    fake_image_latents=None,
    add_noise_to_image_latents=True,
    image_noise_sigma_min=0.111,
    image_noise_sigma_max=0.135,
    video=None,
    video_latents=None,
    add_noise_to_video_latents=True,
    video_noise_sigma_min=0.111,
    video_noise_sigma_max=0.135,
    use_interpolate_prompt=False,
    interpolate_time_list=[7, 7, 7],
    interpolation_steps=3,
    history_sizes=[16, 2, 1],
    num_latent_frames_per_chunk=9,
    keep_first_frame=True,
    is_skip_first_chunk=False,
    is_enable_stage2=False,
    pyramid_num_stages=3,
    pyramid_num_inference_steps_list=[10, 10, 10],
    use_zero_init=True,
    zero_steps=1,
    is_amplify_first_chunk=False,
)
```

This local source path is the better reference when a task involves the repo's
batch prompts, stage-2 toggle, or interpolation options.

### `helios.diffusers_version.scheduling_helios_diffusers.HeliosScheduler.__init__`

```python
HeliosScheduler(
    num_train_timesteps=1000,
    shift=1.0,
    stages=3,
    stage_range=[0, 0.3333333333333333, 0.6666666666666666, 1],
    gamma=0.3333333333333333,
    thresholding=False,
    prediction_type="flow_prediction",
    solver_order=2,
    predict_x0=True,
    solver_type="bh2",
    lower_order_final=True,
    disable_corrector=[],
    solver_p=None,
    use_flow_sigmas=True,
    scheduler_type="unipc",
    use_dynamic_shifting=False,
    time_shift_type="linear",
)
```

### `helios.diffusers_version.transformer_helios_diffusers.HeliosTransformer3DModel.forward`

```python
HeliosTransformer3DModel.forward(
    hidden_states,
    timestep,
    encoder_hidden_states,
    indices_hidden_states=None,
    indices_latents_history_short=None,
    indices_latents_history_mid=None,
    indices_latents_history_long=None,
    latents_history_short=None,
    latents_history_mid=None,
    latents_history_long=None,
    return_dict=True,
    attention_kwargs=None,
)
```

This is the signature to keep in mind when reading the training and source
pipeline code.

## Context parallel config

```python
ContextParallelConfig(
    ring_degree=None,
    ulysses_degree=None,
    convert_to_fp32=True,
    rotate_method="allgather",
    mesh=None,
    ulysses_anything=False,
    ring_anything=False,
    ...
)
```

The concrete values depend on the launched world size and the selected backend
(`ring`, `ulysses`, `unified`, or `ulysses_anything`).
