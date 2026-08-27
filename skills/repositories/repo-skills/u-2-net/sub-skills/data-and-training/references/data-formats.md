# Data Formats and Layouts

## Training layout

The source training script expects a DUTS-style directory tree below `train_data/`:

```text
train_data/
  DUTS/DUTS-TR/DUTS-TR/
    im_aug/
      <stem>.jpg
    gt_aug/
      <stem>.png
```

Each image stem in `im_aug` should have a matching mask stem in `gt_aug`. Use the bundled validator before planning a training command:

```bash
python scripts/validate_training_layout.py --data-root TRAIN_DATA_ROOT --max-pairs 100 --json
```

For an adapted dataset, preserve the same image/mask stem pairing or pass custom `--image-subdir`, `--label-subdir`, `--image-ext`, and `--label-ext` options to the validator.

## Sample dictionary schema

The source `SalObjDataset` yields dictionaries with:

| Key | Meaning |
| --- | --- |
| `imidx` | One-element array/tensor containing the sample index. |
| `image` | Image array/tensor. Before tensor conversion it is HWC; after conversion it is channel-first. |
| `label` | Mask array/tensor. If no labels are supplied for inference, a zero label matching the image is used. |

Training uses labels; inference scripts pass an empty label list.

## Transform chain

Training chain:

```text
RescaleT(320) -> RandomCrop(288) -> ToTensorLab(flag=0)
```

Inference chain for saliency/human segmentation:

```text
RescaleT(320) -> ToTensorLab(flag=0)
```

Portrait-set chain:

```text
RescaleT(512) -> ToTensorLab(flag=0)
```

`flag=0` uses RGB normalization with ImageNet-style means/stds. `flag=1` uses Lab color. `flag=2` concatenates RGB and Lab-like channels, producing six channels; do not use it with the default `U2NET(3,1)` unless the model input channels are changed deliberately.

## Inspect one sample

```bash
python scripts/inspect_data_pipeline.py \
  --image IMAGE_FILE \
  --label OPTIONAL_MASK_FILE \
  --resize 320 \
  --flag 0
```

The script prints JSON summaries before transform, after resize, and after tensor conversion. Use it to catch shape/range problems before a long training run.

## Common data pitfalls

- Image and label stems differ.
- Labels are nested in subdirectories; the source training loop expects flat `gt_aug` files.
- Images are smaller than the crop size after custom resizing, which can break random crop.
- Mask files are RGB color images but only one channel is intended.
- `flag=2` changes the input channel count to six and is incompatible with default 3-channel model constructors unless the architecture is edited.
