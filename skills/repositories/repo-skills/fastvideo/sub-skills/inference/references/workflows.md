# Inference workflows

## Minimal Python

Use a stable model ID, select a CUDA/MPS-compatible environment, and start with
a small supported resolution and frame count. Set `save_video=True` only when
you need an encoded file; use `return_frames=False` for a metadata-only smoke.
For reproducibility set `seed`, prompt, resolution, FPS, and inference steps.

## Image-conditioned generation

Put the input under `request.inputs.image_path` and use an I2V-registered model.
Check that the image is readable and that the requested frame count/resolution
matches the family preset. For lists of prompts and media, each list must have
matching lengths; otherwise split requests explicitly.

## Config-first generation

Use this portable shape:

```yaml
generator:
  model_path: FastVideo/FastWan2.1-T2V-1.3B-Diffusers
  engine:
    num_gpus: 1
request:
  prompt: A curious raccoon in sunflowers
  sampling:
    num_frames: 81
    height: 480
    width: 832
    num_inference_steps: 3
    seed: 1024
  output:
    output_path: outputs/
    save_video: true
    return_frames: false
```

Use dotted overrides for experiments. Keep output directories writable and
expect a sanitized prompt-derived filename when the output path is a directory.

## Control/refinement

Matrix-Game and GameCraft use additional action/camera inputs; GEN3C and world
models use trajectory/pose inputs. LongCat refinement is a distinct two-stage
workflow: produce or obtain a stage-1 video, then pass refinement controls and
validate target geometry. Do not invent tensor shapes; use the selected model's
preset and input contract.

For audio/video multimodal workflows, inspect the result's audio fields and
ensure `ffmpeg`/PyAV is available if muxed media is required.
