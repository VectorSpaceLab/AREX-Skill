# Dataset Formats

## Purpose

This reference summarizes the dataset layouts that Luminoth's built-in readers
expect and the TFRecord schema that the writer produces.

## Output schema

Luminoth's object-detection writer emits one `SequenceExample` per image.

### Context features

- `image_raw`: encoded image bytes
- `filename`: original file name or image id
- `width`: image width
- `height`: image height
- `depth`: number of channels

### Sequence features

- `label`: class index for each bounding box
- `xmin`: left x coordinate
- `ymin`: top y coordinate
- `xmax`: right x coordinate
- `ymax`: bottom y coordinate

The writer also creates `classes.json`, which stores the pretty class names in
class-index order.

## Reader layouts

| Reader | Required layout | Notes |
| --- | --- | --- |
| `pascal` | `ImageSets/Main/{split}.txt`, `JPEGImages/{image_id}.jpg`, `Annotations/{image_id}.xml` | VOC-style folder layout. The split file lists image ids. |
| `imagenet` | `ImageSets/DET/{split}.txt`, `Data/DET/{split}/{image_id}.JPEG`, `Annotations/DET/{split}/{image_id}.xml` | ImageNet DET layout. The reader skips entries tagged as `extra`. |
| `coco` | `instances_{split}2017.json` or `annotations/instances_{split}2017.json`, plus images in `{split}2017/` | Reads COCO annotations and maps categories to class labels or supercategories. |
| `csv` | `{split}.csv` plus images in `{split}/` | Default columns are `image_id,xmin,ymin,xmax,ymax,label`. |
| `flat` | `{split}/` containing images and sidecar annotations with the configured extension | Default annotation type is JSON. Default object key is `rects`. |
| `taggerine` | `{split}/` containing Taggerine-style JSON annotations and image files | Supports both normalized corner boxes and `x,y,width,height` boxes. |
| `openimages` | `class-descriptions-boxable.csv`, `{split}/{split}-annotations-bbox.csv`, and `{split}/{split}-annotations-human-imagelabels-boxable.csv` | Images are downloaded from the OpenImages bucket, so network and access setup are required. |

## Reader-specific notes

- CSV readers can skip headers when `--override headers=false` is supplied, but
  the column names must still match the expected six-field schema.
- Flat readers can use `--override objects_key=...` and custom coordinate keys
  when the annotations use non-default names.
- OpenImages readers expect the trainable-label CSV and class-description CSV to
  live in the dataset root.
- Taggerine readers accept either normalized or absolute box coordinates,
  depending on which key set is present in the JSON objects.

## What counts as a valid record

Before writing a TFRecord, the reader must yield a record with:

- `width`, `height`, `depth`
- `filename`
- `image_raw`
- at least one `gt_boxes` entry
- each box containing `label`, `xmin`, `ymin`, `xmax`, and `ymax`

## What to read next

- `references/workflows.md` for command shapes.
- `references/troubleshooting.md` for the most common layout errors.
- `scripts/validate_dataset_layout.py` to check a candidate layout safely.
