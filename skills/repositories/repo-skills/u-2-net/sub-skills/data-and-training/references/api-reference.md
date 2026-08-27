# Data and Training API Reference

## Dataset and transforms

| API | Signature | Notes |
| --- | --- | --- |
| `RescaleT` | `RescaleT(output_size)` | Resizes image and label to a square output size. Used in training and inference. |
| `Rescale` | `Rescale(output_size)` | Resizes while preserving aspect in one branch and includes random vertical flip behavior in source. |
| `RandomCrop` | `RandomCrop(output_size)` | Randomly crops image and label; source training uses `288`. |
| `ToTensor` | `ToTensor()` | Converts normalized arrays to channel-first tensors. |
| `ToTensorLab` | `ToTensorLab(flag=0)` | Converts RGB/Lab variants to tensors. `flag=0` is the normal 3-channel RGB path. |
| `SalObjDataset` | `SalObjDataset(img_name_list, lbl_name_list, transform=None)` | Returns `imidx`, `image`, and `label` samples. Empty label list creates zero labels for inference. |

The generated skill bundles self-contained preprocessing inspectors rather than the full source data loader. They are intended for validation and planning, not as a replacement for all research modifications.

## `validate_training_layout.py`

Checks image/mask stem pairing without loading tensors.

```bash
python scripts/validate_training_layout.py --data-root TRAIN_DATA_ROOT --json
```

Options:

- `--data-root`: root containing the DUTS tree; default `train_data`.
- `--image-subdir`: default `DUTS/DUTS-TR/DUTS-TR/im_aug`.
- `--label-subdir`: default `DUTS/DUTS-TR/DUTS-TR/gt_aug`.
- `--image-ext`: default `.jpg`.
- `--label-ext`: default `.png`.
- `--max-pairs`: optional positive limit after sorting.
- `--json`: print complete JSON; otherwise print a compact summary.

Exit status is nonzero when required directories are missing, no images are found, or checked images miss labels.

## `inspect_data_pipeline.py`

Inspects one image and optional label through a self-contained RescaleT/ToTensorLab-like path.

```bash
python scripts/inspect_data_pipeline.py --image IMAGE --label MASK --resize 320 --flag 0
```

Options:

- `--image`: image file to inspect.
- `--label`: optional mask file; omitted labels become a zero mask for inference-like checks.
- `--resize`: square resize size; default `320`.
- `--flag`: `0`, `1`, or `2`, matching source color-mode intent.
- `--json-indent`: output formatting.

Use this to verify channel-first output shapes and finite values before launching or adapting training.
