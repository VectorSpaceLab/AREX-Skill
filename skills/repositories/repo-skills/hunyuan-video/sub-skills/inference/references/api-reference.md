# API Reference

Read this before writing Python code around HunyuanVideo inference.

## Verified signatures

Inspection of the prepared environment verified these signatures:

```python
hyvideo.config.parse_args(namespace=None)
Inference.from_pretrained(pretrained_model_path, args, device=None, **kwargs)
HunyuanVideoSampler.predict(
    self,
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
    **kwargs,
)
hyvideo.utils.file_utils.save_videos_grid(videos: torch.Tensor, path: str, rescale=False, n_rows=1, fps=24)
```

## Loader behavior

`HunyuanVideoSampler.from_pretrained(Path(args.model_base), args=args)`:

- initializes distributed xDiT state when `args.ulysses_degree > 1` or `args.ring_degree > 1`;
- disables gradients;
- builds `HYVideoDiffusionTransformer` using `HUNYUAN_VIDEO_CONFIG`;
- optionally converts FP8 linear layers before loading state dict;
- loads the 3D VAE and text encoders from model-base-derived paths;
- enables sequential CPU offload if requested, otherwise moves the pipeline to the selected device.

## `predict()` behavior

- `prompt` must be a string; it is stripped and wrapped as a single-item list.
- `seed=None` creates random integer seeds. An integer seed expands as `seed + i` across requested videos. A seed list must match `batch_size` or `batch_size * num_videos_per_prompt`.
- `height`, `width`, and `video_length` must be positive. For the default VAE, `(video_length - 1) % 4 == 0` is enforced.
- Height and width are aligned upward to multiples of 16 before sampling.
- If `negative_prompt` is empty or `None`, the default negative prompt is used, unless `guidance_scale == 1.0`, in which case it is cleared.
- The scheduler is recreated with the supplied `flow_shift`, `args.flow_reverse`, and `args.flow_solver`.
- Return dict keys include `samples`, `seeds`, `prompts`, and `size`.

## Output saving

The canonical script saves each generated sample as an MP4 grid at 24 fps. Only rank 0 saves in distributed runs. The filename includes timestamp, seed, and the first 100 prompt characters with `/` removed.
