# Tiled VAE Troubleshooting

## VAE OOM

**Symptoms**

- Generation denoising finishes, then decode fails with CUDA OOM.
- Img2img fails while encoding a large source image.
- Logs show Tiled Diffusion tile batches succeeded, but VAE still fails.

**Recovery**

1. Enable **Tiled VAE**.
2. Lower **Decoder Tile Size** for output decode failures.
3. Lower **Encoder Tile Size** for img2img input encode failures.
4. Keep **Fast Decoder** and **Fast Encoder** enabled if memory is the main problem.
5. If VAE is left on CPU while CUDA is available, try enabling **Move VAE to GPU** when VRAM allows.
6. If memory still fails, reduce image size/upscale factor or use lower precision/model settings at the WebUI level.

## NaNs with giant images

**Symptoms**

- WebUI reports NaNs in VAE.
- Output is corrupt or the run aborts during VAE tiled execution.

**Cause**

The source comments warn that fp16 VAE can produce NaNs on 8K-style images.

**Recovery**

- Launch WebUI with `--no-half-vae` for giant-image work.
- Reduce tile sizes and retry.
- Disable fast encoder/decoder if NaNs occur during fast mode estimation.
- If using MPS, be aware that the implementation clamps some fp16 variance values to avoid overflow.

## Unknown attention optimization warning

**Symptom**

`[Tiled VAE] Warning: Unknown attention optimization method ...`

**Cause**

The WebUI attention optimization method is not one of the names recognized by the helper.

**Recovery**

- Switch WebUI to a supported attention optimization when possible.
- Update WebUI and/or the extension if the method name is from a newer WebUI.
- Use the fallback path for a small validation run before attempting a large output.

## Stale VAE hook after an interrupted run

**Symptoms**

- VAE behavior remains altered after disabling Tiled VAE.
- Later runs fail in unexpected VAE hook code.

**Recovery**

The script restores encoder/decoder `forward` methods when disabled and in postprocess, but hard interruptions can leave state stale. Disable Tiled VAE and run a tiny job, use WebUI memory cleanup, or restart WebUI to guarantee original VAE forwards are restored.

## Output color or quality shifts

**Likely causes**

- Fast encoder/downsampled GroupNorm estimation differs from the full path.
- Tile size too small for stable normalization.
- Half VAE precision issues at large resolution.

**Recovery**

- Try **Fast Encoder Color Fix**.
- Increase tile size if memory allows.
- Disable fast encoder for a comparison run.
- Use `--no-half-vae` when large-image fp16 behavior is suspect.
