# Troubleshooting

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `FileNotFoundError` for `pretrained_models/...` | Local checkpoint tree is missing or incomplete | Confirm the VQ tokenizer checkpoints (`vq_ds16_c2i.pt`, `vq_ds8_c2i.pt`, and `vq_ds16_t2i.pt` if needed) plus the converted VQGAN `.pth` files are present under the expected subdirectories. VAE and Consistency Decoder checkpoints come from diffusers model ids instead. |
| `AssertionError: Training currently requires at least one GPU.` or `torch.cuda.is_available() == False` | CPU-only prefix or CUDA wheel mismatch | Use the CUDA-capable environment; the core tokenizer and reconstruction workflows are GPU-required. |
| `Torch not compiled with CUDA enabled`, `CUDA error`, or `device mismatch` | Wrong torch / torchvision wheel pair | Recheck the installed `+cu121` wheels and keep them paired with the host CUDA driver. |
| `load_state_dict` missing / unexpected keys | Wrong checkpoint family or stale format | Match `--vq-model`, `--codebook-size`, `--codebook-embed-dim`, and the checkpoint format (`model`, `ema`, `state_dict`). For VQGAN, use the converted `.pth` file. |
| `ModuleNotFoundError: skimage` during reconstruction wrappers | The reconstruction helpers call `skimage.metrics` for PSNR / SSIM | Install `scikit-image` in the active environment before running the reconstruction wrappers or the DDP reconstruction examples. |
| `ModuleNotFoundError: omegaconf` in the legacy VQGAN demo | The taming-transformers demo relies on an OmegaConf config | Install `omegaconf` before using `tokenizer/vqgan/taming_vqgan_demo.py`, or use the bundled reconstruction wrappers instead. |
| `ModuleNotFoundError: pytorch_lightning` in the legacy VQGAN conversion path | The conversion note assumes the original taming-transformers Lightning package is available during migration | Install `pytorch_lightning` only for the one-time conversion step, then remove it again or use the converted `.pth` files with the bundled wrappers. |
| Decoded image size or reconstruction looks wrong | `--image-size` or `--downsample-size` mismatch | Make the code tensor geometry match the model geometry. The helper assumes the same token-grid size the checkpoint was trained for. |
| The code/image grid looks scrambled or too wide | The augmentation dimension was misunderstood | For saved tensors with `codes.ndim == 3`, the helper treats `codes.shape[1]` as the augmentation count; override `--nrow` if you want a different layout. |
| VQGAN demo fails on raw `.ckpt` weights | Lightning conversion was skipped | Run the reference-only conversion step first, then point the demo at the generated `.pth` file. |
| `ImageFolder` cannot find classes or COCO path errors | Dataset layout mismatch | Use `imagenet` only for ImageFolder-style trees; use `coco` for a flat image folder. |

## Fast checks

1. Confirm the checkpoint family and path layout.
2. Confirm `--vq-model`, `--codebook-size`, `--codebook-embed-dim`, `--image-size`, and `--downsample-size` match the saved codes.
3. Run the tiny code round-trip helper before a larger reconstruction job.
4. If the problem is still unclear, compare against the workflow and checkpoint notes instead of reopening the source repo.
