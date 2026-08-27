# Data formats

This sub-skill covers the shared dataset layouts used by Maestro before any model-specific formatting happens.

## JSONL datasets

A Maestro JSONL dataset is split into three directories:

```text
dataset/
├── train/
│   ├── annotations.jsonl
│   └── image files...
├── valid/
│   ├── annotations.jsonl
│   └── image files...
└── test/
    ├── annotations.jsonl
    └── image files...
```

### Required record keys

Each JSON line must include:

- `image`: image file name or relative path inside the split directory.
- `prefix`: prompt text sent to the model.
- `suffix`: expected model response.

Example:

```json
{"image":"image1.jpg","prefix":"What is in the image?","suffix":"box"}
```

### Loading behavior

- `JSONLDataset` reads `annotations.jsonl` line by line.
- Bad JSON lines are skipped with warnings.
- Records missing required keys are skipped with warnings.
- Records whose image file is missing are skipped with warnings.
- The dataset object only keeps valid entries, so a broken file can silently shrink the sample count.

### Split requirement

`create_data_loaders()` requires all three split directories:

- `train`
- `valid`
- `test`

If any one is missing, the function raises `ValueError` instead of returning partial loaders.

## COCO datasets

A Maestro COCO dataset uses the same three-split layout, but each split stores `_annotations.coco.json` instead of JSONL:

```text
dataset/
├── train/
│   ├── _annotations.coco.json
│   └── image files...
├── valid/
│   ├── _annotations.coco.json
│   └── image files...
└── test/
    ├── _annotations.coco.json
    └── image files...
```

### Required COCO keys

The top-level COCO annotation file must include:

- `images`
- `annotations`
- `categories`

`COCODataset` delegates parsing to `supervision` and skips images that are missing on disk.

### COCO-to-VLM adaptation

`COCOVLMAdapter` wraps a `COCODataset` and calls two formatter callbacks:

- `prefix_formatter(boxes, class_ids, class_names, image_size)`
- `suffix_formatter(boxes, class_ids, class_names, image_size)`

Both callbacks receive:

- `boxes`: `numpy.ndarray` of `xyxy` boxes
- `class_ids`: `numpy.ndarray` of integer class ids
- `class_names`: list of class names
- `image_size`: `(width, height)`

`create_data_loaders()` requires both callbacks whenever it detects COCO input.

## Roboflow identifiers

`parse_roboflow_identifier()` accepts these forms:

- `workspace/project`
- `workspace/project/version`
- `https://universe.roboflow.com/workspace/project`
- `https://app.roboflow.com/workspace/project/version`
- `roboflow.com/workspace/project`

The protocol and domain are optional. The version segment is optional. The version must be an integer if present.

Invalid forms include:

- fewer than two path segments
- more than three path segments
- a non-integer version segment

### Roboflow download mapping

`resolve_dataset_path()` uses this project-type mapping:

- `object-detection` → `coco`
- `text-image-pairs` → `jsonl`

If the input string already points to a local path, the function returns it unchanged.
If the input is remote, `ROBOFLOW_API_KEY` must be present before Maestro can download the dataset.

## Recommended preflight

Before training or inference:

1. Validate JSONL structure with `scripts/validate_jsonl_dataset.py`.
2. Use `resolve_dataset_path()` only after deciding whether the path is local or Roboflow-based.
3. For COCO data, verify that your formatter callbacks are ready before calling `create_data_loaders()`.
4. Keep model-specific prompt formatting in the sibling model sub-skills.
