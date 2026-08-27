# Tiled Diffusion Troubleshooting

## No-effect runs

**Symptoms**

- The panel is enabled but logs say tiling is ignored.
- Output resembles normal WebUI generation.

**Cause**

The extension skips tiling when there is only one latent tile and no other work is active. It checks whether the latent canvas can be split by tile width/height/overlap, whether region control is enabled, and whether img2img noise inversion is enabled.

**Recovery**

- Increase canvas/upscale size or reduce latent tile width/height so the image splits into multiple tiles.
- Enable region control or noise inversion only if those features are actually needed.
- Confirm DemoFusion is not also enabled.

## `UniPC` sampler conflict

**Symptoms**

- Assertion or failure indicating MultiDiffusion is not compatible with UniPC.

**Recovery**

Use a different sampler for MultiDiffusion. If the user also enables noise inversion, expect the script to switch to `Euler`.

## Noise inversion surprises

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Sampler changes to `Euler` | Noise inversion path only supports Euler. | Accept Euler or disable noise inversion. |
| Output diverges from input | Denoise too high, inversion steps/retouch mismatch, or renoise strength too aggressive. | Test on smaller image; keep denoise `<= 0.6` for default noise inversion guidance; reduce renoise strength. |
| Cached latent seems stale | Cache is reused when checkpoint, prompt, retouch, inversion steps, and image are unchanged. | Click **Free GPU** or restart WebUI to clear extension state. |
| Folder/batch img2img behaves oddly | The extension preserves and restores original init images and cleans `noise_inverse_latent`; interrupted runs can leave hooks/state. | Use **Free GPU**, then restart WebUI if state remains inconsistent. |

## ControlNet or StableSR failures

**Symptoms**

- ControlNet conditioning looks misaligned with tiles.
- VRAM spikes when ControlNet is used.
- StableSR output does not track the tiled latent.

**Recovery**

1. Prove the optional extension works without Tiled Diffusion.
2. Run a small Tiled Diffusion job and look for detection messages.
3. Enable `Move ControlNet tensor to CPU` if the problem is VRAM, not correctness.
4. Reduce tile batch size if tensor repetition/cropping increases memory.
5. If optional extension internals changed, update or pin compatible extension versions.

## Region config save/load errors

| Error or message | Cause | Fix |
| --- | --- | --- |
| `Config file name cannot be empty` | Empty Custom Config File field. | Use a simple filename such as `config.json`. |
| `Please create or upload a ref image first` | Loading requires a reference image. | Create txt2img canvas or load img2img reference first. |
| `Config ... not found` | File is absent from runtime config directory. | Save it first or use the correct config name. |
| `Failed to load config ...` | Invalid JSON or unreadable file. | Repair JSON to the `bbox_controls` shape. |

## Seams, slow runs, and memory pressure

- Increase overlap for seams, but reduce overlap for speed.
- Lower tile batch size for OOM.
- For very large region boxes, shrink the bbox or treat it as background rather than a foreground overlay when possible.
- If VAE decode/encode fails after denoising succeeds, switch to the Tiled VAE route.
- If a run is interrupted, use **Free GPU** to unhook sampler state and clear the noise inversion cache; restart WebUI if hooks remain stale.
