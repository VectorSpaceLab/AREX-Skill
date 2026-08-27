# Setup and Compatibility

## Purpose

Read this before answering installation, load-check, backend, WebUI-version, or optional-integration questions for the Tiled Diffusion & VAE extension.

## Installation model

This repository is an AUTOMATIC1111 Stable Diffusion WebUI extension, not a standalone Python distribution. Treat installation as WebUI extension installation:

1. Install or copy the extension folder into an AUTOMATIC1111 WebUI `extensions/` directory, or use the WebUI extension installer with the public repository URL.
2. Restart WebUI so it discovers extension scripts.
3. Confirm the txt2img/img2img interfaces show panels named **Tiled Diffusion**, **Tiled VAE**, and **DemoFusion**.

A standalone import check outside WebUI is not meaningful because the extension imports WebUI-provided modules such as `modules.scripts`, `modules.processing`, `modules.shared`, `modules.devices`, and sampler classes.

## Host/runtime prerequisites

| Requirement | Why it matters |
| --- | --- |
| AUTOMATIC1111 WebUI runtime | Provides script registration, Gradio UI, processing objects, sampler factories, model state, device helpers, and launch lifecycle. |
| Stable Diffusion checkpoint and VAE | The extension hooks the active sampler and VAE; it does not supply model weights. |
| Torch backend | Real generation uses Torch tensors; CUDA is the practical target for large images, but WebUI may be configured for other backends. |
| Gradio UI | Region controls and panel widgets are WebUI/Gradio components. |
| Optional ControlNet extension | The code detects a loaded ControlNet script and crops/control-tensor batches when present. |
| Optional StableSR extension | The code detects a loaded StableSR model and switches its latent image tensors per tile when present. |

## Panels and high-level responsibilities

| Panel | Main responsibility | Read more |
| --- | --- | --- |
| Tiled Diffusion | Split latent denoising into tiles for large txt2img/img2img; supports MultiDiffusion, Mixture of Diffusers, region prompts, noise inversion, ControlNet, and StableSR. | `sub-skills/tiled-diffusion/` |
| Tiled VAE | Split VAE encode/decode work into tiles to reduce memory during high-resolution image encode/decode. | `sub-skills/tiled-vae/` |
| DemoFusion | Separate staged multi-scale upscaling workflow using local/global windows and optional jitter/mixture behavior. | `sub-skills/demofusion/` |

## Backend and model assumptions

- The README positions the extension for generating or upscaling images at 2K or larger with limited VRAM.
- Tiled workflows reduce memory pressure; they do not remove the need for a working WebUI model/backend stack.
- CPU execution may be possible only insofar as WebUI itself supports it, but it is not a practical substitute for validating large image generation.
- For Tiled VAE at very large sizes, the source comments warn that fp16 VAE can produce NaNs and recommends `--no-half-vae` for giant images.
- Optional ControlNet/StableSR behavior is auto-detected at runtime. Do not promise those controls unless the user's WebUI has those extensions loaded.

## Compatibility signals

Use these signals when diagnosing whether the extension matches the current WebUI:

- WebUI versions with `opts.hypertile_enable_unet` use `InputAccordion`; older WebUI/Gradio paths fall back to a standard accordion.
- Region Prompt Control JavaScript includes a workaround for Gradio 3.17-3.28 accordion DOM behavior; stale or invisible boxes can indicate Gradio/UI mismatch.
- The type aliases include fallbacks for older WebUI sampler modules, such as `modules.sd_samplers_compvis` when newer `modules.sd_samplers_timesteps` imports fail.
- MultiDiffusion and DemoFusion assert that the `UniPC` sampler is not compatible.

## Safe operating advice

- Start with a smaller image or lower scale before attempting a large production run.
- Increase tile sizes only until memory pressure appears; reduce tile size or batch size before changing core WebUI model settings.
- Keep Tiled Diffusion and DemoFusion mutually exclusive for one generation.
- When debugging extension load failures, first confirm WebUI can launch without this extension, then re-enable this extension and inspect startup errors.
