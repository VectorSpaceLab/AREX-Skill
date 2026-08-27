# Export Workflows

## Single Annotation File

```bash
python sub-skills/dataset-export/scripts/export_labelme_json.py \
  annotations/image.json --out outputs/image-labels
python sub-skills/dataset-export/scripts/inspect_label_png.py \
  outputs/image-labels/label.png --json
```

Outputs are `img.png`, `label.png`, optional `label_viz.png`, and
`label_names.txt`. This helper may reuse the output directory; choose a fresh
`--out` if existing artifacts must not be overwritten.

## Semantic/instance VOC

```bash
python sub-skills/dataset-export/scripts/labelme_export_voc.py \
  annotated/ voc_dataset/ --labels labels.txt
```

Use `--noobject` for semantic-only outputs, `--nonpy` to skip NumPy arrays, or
`--noviz` to skip visualization JPEGs. The input directory must contain JSON
files and the output directory must not already exist.

## Bounding-box VOC

```bash
python sub-skills/dataset-export/scripts/labelme_export_bbox_voc.py \
  annotated/ bbox_voc/ --labels labels.txt
```

Install missing converter dependencies for this workflow:

```bash
python -m pip install imgviz lxml
```

Only rectangle Shapes are emitted as VOC objects; other Shapes are reported and
skipped.

## COCO instance export

```bash
python sub-skills/dataset-export/scripts/labelme_export_coco.py \
  annotated/ coco_dataset/ --labels labels.txt
```

Install missing converter dependencies only when needed:

```bash
python -m pip install imgviz pycocotools
```

The helper creates `JPEGImages/`, optional `Visualization/`, and
`annotations.json`.

## Video frames

Convert a video to an image directory with a separate video tool, then annotate
that directory with labelme and run the same VOC/COCO directory exporters. Keep
frame JSON/image basenames aligned so downstream consumers can pair them.

## Validation after export

- Inspect `class_names.txt` and confirm class ids.
- Use `inspect_label_png.py` to check dtype/shape/unique values.
- Confirm every input Label is represented in the supplied vocabulary.
- Confirm out-of-bounds Shapes are clipped rather than unexpectedly rejected.
- Open generated JSON/XML with a consumer-specific parser before training.
