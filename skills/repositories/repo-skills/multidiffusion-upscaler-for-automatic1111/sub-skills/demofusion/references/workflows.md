# DemoFusion Workflows

## Purpose

Use this reference to configure DemoFusion's staged upscaling panel and explain how its controls interact.

## Mental model

DemoFusion is a separate staged upscaling path. It first works at an initial scale, then repeatedly interpolates latents and denoises each scale stage. During each stage it combines local tiled windows with global views. This is why it exposes both local **Latent window batch size** and **Global window batch size**.

Do not enable Tiled Diffusion at the same time. Both features hook sampler/model behavior, and the UI explicitly warns against using them together.

## Basic txt2img workflow

1. Open txt2img and enable **DemoFusion**.
2. Leave Tiled Diffusion disabled for this run.
3. Choose an integer **Scale Factor**. The script treats scale factor as an integer stage count.
4. Start with **Latent window size** 128, **Latent window overlap** 64, local batch size 4, and global batch size 4.
5. Keep **Random Jitter** enabled for the default behavior; disable it when reproducibility or stable tile placement is more important.
6. Start with default cosine scales `3/1/1` and sigma `0.6`.
7. Use the substage denoising strength default `0.85` as a starting point, then lower it if the staged output over-changes the prompt result.

Validation signals:

- Logs should print `Phase 1 Denoising` and then later phase denoising messages as scale increases.
- Logs should report tile size, tile count, local/global batch sizes, and local/global batch counts.
- Infotext size is patched so staged outputs carry their generated dimensions.

## Basic img2img workflow

1. Open img2img with a source image and enable **DemoFusion**.
2. Decide whether **Keep input-image size** should preserve the source size or allow scale-stage output behavior.
3. Select integer **Scale Factor**.
4. If using noise inversion, test on a small image first and expect Euler-only behavior similar to Tiled Diffusion's inversion path.
5. Tune local/global batch sizes before changing cosine/sigma controls.

## Key controls

| Control | Default | Meaning |
| --- | --- | --- |
| Random Jitter | on | Randomly offsets local windows within a bounded jitter range. Helps vary local views but reduces deterministic placement. |
| Mixture mode | off | Changes the global view behavior; when off, sigma is halved internally before staged sampling. |
| Latent window size | 128 | Local window size in latent space, clamped to the current latent canvas. |
| Latent window overlap | 64 | Overlap for local windows. Higher overlap can improve continuity but increases work. |
| Latent window batch size | 4 | Local window batch size. Lower for VRAM pressure. |
| Global window batch size | 4 | Global view batch size. Lower for VRAM pressure in global passes. |
| Cosine Scale 1/2/3 | 3/1/1 | Weights for the staged cosine mixing factors. |
| Sigma | 0.6 | Gaussian/global filtering scale, adjusted by mixture mode and cosine factor. |
| Scale Factor | 2 | Integer number of target scale stages. |

## Optional integrations

DemoFusion has similar optional ControlNet and StableSR detection surfaces to Tiled Diffusion:

- It searches for a loaded ControlNet script and can move ControlNet tensors to CPU.
- It searches for a loaded StableSR script with a model.
- These integrations depend on the optional extensions being installed and compatible in the current WebUI runtime.

## Choosing DemoFusion vs Tiled Diffusion

Use DemoFusion when the user specifically wants DemoFusion-style multi-scale staged upscaling or is comparing the DemoFusion implementation. Use Tiled Diffusion when the user wants the extension's main MultiDiffusion/Mixture of Diffusers tiled denoising, region prompt control, or standard img2img upscale path.
