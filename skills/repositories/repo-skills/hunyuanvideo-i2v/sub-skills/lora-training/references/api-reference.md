# LoRA Training API Reference

## Purpose

Read this when you need the inspected helper functions and dataset schema behind the LoRA training flow.

## Key Functions and Classes

### `hyvideo.dataset.video_loader.VideoDataset`

```python
VideoDataset(
    data_jsons_path: str,
    sample_n_frames: int = 129,
    sample_stride: int = 1,
    text_encoder=None,
    text_encoder_2=None,
    uncond_p=0.0,
    args=None,
    logger=None,
)
```

What it expects:

- a directory of processed latent JSON files
- each JSON must provide `video_id`, `latent_shape`, `prompt`, `npy_save_path`, `height`, and `width`
- `npy_save_path` must point to a real `.npy` latent file

### `hyvideo.ds_config.get_deepspeed_config`

```python
get_deepspeed_config(args, micro_batch_size, global_batch_size, output_dir=None, job_name=None)
```

- Builds the DeepSpeed JSON-like config used by the launcher.
- Supports tensorboard wiring when `args.tensorboard` is set.

### `hyvideo.utils.train_utils.prepare_model_inputs`

```python
prepare_model_inputs(
    args,
    batch,
    device,
    model,
    vae,
    text_encoder,
    text_encoder_2=None,
    rope_theta_rescale_factor=1.0,
    rope_interpolation_factor=1.0,
)
```

- Accepts a batch from the video dataset.
- Encodes media when the batch does not already contain cached latents.
- Builds the RoPE tensors and model kwargs for the training step.

### `hyvideo.utils.train_utils.load_lora`

```python
load_lora(model, lora_path, device)
```

- Loads a Kohya-format LoRA file into the model.
- The launcher uses it when resuming or stacking an existing LoRA.

## Important Training Behavior

- The base transformer and text encoders are loaded before the first iteration.
- `use_lora` freezes the base model parameters and wraps the target modules with PEFT.
- The code assumes the dataset points at processed latent arrays, not raw video files.
