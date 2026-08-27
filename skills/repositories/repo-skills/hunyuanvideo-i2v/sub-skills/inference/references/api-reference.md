# Inference API Reference

## Purpose

Read this when you need the verified class/function surface behind the inference CLI.

## Key Signatures

### `hyvideo.config.parse_args`

```python
parse_args(mode='eval', namespace=None)
```

- Builds the full CLI parser for inference, LoRA, parallel, and training flows.
- `mode='train'` enables the training-specific groups.

### `hyvideo.inference.HunyuanVideoSampler.predict`

```python
predict(
    prompt,
    height=192,
    width=336,
    video_length=129,
    seed=None,
    negative_prompt=None,
    infer_steps=50,
    guidance_scale=6.0,
    flow_shift=5.0,
    embedded_guidance_scale=None,
    batch_size=1,
    num_videos_per_prompt=1,
    i2v_mode=False,
    i2v_resolution='720p',
    i2v_image_path=None,
    i2v_condition_type=None,
    i2v_stability=True,
    ulysses_degree=1,
    ring_degree=1,
    **kwargs,
)
```

Important behavior:

- Requires a string prompt.
- Validates positive `height`, `width`, and `video_length`.
- Requires `video_length - 1` to be divisible by 4.
- Chooses a default negative prompt unless classifier-free guidance is disabled.
- Rebuilds the scheduler with the requested `flow_shift`.
- In I2V mode, loads the reference image, resizes/crops to the closest supported bucket, and builds semantic image latents.
- In xDiT mode, it repartitions the transformer and all-gathers the final output.

### `hyvideo.vae.load_vae`

```python
load_vae(vae_type='884-16c-hy', vae_precision=None, sample_size=None, vae_path=None, logger=None, device=None)
```

- Loads the 3D VAE from the checkpoint tree.
- Raises if `pytorch_model.pt` is missing.

### `hyvideo.modules.load_model`

```python
load_model(args, in_channels, out_channels, factor_kwargs)
```

- Instantiates `HYVideoDiffusionTransformer` using `HUNYUAN_VIDEO_CONFIG[args.model]`.

### `hyvideo.text_encoder.TextEncoder`

- Wraps the text encoder and tokenizer pair.
- In I2V mode, the inspected code uses `llm-i2v` and `clipL`.

## Config Facts

The inspected config allows these model names:

- `HYVideo-T/2`
- `HYVideo-T/2-cfgdistill`
- `HYVideo-S/2`

## Return Shapes and Fields

The sampler’s output dictionary is the public runtime contract. When you need to adapt the inference flow into another script, preserve the `samples`, `seeds`, `prompts`, and `size` fields.
