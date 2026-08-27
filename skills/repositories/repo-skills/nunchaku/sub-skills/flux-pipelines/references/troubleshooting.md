# FLUX troubleshooting

Use this when a Nunchaku FLUX or FLUX v2 Diffusers replacement fails before or during one-image generation.

## Quick diagnosis checklist

1. Confirm the task is a FLUX-family task. Qwen-Image, Sana, Z-Image, and SDXL use other model classes.
2. Confirm the selected Diffusers pipeline matches the base model: `FluxPipeline`, `FluxKontextPipeline`, `FluxControlPipeline`, `FluxFillPipeline`, `FluxPriorReduxPipeline`, or `FluxControlNetPipeline` as appropriate.
3. Confirm the transformer asset is a Nunchaku quantized FLUX asset, not the full Diffusers transformer directory.
4. Confirm CUDA is available. Nunchaku quantized FLUX transformer loading is not a CPU-only path.
5. Confirm the dtype and precision match the GPU and asset: `bf16` + INT4 for most modern NVIDIA GPUs, FP4 assets for Blackwell, FP16 on Turing.

## Import or extension loading failures

Symptoms:

- `ModuleNotFoundError: No module named 'nunchaku'`
- CUDA extension import errors
- errors about unsupported architecture or missing CUDA/Torch symbols

Actions:

- Install a Nunchaku build compatible with the local Python, PyTorch, and CUDA versions.
- Use Python >=3.10 and a CUDA-capable PyTorch build. Nunchaku source evidence requires CUDA for quantized FLUX inference.
- If the build reports unsupported SM, use a supported GPU architecture or rebuild/install a wheel built for the target CUDA architecture. Source build evidence lists common supported SM targets including Turing, Ampere, Ada, and Blackwell-class devices.
- Do not attempt to work around extension failures by moving the Nunchaku transformer to CPU; the quantized module loader asserts CUDA device use.

## Model asset access failures

Symptoms:

- Hugging Face 401/403 errors
- `RepositoryNotFoundError`, `EntryNotFoundError`, or similar hub-download failures
- local path not found
- generation code works for public assets but fails for gated FLUX base models

Actions:

- Verify the base model id and the Nunchaku transformer model-file path are both accessible to the runtime account.
- If the selected Hugging Face model is gated, authenticate using the standard Hugging Face mechanism for the environment; do not hard-code tokens in scripts.
- For offline runs, pass local model and transformer paths and configure Hugging Face local/offline behavior outside the template.
- Check spelling and case. FLUX model ids are case-sensitive; evidence includes both lower-case and capitalized `FLUX.1-krea-dev` variants, so verify the currently published upstream id if Krea loading fails.

## Safetensors versus directory loading

Symptoms:

- `AssertionError: Only safetensors are supported`
- warnings that folder loading is deprecated
- file names such as `unquantized_layers.safetensors` or `transformer_blocks.safetensors` are missing

Actions:

- Prefer a single Nunchaku `.safetensors` or `.sft` transformer asset.
- Use `NunchakuFluxTransformer2DModelV2` only with single safetensors-style assets. Source inspection shows V2 asserts on non-safetensors paths.
- If a legacy directory is unavoidable, use `NunchakuFluxTransformer2dModel`, not V2, and ensure the folder contains the expected legacy weight files.
- Do not pass a standard Diffusers base-model directory as the Nunchaku transformer argument; the transformer argument must point to Nunchaku quantized weights.

## Dtype and precision mismatches

Symptoms:

- warnings that an FP4 model is being loaded with INT4 precision or vice versa
- NaNs or unstable outputs on older GPUs
- Turing GPU failures when using BF16

Actions:

- Let `nunchaku.utils.get_precision()` select `int4` or `fp4` when possible, then use a matching transformer asset path.
- On Blackwell-class GPUs, use FP4 assets when `get_precision()` returns `fp4`.
- On Turing GPUs, set both transformer and pipeline `torch_dtype=torch.float16` and use the non-V2 transformer's `set_attention_impl("nunchaku-fp16")` when available.
- On Ampere/Ada/Hopper-class GPUs, `torch.bfloat16` is the normal default in examples.

## Offload and low-VRAM failures

Symptoms:

- CUDA out-of-memory during transformer load or pipeline construction
- `NotImplementedError: Offload is not supported for FluxTransformer2DModelV2`
- failure after calling `.to("cuda")` before enabling offload

Actions:

- For `NunchakuFluxTransformer2dModel`, pass `offload=True` while loading the transformer and call `pipeline.enable_sequential_cpu_offload()` instead of eagerly moving the whole pipeline to CUDA.
- For `NunchakuFluxTransformer2DModelV2`, do not pass `offload=True` to `from_pretrained`. Use Diffusers offload on the pipeline or choose the non-V2 transformer class when transformer-level offload is required.
- Avoid calling `pipe.to("cuda")` before enabling CPU offload. Construct the pipeline, then choose either `.to(device)` or offload, not both in that order.
- Reduce width, height, batch size, and number of steps for smoke runs.

## Turing-specific failures

Symptoms:

- Turing/RTX 20-series run fails with BF16 dtype errors
- attention implementation errors or poor performance
- VRAM pressure even for one image

Actions:

- Use `torch.float16` for both transformer and pipeline.
- Use `NunchakuFluxTransformer2dModel` for the documented Turing path.
- Call `transformer.set_attention_impl("nunchaku-fp16")` after loading the transformer.
- Pair transformer `offload=True` with `pipeline.enable_sequential_cpu_offload()` when memory is limited.

## `return_metadata` tuple mistakes

Symptoms:

- Diffusers reports that `transformer` is a tuple or has no expected transformer attributes

Cause:

- `NunchakuFluxTransformer2dModel.from_pretrained(..., return_metadata=True)` returns `(transformer, metadata)`.

Action:

```python
transformer, metadata = NunchakuFluxTransformer2dModel.from_pretrained(path, return_metadata=True)
metadata = metadata or {}
pipe = FluxPipeline.from_pretrained(base_model, transformer=transformer, torch_dtype=torch.bfloat16)
```

Do not expect V2 to provide the same metadata-return contract.

## Kontext and tool-pipeline input failures

Symptoms:

- pipeline complains that `image`, `mask_image`, or `control_image` is missing
- control preprocessors such as `controlnet_aux` or `image_gen_aux` are missing
- image size mismatch or unexpected dimensions

Actions:

- Kontext requires a source `image=` plus an editing `prompt=`.
- Fill requires both `image=` and `mask_image=`.
- Canny and Depth require a preprocessed `control_image=` and the corresponding external preprocessing dependency.
- Keep image dimensions consistent with the selected pipeline and use explicit `height=` and `width=` when control images define the generation size.

## V2 control caveat

The V2 source forward method raises `NotImplementedError` if controlnet residual samples are passed. If a Canny or Depth route with `NunchakuFluxTransformer2DModelV2` fails on a controlnet-not-supported error, switch that workflow to `NunchakuFluxTransformer2dModel` or verify against the exact installed package version before treating it as supported.

## Verification candidates

Potential native checks for a verifier include selected FLUX example scripts, `tests/flux/test_flux_examples.py`, and one or two targeted `tests/v1/flux/test_flux1_*.py` cases. These are candidates only; do not claim they passed unless a verifier actually runs them with accessible model assets and a compatible CUDA environment.
