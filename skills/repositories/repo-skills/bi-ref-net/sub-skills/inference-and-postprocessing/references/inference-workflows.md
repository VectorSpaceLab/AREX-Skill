# BiRefNet Image Inference Workflows

## Load paths

- **Hugging Face load**: the source helper uses `BiRefNet.from_pretrained(repo_id, bb_pretrained=False)`.
- The README also shows `transformers.AutoModelForImageSegmentation.from_pretrained('zhengpeng7/BiRefNet', trust_remote_code=True)`; that shortcut is optional and needs `transformers`.
- **Local `.pth` load**:
  - build `BiRefNet(bb_pretrained=False)`;
  - load the checkpoint from CPU with `weights_only=True` when available;
  - clean prefixes with `check_state_dict` (`module.`, `_orig_mod.`);
  - if the checkpoint stores weights under a nested key, unwrap the tensor state dict first.
- If the load fails, treat it as a backbone/config mismatch, a missing dependency, or a non-BiRefNet checkpoint.

## Bundled image helper

The runtime helper is designed to be explicit and low-risk:

1. Pass `--repo-root` so the helper imports the intended checkout only.
2. Point `--input` at a single image or an image directory.
3. Point `--output-dir` at a separate destination tree.
4. Select `--model-source local` for a `.pth` file or `--model-source hf` for hub weights.
5. Use `--resolution config.size` for the repo default, `original`/`keep` for no resize, or a concrete `WxH` value.
6. Run `--dry-run` first to confirm path discovery, device choice, and output layout without loading weights.
7. Enable `--foreground-refine` only when you want a matting-style foreground export.
8. Enable `--save-comparison` only when you want a three-panel preview.

## Notebook-style image workflow

1. Open the image and convert it to RGB.
2. Resize the model input to `config.size` by default.
3. Apply `ToTensor` and ImageNet normalization:
   - mean `[0.485, 0.456, 0.406]`
   - std `[0.229, 0.224, 0.225]`
4. Run the model in eval/inference mode.
5. Take the last prediction tensor and apply sigmoid:

```python
with autocast_ctx, torch.inference_mode():
    pred = birefnet(batch)[-1].sigmoid().to(torch.float32)
```

6. Convert the first mask to PIL and resize it back to the original image size.
7. Save the mask as PNG.
8. When `--foreground-refine` is enabled, call `refine_foreground(image, mask, device='cuda' or 'cpu')` and attach the mask as alpha.
9. When `--save-comparison` is enabled, generate a 3-panel image: mask, source image, and a foreground/composited preview.

## Output layout

- `masks/<relative-name>.png`
- `foregrounds/<relative-name>.png`
- `comparisons/<relative-name>.png`
- Keep the relative folder structure when the input is a directory.
- Always save soft prediction masks as PNG, even if the source file is JPG/JPEG.

## Device and precision

- `--device auto` falls back to CPU when CUDA is unavailable.
- Explicit `--device cuda` should fail with a clear error on CPU-only builds.
- CUDA autocast is only used on CUDA.
- CPU inference should use plain `torch.inference_mode()` with no autocast.
- The repository default mixed precision is BF16; if BF16 is not supported, fall back to FP16 on CUDA.
- `Config.size` and `dataset.py` treat image size as `(width, height)`; `torchvision.transforms.Resize` wants `(height, width)`, so the helper flips the tuple before resizing.
- `refine_foreground` accepts PIL image/mask inputs and resizes a mismatched mask to the image size.
- For large images, lower `--resolution` or skip refinement/comparison to reduce memory.

## Native `inference.py` semantics

- Default parser behavior points `--ckpt_folder` at `ckpts/*`; that glob can fail immediately when no checkpoint directory exists.
- `--resolution` accepts `None`/`default`/`config.size` or an explicit `WxH` string.
- The script iterates over configured testsets, loads each `.pth`, cleans the state dict, and writes predictions to:
  `<pred_root>/<method>/<testset>/<filename>.png`
- Each prediction is interpolated back to the label size before saving.
- If a user wants a direct CLI replacement for notebook inference, prefer the bundled helper rather than the native script when the checkpoint layout is not already prepared.

## Practical validation

- Use `--dry-run` to confirm path discovery, device choice, and output locations without loading weights or downloading anything.
- Prefer local weights for reproducible offline checks.
- Use HF mode only when hub download/cache access is expected.
- The dry-run still checks the requested backend and local checkpoint path when those options are provided.
