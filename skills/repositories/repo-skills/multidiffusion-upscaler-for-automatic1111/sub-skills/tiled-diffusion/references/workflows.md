# Tiled Diffusion Workflows

## Purpose

Use this reference to choose and configure the Tiled Diffusion panel without reopening implementation files.

## Mental model

Tiled Diffusion changes the UNet denoising path by splitting the latent canvas into overlapping tiles, denoising tiles in batches, and merging tile outputs back into the full latent. It can also add custom region boxes, region-specific prompts/seeds, ControlNet tensor tiling, StableSR tensor tiling, and noise inversion for img2img.

The extension's main methods differ in where fusion happens:

| Method | Behavior | Practical notes |
| --- | --- | --- |
| `MultiDiffusion` | Denoises individual tiles and averages overlapping tile outputs. | Default for txt2img. Not compatible with `UniPC`. Good first choice for large txt2img and regional prompt control. |
| `Mixture of Diffusers` | Fuses noise predictions with Gaussian weights before denoising the whole step. | Default for img2img. Useful for smooth tiled img2img/upscale behavior. |

## Large txt2img canvas

1. Open txt2img and enable **Tiled Diffusion**.
2. If the normal WebUI size is not the desired final size, enable **Overwrite image size** and set image width/height.
3. Start with method `MultiDiffusion` unless a prior run suggests Mixture of Diffusers is smoother for the prompt/model.
4. Start from latent tile width/height 96 and overlap 48.
5. Reduce tile batch size first when VRAM is tight; increase it only after a smaller run succeeds.
6. Keep overlap high enough to hide seams, but remember that overlap increases tile count and runtime.
7. Run a smaller proof first, then scale canvas size and/or tile count.

Validation signals:

- Logs should report a method hooked into the selected sampler, tile size, tile count, batch size, and tile batches.
- PNG generation info should contain a `Tiled Diffusion` section with method, tile width/height, overlap, and tile batch size.

## Img2img upscaling/detail enhancement

1. Open img2img with a source image and enable **Tiled Diffusion**.
2. Choose an upscaler and scale factor when you want pre-upscaling before tiled denoise.
3. Decide whether **Keep input image size** should preserve the upscaled image size or use the original dimensions plus scale factor.
4. Start with method `Mixture of Diffusers`, latent tile width/height 96, overlap 8, and tile batch size 4.
5. Tune img2img denoising strength outside this panel. For noise inversion, keep denoise low; the panel warning says default noise inversion parameters require denoise `<= 0.6`.
6. If detail changes are too strong, lower denoise or disable noise inversion before changing tiling.

PNG info can include upscaler name, upscale factor, keep-input-size, and noise inversion parameters.

## Noise inversion in img2img

Noise inversion estimates noise from the input image before img2img sampling so tiled upscaling can preserve more source structure.

Controls:

- **Enable Noise Inversion**: img2img-only.
- **Inversion steps**: default 10; higher means slower inversion.
- **Retouch**: default 1.
- **Renoise strength**: default 1.
- **Renoise kernel size**: default 64.

Operational cautions:

- The extension silently switches the sampler to `Euler` when noise inversion is enabled.
- Test on small images before a full upscale.
- Noise inversion caches one latent when checkpoint, prompt, retouch, inverse steps, and image are unchanged. Use **Free GPU** to clear that cache.
- If regional prompts are also active, the noise inversion path filters noise differently when the background is not drawn.

## ControlNet and StableSR integration

The extension does not install ControlNet or StableSR; it detects them when already present in WebUI.

ControlNet behavior:

- The script searches for a loaded script titled `controlnet` with a `latest_network` and control params.
- For grid tiles, it crops `hint_cond` tensors to tile bounds and repeats them to match the denoising batch.
- For custom regions, it prepares per-region control tensors.
- `Move ControlNet tensor to CPU` can reduce GPU memory pressure at the cost of transfer overhead.

StableSR behavior:

- The script searches for a loaded script titled `stablesr` with a non-null `stablesr_model`.
- It switches the StableSR latent image per grid tile or custom region.

If optional integrations do not activate, first prove the optional extension works without Tiled Diffusion, then run a tiny Tiled Diffusion job and check whether detection messages appear.

## Parameter tuning heuristics

| Symptom | First tuning move |
| --- | --- |
| CUDA OOM before/early in generation | Lower tile batch size; for ControlNet, try moving ControlNet tensor to CPU. |
| OOM in VAE encode/decode after denoising | Use the [Tiled VAE](../../tiled-vae/SKILL.md) route. |
| Visible seams | Increase overlap or try the other method. |
| Runtime too slow | Reduce overlap, reduce final size, or increase tile size if VRAM permits. |
| No visible Tiled Diffusion effect | Confirm the canvas splits into more than one latent tile, the panel is enabled, and no conflicting DemoFusion panel is active. |
| Sampler assertion failure | Avoid `UniPC` with MultiDiffusion. |
