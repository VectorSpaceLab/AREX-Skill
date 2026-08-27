# Salient Object Inference Troubleshooting

## Missing weights

Symptoms:

- JSON error: `--weights is required unless --allow-random-weights-for-smoke is set`
- JSON error: `weights file does not exist`

Actions:

1. Ask the user for a local `.pth` checkpoint path or permission to download the documented public weights.
2. Match checkpoint to task: `u2net.pth` for full saliency, `u2netp.pth` for small saliency, `u2net_human_seg.pth` for human segmentation.
3. Use random smoke only for plumbing checks, never for prediction quality.

## Empty or wrong input directory

Symptoms:

- JSON error: `no supported input images found`
- `processed_count` lower than expected

Actions:

- Confirm images are directly under `--input-dir`; the helper does not recurse.
- Check file extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tif`, `.tiff`, `.webp`.
- Use `--max-images` only when intentionally bounding a smoke check.

## Checkpoint mismatch

Symptoms:

- missing/unexpected state-dict keys;
- size mismatch in convolution weights.

Actions:

1. Verify `--task` and `--model` against [model weights](model-weights.md).
2. For saliency, `--model u2netp` must use `u2netp.pth`; `--model u2net` must use `u2net.pth`.
3. For human mode, do not force `u2netp`; the helper uses full `U2NET`.
4. If the checkpoint was saved from `DataParallel`, the helper strips `module.` prefixes automatically.

## Blank, all-white, all-black, or NaN masks

Symptoms:

- Warning about a degenerate prediction denominator.
- Output masks exist but look meaningless.

Actions:

- If using random smoke mode, this is expected and not a model-quality signal.
- If using pretrained weights, verify the checkpoint variant and that input images are valid RGB-like files.
- Check whether preprocessing size was changed from the documented `320` and whether images are extremely small or corrupt.

## CUDA/device failures

Symptoms:

- `--device cuda requested but torch.cuda.is_available() is False`
- CUDA out-of-memory on full `u2net`.

Actions:

- Use `--device cpu` for portability or `--device auto` for optional acceleration.
- For limited memory, try `--model u2netp` when the task allows lightweight saliency.
- Do not classify CUDA absence as a required-backend failure for ordinary saliency/human inference; CPU is an acceptable selected backend for functional runs when weights are present.

## Output naming surprises

Input `sample.v1.jpg` becomes `sample.v1.png`. Existing files in the output directory with the same stem may be overwritten by a new run, so use a fresh output directory for comparisons.
