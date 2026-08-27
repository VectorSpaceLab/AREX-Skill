# Troubleshooting Sana, Z-Image, and SDXL replacements

Use this guide for non-FLUX Nunchaku model-family failures. It does not cover Qwen, FLUX, LoRA/adapters, or global cache/performance controls.

## Quick diagnostic table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: Only safetensors are supported` | Z-Image or SDXL replacement was given a directory, a non-safetensors file, or a model ID without a concrete `.safetensors`/`.sft` filename. | Pass a local safetensors file or a Hub-style path that includes the actual safetensors filename. |
| `NotImplementedError: Offload is not supported` | `offload=True` was passed to `NunchakuZImageTransformer2DModel.from_pretrained` or `NunchakuSDXLUNet2DConditionModel.from_pretrained`. | Remove `offload=True`. For Z-Image, construct the pipeline first, then call `pipe.enable_sequential_cpu_offload()` if appropriate. |
| CUDA assertion or custom kernel load failure | CPU-only environment, unsupported GPU architecture, or PyTorch/CUDA mismatch. | Use a compatible CUDA environment. Treat CPU as unsupported for full Nunchaku quantized inference. |
| Precision mismatch warning or poor output | The selected precision (`int4`/`fp4`) does not match the quantized asset. | On Ampere/Ada/Turing use INT4 assets; on Blackwell use FP4 assets unless separately validated. Check filenames and quantization metadata. |
| `TypeError` or shape errors after pipeline construction | Family/class mismatch, such as using an SDXL UNet asset as a transformer or a Z-Image asset in a Sana pipeline. | Re-check the family matrix: Sana/Z-Image use `transformer=`, SDXL uses `unet=`. Ensure the quantized asset and base model match the same family/variant. |
| Import failure for `ZImagePipeline` | Diffusers version does not expose the pipeline at the expected import path. | Try `from diffusers import ZImagePipeline`; if unavailable, try `from diffusers.pipelines.z_image.pipeline_z_image import ZImagePipeline`. Upgrade Diffusers if neither path exists. |
| Sana PAG output fails or ignores PAG | `pag_layers`, `pag_applied_layers`, or Diffusers PAG processor setup are inconsistent. | Use the same layer number in `NunchakuSanaTransformer2DModel(..., pag_layers=N)` and `SanaPAGPipeline(..., pag_applied_layers="transformer_blocks.N")`; preserve the compatibility workaround only after confirming the Diffusers version needs it. |
| Z-Image-Turbo output looks over-guided or slow | Base-model generation settings were used for a Turbo model. | Use Turbo settings: `guidance_scale=0.0` and a small step count such as 8-9, unless validating a different recipe. |
| SDXL-Turbo output is washed out or slow | Base SDXL guidance/step settings were used. | Use SDXL-Turbo settings: `guidance_scale=0.0` and around 4 inference steps for the native example pattern. |
| Hugging Face download error or authorization failure | External model assets require network access, cache, license acceptance, or credentials. | Ask the caller to provide accessible local files or configure credentials outside the script, for example via standard Hugging Face environment variables. Never hard-code tokens. |
| Out-of-memory during pipeline load or generation | Full pipeline placement on GPU is too large for the selected dimensions/batch. | Reduce dimensions/batch, use Z-Image sequential CPU offload where supported, or select a smaller rank/variant. Do not use replacement-class `offload=True` for Z-Image/SDXL. |

## Family-specific checks

### Sana

1. Confirm the replacement class is `NunchakuSanaTransformer2DModel` and the Diffusers pipeline receives it as `transformer=...`.
2. Confirm the loader gets a CUDA device. The Sana quantized module loader asserts `device.type == "cuda"`.
3. If using PAG, confirm `pag_layers` is an integer or list of integers and matches the pipeline's `pag_applied_layers` string.
4. Use `torch.bfloat16` for the base pipeline, VAE, and text encoder on the native example path.
5. Treat Turing and FP4 Sana paths as unverified unless separately tested; the native Sana test candidate skips them.

### Z-Image-Turbo

1. Confirm the quantized path ends with `.safetensors` or `.sft` if it is not an already-existing local file.
2. Confirm `torch_dtype` is `torch.float16` on Turing and `torch.bfloat16` otherwise.
3. Confirm `guidance_scale=0.0` for Turbo generation.
4. Use `pipe.to("cuda")` for full GPU placement or `pipe.enable_sequential_cpu_offload()` after pipeline construction for low VRAM.
5. If choosing rank manually through the asset path, use rank 32 for faster sampling, rank 128 as a common balanced setting, and rank 256 only where the selected precision/asset supports it.

### SDXL / SDXL-Turbo

1. Import `NunchakuSDXLUNet2DConditionModel` from `nunchaku.models.unets.unet_sdxl` and pass it as `unet=...`.
2. Confirm the quantized file is for SDXL base or SDXL-Turbo as appropriate; do not reuse a base SDXL asset for Turbo or the reverse without evidence.
3. Keep `variant="fp16"` and `torch_dtype=torch.bfloat16` for the native example pattern.
4. For SDXL base, use `guidance_scale=5.0` and around 50 steps when matching the native candidate.
5. For SDXL-Turbo, use `guidance_scale=0.0` and around 4 steps.
6. Treat Turing and FP4 SDXL paths as unverified unless separately tested; the native SDXL test candidate skips them.

## Safe evidence language

When reporting a result from this sub-skill, distinguish these states:

- **Documented by source:** API names, loader assertions, and example generation parameters recorded in the repository sources.
- **Verification candidate:** native tests/examples listed for a future verifier to run.
- **Observed in current environment:** only claim this after an explicit smoke or native run in the target environment.
- **Unverified:** asset availability, model license access, performance, image quality thresholds, Turing/FP4 Sana or SDXL behavior, and any untested Diffusers-version workaround.
