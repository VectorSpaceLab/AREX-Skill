# Image Diffusion Troubleshooting

Use this page to diagnose common 2D image workflow failures in `denoising-diffusion-pytorch` version 2.3.1.

## Import or dependency failure

Install the public distribution name:

```bash
python -m pip install denoising-diffusion-pytorch
```

If only FID fails, separately verify `pytorch-fid`, `scipy`, `torchvision`, and any Inception cache/model access.

## Image size or tensor shape mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `height and width of image must be ...` | Tensor H/W differs from `image_size` | Resize/crop images or construct `GaussianDiffusion(..., image_size=<actual>)`. |
| `Conv2d` expected channels mismatch | `Unet(channels=...)` differs from tensor channels | Use `channels=1`, `3`, or `4` and convert images consistently. |
| input dimensions need to be divisible by downsample factor | Height/width not divisible by `2 ** (len(dim_mults)-1)` | Choose compatible dimensions or reduce `dim_mults` for smoke tests. |
| mixed image modes in folder | Dataset conversion inconsistent | Set `convert_image_to='L'`, `'RGB'`, or `'RGBA'`. |

## Invalid objective or schedule

Valid base image values:

- `objective`: `'pred_noise'`, `'pred_x0'`, `'pred_v'`.
- `beta_schedule`: `'linear'`, `'cosine'`, `'sigmoid'`.

Pass exact lowercase strings. For tiny smoke tests prefer `objective='pred_v'` and `beta_schedule='sigmoid'`.

## `sampling_timesteps > timesteps`

Set `sampling_timesteps=None`, equal to `timesteps`, or a smaller positive integer. Smaller values select DDIM.

## NaN loss in tiny tests

A very small `timesteps=4` plus `beta_schedule='linear'` can produce NaN in a synthetic smoke. Use the bundled defaults first: `timesteps=8`, `sampling_timesteps=4`, `beta_schedule='sigmoid'`, finite inputs in `[0, 1]`, and `amp=False`.

## Trainer gates

- Effective batch size must satisfy `train_batch_size * gradient_accumulate_every >= 16`.
- Folder must contain at least 100 matching image files.
- `num_samples` must be square: `1`, `4`, `9`, `16`, `25`, ...
- `save_best_and_latest_only=True` requires `calculate_fid=True`.

Do not use `Trainer` for a tiny two-image smoke; call `diffusion(images)` or run the bundled smoke script.

## FID is slow or failing

Disable FID for smoke and early wiring: `calculate_fid=False`. When enabling FID, prefer DDIM (`sampling_timesteps < timesteps`), verify `inception_block_idx` support, and remember dataset stats are cached as `dataset_stats.npz` under the results folder.

## CUDA or flash attention issues

Use `--device cpu` for the first smoke. Enable CUDA or `flash_attn=True` only after `torch.cuda.is_available()` and PyTorch SDPA compatibility are verified. `flash_attn` in this package uses PyTorch scaled-dot-product attention, not an additional third-party package.

## RePaint mask errors

Use `gt` shaped `(batch, channels, height, width)` in `[0, 1]` and a mask shaped `(batch, 1, height, width)` or `(batch, channels, height, width)`. Mask value `1` preserves ground truth and `0` regenerates. If sampling is too slow, test with `resample=False` first.
