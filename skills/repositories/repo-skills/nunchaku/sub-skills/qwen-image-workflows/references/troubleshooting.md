# Qwen workflow troubleshooting

## `AssertionError: Only safetensors are supported`

`NunchakuQwenImageTransformer2DModel.from_pretrained(...)` accepts a local checkpoint file or a Hugging Face file path whose final name ends in `.safetensors` or `.sft`. Do not pass a repository/directory such as only `nunchaku-tech/nunchaku-qwen-image`.

Use a full file path pattern instead:

```python
f"nunchaku-tech/nunchaku-qwen-image/svdq-{precision}_r{rank}-qwen-image.safetensors"
```

For local checkpoints, verify the path is a file before calling `from_pretrained`.

## 2509 or ControlNet classes cannot be imported

Symptoms include missing `QwenImageEditPlusPipeline`, `QwenImageControlNetModel`, or `QwenImageControlNetPipeline` from Diffusers.

- Use `diffusers>=0.36` for Qwen-Image-Edit-2509 and Qwen ControlNet routing.
- If a workflow was copied from an example that says to install Diffusers from a development source, first check whether the released installed version now provides the required class.
- Keep the base model and pipeline matched: `Qwen/Qwen-Image-Edit-2509` should use `QwenImageEditPlusPipeline`, not the older edit pipeline.

## Offload is slow, still OOMs, or warns about `.to("cuda")`

Nunchaku Qwen transformer offload is separate from Diffusers offload.

Recommended low-VRAM sequence:

```python
transformer.set_offload(True, use_pin_memory=False, num_blocks_on_gpu=1)
if "transformer" not in pipe._exclude_from_cpu_offload:
    pipe._exclude_from_cpu_offload.append("transformer")
pipe.enable_sequential_cpu_offload()
```

Guidance:

- Do not let Diffusers sequential offload manage the `transformer` module; exclude it and let `set_offload` manage Qwen transformer blocks.
- Increase `num_blocks_on_gpu` only when spare VRAM is available.
- If offload is active, a direct `.to("cuda")` on the transformer may be skipped by design.
- On larger GPUs, `pipe.enable_model_cpu_offload()` can be simpler than per-layer Nunchaku offload.

## Dtype or precision mismatch

- Select the quantized checkpoint family with `get_precision()` when possible: FP4 for Blackwell/RTX 50-series, INT4 for other supported architectures.
- Pass `torch_dtype` during transformer and pipeline construction. Avoid recasting the quantized transformer after initialization; the source rejects dtype changes after quantization.
- Use `torch.float16` on Turing-class GPUs and usually `torch.bfloat16` otherwise.
- Keep the checkpoint name, dtype, and rank explicit in logs or run metadata so quality differences can be traced.

## Text rendering quality is weak

Qwen-Image is intended for complex text rendering, but rank, prompt layout, resolution, and inference steps matter.

- Try rank 128 assets when available; docs note that larger rank can improve quality.
- Preserve exact quoted text in the prompt and include layout instructions.
- For non-Lightning base models, examples use `true_cfg_scale=4.0` and up to 50 inference steps.
- Lightning variants trade speed for fewer steps; use the matching 4-step or 8-step checkpoint and scheduler.

## Lightning output looks wrong or ignores the expected step count

- Use the Lightning `FlowMatchEulerDiscreteScheduler` config shown in `qwen-workflows.md`.
- Match checkpoint and `num_inference_steps`: 4-step assets should run with 4 steps, and 8-step assets with 8 steps.
- Use `true_cfg_scale=1.0` for Lightning variants unless you have a tested reason to change it.
- Do not try to load arbitrary Qwen LoRAs through Nunchaku for these workflows; custom Qwen LoRA support is documented as under development.

## Edit run fails because image input is missing or malformed

- `QwenImageEditPipeline` requires an `image` argument. Load the input as a PIL image and convert to RGB.
- `QwenImageEditPlusPipeline` for 2509 can receive a single RGB image or a list of RGB images for multi-reference edits.
- Validate local image paths before running; for remote URLs, rely on `diffusers.utils.load_image` and expect network/auth failures to surface at load time.
- Avoid silently using multiple input images with the older non-2509 edit pipeline unless you have separately verified that the installed Diffusers version supports it.

## ControlNet routing produces shape or argument errors

- Use `QwenImageControlNetPipeline` with `QwenImageControlNetModel`, not the plain `QwenImagePipeline`.
- Pass a real `control_image` and set `controlnet_conditioning_scale`.
- If the control image controls output dimensions, inspect its size and pass compatible `width`/`height` only when the pipeline supports overriding them.
- Confirm `diffusers>=0.36` before diagnosing model assets.

## Model asset download or credential failures

Qwen workflows rely on large base models, quantized Nunchaku transformer checkpoints, and sometimes ControlNet or example images. Failures may be caused by missing access, a gated model, network interruption, or an incorrect file name.

- Verify the exact Hugging Face repo and file name in a browser or with your normal model-cache tooling.
- Keep credentials outside scripts; use standard Hugging Face authentication mechanisms rather than hard-coding tokens.
- For offline use, download the exact `.safetensors`/`.sft` file and pass its local file path.

## Native candidate status

Qwen native tests/examples are candidates for a later verifier once model assets, CUDA, and Diffusers version are available. This sub-skill draft did not run repo-native Qwen examples, tests, or benchmarks.
