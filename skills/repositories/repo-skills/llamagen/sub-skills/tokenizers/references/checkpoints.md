# Checkpoints and formats

## VQ tokenizer families

| Model | Downsample | Codebook | Embed dim | Typical checkpoint |
| --- | --- | --- | --- | --- |
| `VQ-16` | 16 | 16384 | 8 | `pretrained_models/vq_ds16_c2i.pt` |
| `VQ-8` | 8 | 16384 | 8 | `pretrained_models/vq_ds8_c2i.pt` |

Notes:
- `tokenizer/tokenizer_image/vq_demo.py`, `tokenizer/tokenizer_image/reconstruction_vq_ddp.py`, and `scripts/check_image_codes.py` all require the checkpoint geometry to match the code tensor and image size.
- The released tokenizer weights also include `vq_ds16_t2i.pt`; this sub-skill owns the tokenizer side only, not the downstream generation use of that checkpoint.

## VQ training checkpoint format

`tokenizer/tokenizer_image/vq_train.py` saves:
- `model`
- `optimizer`
- `discriminator`
- `optimizer_disc`
- `steps`
- `args`
- optional `ema`

Training outputs land in the local `results_tokenizer_image/<run>/checkpoints/` tree and are mirrored under the configured `--cloud-save-path`; `--no-local-save` disables the local copy.

Load order in the reconstruction helpers:
1. `ema`
2. `model`
3. `state_dict`

## Legacy VQGAN conversion

`tokenizer/vqgan/README.md` expects converted files under:
- `pretrained_models/vqgan_imagenet_f16_1024/ckpts/last.pth`
- `pretrained_models/vqgan_imagenet_f16_16384/ckpts/last.pth`
- `pretrained_models/vq-f8-n256/model.pth`
- `pretrained_models/vq-f8/model.pth`

VQGAN keys recognized by `VQGAN_FROM_TAMING`:
- `vqgan_imagenet_f16_1024`
- `vqgan_imagenet_f16_16384`
- `vqgan_openimage_f8_256`
- `vqgan_openimage_f8_16384`

Conversion note:
- `tools/convert_pytorch_lightning_to_torch.py` is reference-only because it rewrites local artifacts.
- It expects the original Lightning `.ckpt` files in `pretrained_models/.../last.ckpt` or `model.ckpt`.
- It copies `state_dict` into a new `.pth` file.
- Use the converted `.pth` with `taming_vqgan_demo.py` and `reconstruction_vqgan_ddp.py`.

## Diffusers-backed checkpoints

- Stable Diffusion VAE: `stabilityai/sd-vae-ft-mse`, `stabilityai/sdxl-vae`
- Consistency Decoder: `openai/consistency-decoder`
- These are loaded via `from_pretrained`, so they do not use the local `pretrained_models` tree.
