# Data formats

## COCO JSON

`CocoDataset` expects COCO-style JSON annotations and an image folder.
The dataset loader uses `pycocotools` to read images, categories, and annotations.

### Expected properties

- Each image entry must have a stable integer `id`.
- Each annotation must provide a valid `bbox`, `category_id`, and positive area.
- The category list in the JSON must match the class names that the config and head expect.

### Notes

- Crowd or ignored annotations are separated into the ignored box set.
- Invalid boxes with non-positive width or height are skipped.

## VOC XML

`XMLDataset` converts a directory of VOC-style XML files into an internal COCO-like structure.

### Expected properties

- `class_names` must be supplied in the config.
- Each XML file must contain `filename`, `size/width`, `size/height`, and `object` entries.
- Objects whose class names are not in `class_names` are skipped with a warning.
- Boxes with negative width or height are skipped.

## YOLO TXT

`YoloDataset` expects annotation text files with a matching image file beside each annotation.

### Expected properties

- The annotation file and image file share the same basename.
- The image can use a supported extension such as `.png`, `.jpg`, `.jpeg`, `.bmp`, or `.tiff`.
- The first value in each line is the zero-based class id.
- Remaining values encode normalized `x_center, y_center, width, height` box coordinates in the format used by the repo's loader.

### Notes

- If the matching image cannot be found, the loader skips that annotation file and logs a warning.
- Category IDs that exceed the configured class list are skipped.

## Preprocessing and batching

| Helper | What it does |
| --- | --- |
| `Pipeline` | Applies shape transforms and color normalization to a sample |
| `ShapeTransform` | Resizes and warps image + boxes + masks |
| `stack_batch_img` | Pads tensors to a common size and stacks them into a batch |
| `naive_collate` | Keeps dict values as lists and avoids over-collapsing metadata |

## Field conventions

- `input_size` is stored as `[width, height]` in the configs.
- `normalize` is a pair of arrays: mean and std.
- `multi_scale` is a scale-factor range, not an absolute size list.
- `class_names` controls both training labels and visualization order.
