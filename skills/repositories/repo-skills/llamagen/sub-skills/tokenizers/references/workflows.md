# Tokenizer workflows

## 1. Train or finetune a VQ tokenizer
Use this when the task is to create or update tokenizer weights.

- Base training: `scripts/train_vq.sh`
- Finetune: `scripts/train_vq_finetune.sh`
- Resume finetune: `scripts/train_vq_finetune_continue.sh`

These launch `tokenizer/tokenizer_image/vq_train.py` through `torchrun` and require CUDA.

## 2. Reconstruct images through a tokenizer checkpoint
Use this when the task is to verify encode/decode quality on real images.

- VQ: `scripts/reconstruct_vq.sh`
- VQGAN: `scripts/reconstruct_vqgan.sh`
- Stable Diffusion VAE: `scripts/reconstruct_vae.sh`
- Consistency Decoder: `scripts/reconstruct_consistency_decoder.sh`

The reconstruction scripts write per-image `.png` files plus summary artifacts under the chosen sample directory.

## 3. Sanity-check a saved code tensor
Use this when you already have a tiny code tensor and want to confirm the decode path before a bigger run.

- `scripts/check_image_codes.py`
- Pass `--output-path` to verify the saved image location.
- Pass `--nrow` when you want to override the default grid layout.
- If the saved tensor includes flip or augmentation layout (`codes.ndim == 3`), the helper preserves the repo's original augmentation-count behavior.

## 4. Validate the image pipeline without a model
Use this when you only want to confirm loader, crop, and output packaging behavior.

- `scripts/validate_vq.sh`
- This does not decode through a tokenizer; it saves normalized input images and packages them into `.npz`.

## 5. Legacy VQGAN checkpoints
Use this when you only have taming-transformers `.ckpt` files.

- Convert locally with the reference-only migration note in `references/checkpoints.md`.
- Then run `scripts/reconstruct_vqgan.sh` or `tokenizer/vqgan/taming_vqgan_demo.py`.
