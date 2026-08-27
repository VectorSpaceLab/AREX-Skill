# Inference Workflows

## Direct generation flow

The public direct-generation path is:

1. Build a `LightX2VPipeline` with `task`, `model_path`, and `model_cls`.
2. Call `create_generator()` either with explicit tuning arguments or with `config_json`.
3. Apply optional features before generation:
   - `enable_offload()` for CPU / module offload
   - `enable_quantize()` for quantized checkpoints or quantized text/image encoders
   - `enable_parallel()` through the config / `parallel` block
   - `enable_lightvae()` when the family supports the lightweight VAE path
4. Call `generate()` with the prompt and any family-specific inputs.
5. Save the result to `save_result_path` or request an in-memory tensor / image result when the task supports it.

## Common configuration patterns

### Minimal text-to-video

```python
from lightx2v import LightX2VPipeline

pipe = LightX2VPipeline(
    model_path="/path/to/model",
    model_cls="wan2.1",
    task="t2v",
)
pipe.create_generator(config_json="/path/to/config.json")
pipe.generate(seed=42, prompt="Your prompt", save_result_path="output.mp4")
```

### Image-conditioned or audio-conditioned runs

Keep the model family and task aligned with the supported input shape:
- `i2v` / `i2i` / `ti2t` / `ti2i` use an image input
- `s2v`, `rs2v`, `t2av`, `i2av`, `l2av`, `fl2av`, `ref2av`, and `v2av` introduce audio, pose, or video control fields
- reconstruction and SR workflows use `input_path`, `video_path`, `sr_ratio`, `strict_output_path`, or family-specific geometry options

### Offload, quantization, and parallelism

The pipeline exposes optional optimization knobs that usually need to be selected before `create_generator()`:
- offload for reduced memory use
- quantized DIT / encoder checkpoints for smaller or faster runs
- parallel configuration blocks for multi-GPU execution
- lightweight VAE / autoencoder paths where the family supports them

Use the family reference before setting these knobs, because some families accept only a subset of the generic options.

## Practical workflow order

When a user asks for a fresh direct-generation setup, answer in this order:

1. Identify the family and task.
2. Confirm the model directory layout.
3. Select the generation entry point (`LightX2VPipeline` or `python -m lightx2v.infer`).
4. Set the family-specific config fields.
5. Add optional offload / quantization / parallel flags only if they are part of the request.
6. Explain the expected output type and save path.

## Family-specific notes

- Wan and HunyuanVideo variants often rely on `config.json` in the model tree.
- Wan2.2 may split low-noise and high-noise checkpoints.
- LTX-2.5 may derive fields such as `target_video_length` from metadata when the model layout supports it.
- MiniMax-H3, WorldMirror, WorldPlay, SeedVR, and the Qwen / Z-Image family all have their own input and path constraints.
- The `set_config()` path validates model/task combinations before the runner starts, so surface mismatches early.

## Suggested response style

For future agents, a good answer from this route should name:
- the exact `model_cls`
- the exact `task`
- which input fields matter
- which optional acceleration knobs matter
- where the output is written
- any family-specific file-layout requirement that must be satisfied before the run
