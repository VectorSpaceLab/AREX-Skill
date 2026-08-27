# Data and Training Troubleshooting

## Missing training directories

Symptoms:

- Validator reports `image directory does not exist` or `label directory does not exist`.

Actions:

- Confirm the training root contains `DUTS/DUTS-TR/DUTS-TR/im_aug` and `gt_aug` by default.
- If using another layout, pass custom `--image-subdir` and `--label-subdir`.
- Do not start training until the validator reports matching pairs.

## Missing labels or orphan labels

Symptoms:

- Validator reports checked images missing labels.
- Label count differs from image count.

Actions:

- Match image and mask stems exactly.
- Verify extensions: source defaults are `.jpg` images and `.png` labels.
- Inspect a few missing pairs from validator JSON before writing conversion code.

## Crop-size failures

Symptoms:

- Random crop errors such as invalid range for `np.random.randint`.

Likely cause: image or label dimensions after resizing/adaptation are smaller than the crop size. Source training uses `RescaleT(320)` then `RandomCrop(288)`, so custom transform changes must preserve crop feasibility.

## Mask shape/channel problems

Symptoms:

- Tensor shape mismatch in BCE loss.
- Labels look all-zero or non-finite after transform.

Actions:

- Run `inspect_data_pipeline.py` with a representative image and mask.
- Ensure masks are single-channel foreground/background targets or that only the intended first channel is used.
- Keep `out_ch=1` for the default source training loop.

## Long training or GPU memory pressure

Symptoms:

- Full training takes too long on CPU.
- CUDA out-of-memory with full `U2NET` and batch size 12.

Actions:

- Ask for a bounded smoke run first.
- Reduce batch size or use `u2netp` for lightweight experiments.
- Confirm checkpoint save directory and disk space before a long run.

## Checkpoint confusion

Do not mix full `u2net` and `u2netp` checkpoint directories. If switching `model_name`, update constructor, save path, and downstream inference command together.

## Optional downloads

Downloading DUTS, APDrawingGAN, or pretrained weights is network- and storage-affecting. Obtain approval and record source URLs before running download commands.
