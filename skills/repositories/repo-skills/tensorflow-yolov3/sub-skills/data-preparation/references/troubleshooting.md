# Troubleshooting

## Common failures and fixes

| Symptom | Likely cause | What to do |
|---|---|---|
| `validate_yolo_annotations.py` reports a row with no boxes | The converted row lost every object or the file has a blank image-only row | Regenerate the row or delete the bad row. The validator is stricter than the dataset loader so that empty rows do not hide conversion mistakes. |
| `invalid box geometry` or a training-time `nan` issue | `xmin/xmax` or `ymin/ymax` are swapped, equal, or otherwise malformed | Fix the source XML or annotation row. `core.dataset.Dataset` drops zero-area boxes, but you should not rely on that during cleanup. |
| `class id out of range` or a one-hot index error in dataset preparation | The class file and annotation ids do not match | Make sure the annotation ids are zero-based and that `cfg.YOLO.CLASSES` points to the correct `*.names` file. |
| `image does not exist` during parsing | The annotation row points at a stale path or you are validating from the wrong root | Re-run with `--check-images --image-root <DATA_ROOT>` or regenerate the annotation list with portable paths. |
| Anchor parsing or reshape failures | The anchor file is not a single line of 18 numeric values | Keep the default anchor file format or replace it with a file that still reshapes to `(3, 3, 2)`. |
| `voc_annotation.py` writes fewer rows than expected | Wrong VOC tree, missing split files, missing XMLs, or `difficult=1` objects being skipped | Check `ImageSets/Main/*.txt`, the XML contents, and whether the labels are actually VOC classes. |
| Importing helper code from a neutral working directory fails on `./data/classes/coco.names` | Relative paths in config or defaults are resolving against the wrong current directory | Run helper scripts from the repository root or pass explicit paths into your own tooling. |
| The train annotation file looks smaller than the source dataset | Blank lines were skipped or image-only rows were filtered out | Use the bundled validator to find rows that were accidentally left empty. |

## Validation strategy

When the data looks suspicious, validate in this order:

1. Class file.
2. Anchor file.
3. Annotation rows.
4. Optional image existence.

That sequence catches the most common failures before the dataset loader gets involved.

## Notes on the bundled parser

- `Dataset.parse_annotation` raises immediately when an image path is missing.
- Box coordinates are clipped after preprocessing, so a badly formed file can appear to work while still damaging training quality.
- `core.utils.read_class_names` and `core.utils.get_anchors` are simple file readers; they will not repair a bad file for you.

The safe rule is simple: fix the data first, then let the repo loaders consume it.
