# Programmatic API Troubleshooting

## Package import fails before code runs

If importing `stylegan2_pytorch` fails with a CUDA assertion or missing package,
use the root [cross-cutting troubleshooting](../../../references/troubleshooting.md).
The programmatic API cannot be used from a CPU-only torch environment in this
source snapshot.

## `ModelLoader` cannot find a checkpoint

**Symptoms**

- No `continuing from previous epoch - <n>` message appears.
- Later calls fail because `GAN` or moving-average modules are not initialized.
- The helper script reports no `model_*.pt` files.

**Likely causes**

- `base_dir` is not the directory where the CLI used the default layout.
- The project `name` differs from the CLI `--name`.
- Training used a custom `--models_dir`; `ModelLoader` does not expose a
  `models_dir` parameter.
- `--new` cleared the prior checkpoints.

**Recovery**

- Check for `base_dir/models/<name>/model_<n>.pt` and
  `base_dir/models/<name>/.config.json`.
- Use `load_from=<n>` for a specific checkpoint.
- If the checkpoint lives in a custom models directory, either create the
  default layout or use `Trainer(name=..., base_dir=..., models_dir=...)`
  directly.

## Tensor/device failures

`ModelLoader.noise_to_styles` calls `noise.cuda()`, and `styles_to_images` uses
CUDA device `0` for image noise. If the user passes CPU tensors or uses a
non-default CUDA device setup:

- Create noise with `torch.randn(count, 512).cuda()` or move it to the active
  CUDA device before calling `noise_to_styles`.
- Set `CUDA_VISIBLE_DEVICES` before launching Python if a specific GPU should
  become logical device `0`.
- Reduce sample `count` when image generation runs out of memory.

## Wrong latent dimension or style shape

The latent dimension is `512` in this source snapshot. Use:

```python
noise = torch.randn(count, 512).cuda()
styles = loader.noise_to_styles(noise, trunc_psi=0.75)
images = loader.styles_to_images(styles)
```

Do not pass arbitrary image tensors to `noise_to_styles`; it expects latent
noise, not input images.

## Version or architecture mismatch

If loading raises after printing guidance about the saved model version, suspect
one of these:

- The checkpoint was created by a different package version.
- `image_size`, `network_capacity`, `transparent`, attention layers, feature
  quantization layers, or `no_const` differ from the saved `.config.json`.
- The checkpoint path points to a different project.

Recovery options:

1. Restore the package version or architecture settings used to create the
   checkpoint.
2. Start a new training run if the user intentionally changed architecture.
3. Preserve the old checkpoint and config before trying migrations.

## Output overwrite and format surprises

- Save RGB models to `.jpg` or `.png`; transparent models should use `.png` to
  preserve alpha.
- The bundled helper refuses to overwrite an existing output file unless
  `--overwrite` is set.
- `save_image` writes grids; use `nrow` to control grid shape.
