# Data Formats and Generator Contracts

This repository is centered on object-detection datasets rather than a single fixed schema. The `DataGenerator` class can load data directly from filenames and labels, from HDF5, or from CSV / XML / JSON annotation sources.

## Supported input sources

### CSV

`DataGenerator.parse_csv(images_dir, labels_filename, input_format, ...)`

Expected columns in the CSV rows:

- image file name
- class ID
- `xmin`
- `xmax`
- `ymin`
- `ymax`

Important notes:

- The row order can vary, but the parser expects those six fields to be present.
- The parser skips the header row.
- `class_id` is expected to be a positive integer; background is class 0.
- `input_format` must describe the CSV column order.

### Pascal VOC XML

`DataGenerator.parse_xml(images_dirs, image_set_filenames, annotations_dirs, classes=..., ...)`

Expected inputs:

- one image directory per dataset split
- one image-set text file per split
- one annotation directory per split, when labels are available

Important notes:

- The classes list must begin with `background`.
- `exclude_truncated` and `exclude_difficult` let you filter VOC annotations.
- The parser can merge multiple VOC-style splits.

### COCO JSON

`DataGenerator.parse_json(images_dirs, annotations_filenames, ground_truth_available=False, ...)`

Expected inputs:

- one image directory per split
- one annotations JSON file per split

Important notes:

- COCO category IDs are not consecutive; `eval_utils.coco_utils.get_coco_category_maps()` converts them to contiguous class IDs.
- The JSON format is used by the COCO evaluation notebook and helper utilities.

### HDF5

`DataGenerator.create_hdf5_dataset(file_path='dataset.h5', ...)`

The HDF5 file stores flattened images, image shapes, flattened labels, label shapes, image IDs, and optional evaluation-neutral flags.

`DataGenerator.load_hdf5_dataset()` can then reload the same structure without reparsing the source annotations.

## Generator contract

`DataGenerator.generate(batch_size=32, shuffle=True, transformations=[], label_encoder=None, returns={...}, keep_images_without_gt=False, degenerate_box_handling='remove')`

Key outputs the generator can yield:

- `processed_images`
- `encoded_labels`
- `matched_anchors`
- `processed_labels`
- `filenames`
- `image_ids`
- `evaluation-neutral`
- `inverse_transform`
- `original_images`
- `original_labels`

Important notes:

- If `label_encoder` is an `SSDInputEncoder`, the generator can produce encoded labels for SSD training.
- `degenerate_box_handling='remove'` is the safest default for noisy datasets.
- `keep_images_without_gt=False` removes empty images from training batches.

## Label conventions

The codebase commonly uses one of two label layouts:

- detection labels: `(class_id, xmin, ymin, xmax, ymax)`
- CSV parsing input order: any order, as long as `input_format` tells the parser where each field lives

When a transform or generator needs a label mapping, it uses a `labels_format` dictionary such as:

- `class_id`
- `xmin`
- `ymin`
- `xmax`
- `ymax`

## Augmentation and validity helpers

- `ConvertTo3Channels` converts grayscale or single-channel images to three channels.
- `Resize` and `ResizeRandomInterp` reshape images to the model input size.
- `RandomFlip`, `RandomTranslate`, `RandomScale`, and `RandomRotate` alter geometry.
- `ConvertColor`, `RandomBrightness`, `RandomContrast`, `RandomHue`, `RandomSaturation`, `RandomGamma`, and `RandomChannelSwap` perform photometric augmentation.
- `BoxFilter`, `ImageValidator`, and `BoundGenerator` are used to keep crops and boxes valid.

## Practical rule

The dataset loader, augmentation chain, and encoder must agree on the same coordinate convention. If boxes look shifted, clipped, or disappear, check `labels_format`, `coords`, `normalize_coords`, and the image size passed into the encoder or decoder.
