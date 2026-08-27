# Data formats

## Raw TuSimple JSON

Each line in a TuSimple label file is a JSON object. The data-preparation flow uses these fields:

| Field | Meaning | Notes |
| --- | --- | --- |
| `raw_file` | Relative path to the source frame | Usually lives under `clips/...`; join it against the unzipped TuSimple root. |
| `h_samples` | Y positions used for lane sampling | Must align with each lane array element-by-element. |
| `lanes` | X positions for each lane | `-2` means no annotation at that `h_sample` and is skipped when drawing. |

The converter draws polylines with thickness `5` and writes:
- binary lane pixels as `255` on a `0` background
- instance lane pixels as lane-specific grayscale IDs (`20`, `70`, `120`, `170`, ...)

## Raw conversion output

The bundled TuSimple converter writes a `training/` folder under the raw archive root:

- `training/gt_image/*.png`
- `training/gt_binary_image/*.png`
- `training/gt_instance_image/*.png`
- `training/train.txt`
- copied label JSON files under `training/` and `testing/`

Each row in `training/train.txt` has three columns:

```text
<image_path> <binary_mask_path> <instance_mask_path>
```

The generated names are zero-padded PNGs such as `0000.png`, `0001.png`, and so on.

## TFRecord-ready dataset root

The TFRecord step consumes a dataset root that exposes the following siblings at the top level:

- `gt_image/`
- `gt_binary_image/`
- `gt_instance_image/`
- `train.txt`
- `val.txt`
- `test.txt`
- `tfrecords/`

The TFRecord writer emits:
- `tfrecords/tusimple_train.tfrecords`
- `tfrecords/tusimple_val.tfrecords`
- `tfrecords/tusimple_test.tfrecords`

If the three list files are missing, `LaneNetDataProducer` can generate them from `gt_image/` with an internal shuffle and split. The default split is 85% train, 5% val, and 10% test.

## Image and label shaping

The pipeline uses the configured crop size and pad size from `AUG`:

| Config key | Value in this repo | Effect |
| --- | --- | --- |
| `AUG.TRAIN_CROP_SIZE` | `[512, 256]` | Final crop size used for training and evaluation. |
| `AUG.EVAL_CROP_SIZE` | `[512, 256]` | Central crop size used for validation and evaluation. |
| `AUG.CROP_PAD_SIZE` | `32` | Intermediate resize padding before cropping. |
| `DATASET.IMAGE_TYPE` | `rgb` | Source images are treated as 3-channel RGB. |
| `DATASET.CPU_MULTI_PROCESS_NUMS` | `8` | Parallel map workers in the input pipeline. |

The intermediate resize target is `544 x 288` (`512 + 32` by `256 + 32`).

- Training: random color jitter, horizontal flip, and random crop to `512 x 256`.
- Validation/test: central crop to `512 x 256`.
- Normalization: source images are converted to float and scaled by `image / 127.5 - 1.0`.
- Labels: binary and instance masks stay single-channel `uint8` tensors.

## TFRecord feature keys

The writer stores three byte features:

- `gt_image_raw`
- `gt_binary_image_raw`
- `gt_instance_image_raw`

The decoder reshapes them back to the resize target before augmentation.

## Example tree caveat

The shipped `data/training_data_example/` tree is only a rough example. Its list files still contain placeholder paths, and its image folder is named `image/` instead of `gt_image/`. Normalize that layout before using the TFRecord wrapper.
