# DemoFusion Troubleshooting

## DemoFusion and Tiled Diffusion both enabled

**Symptoms**

- Unstable output, sampler hooks conflicting, unexpected no-effect behavior, or confusing logs.

**Cause**

DemoFusion and Tiled Diffusion both hook WebUI sampler/model behavior. The DemoFusion UI explicitly warns not to open it with Tiled Diffusion.

**Recovery**

Disable Tiled Diffusion for DemoFusion runs. Use only one large-image denoising method per generation.

## `UniPC` sampler conflict

**Symptom**

DemoFusion fails with a sampler compatibility assertion.

**Recovery**

Select a sampler other than `UniPC` for DemoFusion.

## Slow or OOM staged upscale

**Likely causes**

- Scale factor adds multiple denoising stages.
- High local overlap increases tile count.
- Local and global batch sizes multiply memory use.
- ControlNet/StableSR optional integrations add tensors.

**Recovery**

1. Lower local **Latent window batch size**.
2. Lower **Global window batch size**.
3. Reduce overlap if seams/continuity remain acceptable.
4. Use a smaller integer scale factor for the proof run.
5. If ControlNet is active, try moving ControlNet tensors to CPU.
6. If VAE decode fails after DemoFusion, use Tiled VAE settings.

## Output changes too much or not enough

| Symptom | Tuning path |
| --- | --- |
| Staged result over-changes the prompt/base image | Lower txt2img substage denoising strength or reduce scale factor. |
| Local details look inconsistent | Disable Random Jitter for a deterministic comparison, then tune overlap/window size. |
| Global structure drifts | Tune cosine scales and sigma conservatively; compare mixture mode on/off. |
| Img2img result ignores input proportions | Recheck **Keep input-image size** and scale factor. |

## Random jitter reproducibility

Random jitter is enabled by default and offsets local windows within a bounded range. If a user is comparing settings or needs deterministic tile placement, disable Random Jitter before changing multiple other controls.

## Noise inversion caveats

DemoFusion exposes an img2img Noise Inversion accordion similar to Tiled Diffusion. Use the same cautions:

- Test small first.
- Expect Euler-only behavior for inversion.
- Use **Free GPU** or restart WebUI if interrupted runs leave stale state.
