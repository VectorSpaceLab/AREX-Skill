# Model Family and Task Troubleshooting

Use this when a model/task choice fails, the CLI rejects arguments, or result fields do not match what downstream code expects.

## Import and Installation Failures

### `ImportError: No module named ultralytics`

Install the public package in the active Python environment:

```bash
python -m pip install ultralytics
```

Then verify only the public import surface without loading weights:

```bash
python - <<'PY'
import ultralytics
from ultralytics import YOLO, YOLOWorld, YOLOE, NAS, SAM, FastSAM, RTDETR
print(ultralytics.__version__)
PY
```

Do not paste local virtualenv, conda prefix, or checkout paths into reusable instructions.

### Optional dependency failures

- `NAS` may require `super_gradients` when loading model names without a `.pt` suffix.
- SAM3 text concept workflows may fail if the wrong `clip` package is installed. The docs identify `TypeError: 'SimpleTokenizer' object is not callable` and recommend replacing `clip` with Ultralytics' CLIP package.
- RT-DETR requires `torch>=1.11`.
- Export or backend-specific work may require additional packages; route those to `../export-and-deployment/`.

## CLI Argument Shape

The CLI uses `yolo TASK MODE arg=value`. Avoid shell-flag style unless a documented command explicitly supports it.

Correct:

```bash
yolo detect predict model=yolo26n.pt source=path/to/image.jpg imgsz=640 device=cpu save=False
```

Incorrect patterns to rewrite:

```bash
yolo --task detect --mode predict --model yolo26n.pt
yolo predict yolo26n.pt path/to/image.jpg
```

If the task is omitted, Ultralytics can often infer it from model names, but explicit task is safer when filenames are custom or ambiguous:

```bash
yolo semantic predict model=custom-semantic-best.pt source=path/to/image.jpg
```

## Wrong Result Field

### Semantic segmentation routed as instance segmentation

Symptom: downstream code expects `result.boxes`, `result.masks.xy`, tracking IDs, or per-object confidences but the model is `yolo26n-sem.pt` or task is `semantic`.

Fix: semantic segmentation returns one dense class map in `result.semantic_mask`; it is not an object tracking/boxes workflow by default. Use `segment` with a `-seg` model for object masks, or add a separate post-processing step outside this sub-skill if dense maps must become objects.

### Instance segmentation routed as semantic segmentation

Symptom: user needs individual object masks, counts, or crop polygons but selected `task=semantic`.

Fix: use `task=segment`, a `-seg` model, and read `result.masks` plus `result.boxes`.

### OBB code reads ordinary boxes

Symptom: rotated boxes appear missing, or angle data is unavailable.

Fix: OBB uses `result.obb`, with fields such as `xywhr` and polygon-like accessors. Do not treat it as ordinary `result.boxes`.

### Classification used for localization

Symptom: code expects object coordinates from `-cls` models.

Fix: classification returns `result.probs`; choose `detect`, `segment`, `pose`, or `obb` for object locations.

## Bad Model Filename or Task Suffix

Use these suffix cues:

- `-seg`: instance segmentation.
- `-sem`: semantic segmentation.
- `-cls`: classification.
- `-pose`: pose estimation.
- `-obb`: oriented bounding boxes.
- no task suffix: usually detection for YOLO.
- `-world`/`-worldv2`: YOLO-World detection.
- `yoloe-...`: YOLOE detection/segmentation depending on config/weights.

If a custom weight name hides the task, pass `task=` in Python or choose the CLI task explicitly.

## Prompt and Open-Vocabulary Mistakes

### YOLO-World expected to output masks

`YOLOWorld` is open-vocabulary detection. It returns boxes/classes/confidences. For open-vocabulary masks, consider `YOLOE` segmentation weights or SAM3 concept segmentation.

### YOLOE visual prompts assertion error

`YOLOE.predict(..., visual_prompts=...)` expects both `bboxes` and `cls`, with the same number of entries. Example:

```python
visual_prompts = {"bboxes": [[10, 20, 100, 200]], "cls": ["hard hat"]}
```

### SAM3 text prompt routed to plain SAM call

SAM3 text concept examples use `SAM3SemanticPredictor`. Plain `SAM("sam3.pt")` is still useful for SAM-style segmentation, but concept text prompts should use the semantic predictor interface.

### SAM3 weights not found

SAM3 docs state that `sam3.pt` is not automatically downloaded. Obtain approved weights separately and point `model=` to that file. Do not assume normal Ultralytics asset auto-download will fetch SAM3.

## Data and Config Path Problems

This sub-skill only selects family/task. If errors mention missing `data=`, image directories, label formats, YAML keys, train/val splits, or dataset masks, route to `../data-and-configuration/`.

Fast triage:

- `data=` should be a dataset YAML or classification root appropriate for the selected task.
- `source=` should point to an image, video, directory, stream, URL, tensor, PIL image, or supported list depending on inference mode.
- Semantic segmentation datasets need dense mask images/class maps, not YOLO polygon labels.
- Instance segmentation datasets need polygon/segment labels, not semantic class-map PNGs.

## Device, Backend, and Resource Problems

- Use `device=cpu` for safe smoke predictions when GPU availability is unknown.
- Reduce `imgsz` for memory-constrained checks; tests use small sizes such as `imgsz=32` for smoke behavior, but production quality requires appropriate resolution.
- Semantic segmentation can be memory-heavy on small devices; repository tests skip semantic checks on Raspberry Pi.
- RT-DETR and SAM-family models can be heavier than small YOLO models. Choose YOLO nano/small weights for constrained devices.
- Export/runtime backend errors belong in `../export-and-deployment/` after selecting the model family.

## Download, Network, and Side Effects

Official model names may trigger automatic weight downloads on first use. Avoid downloads while only deciding a family/task:

```bash
python scripts/model_family_lookup.py --cue "open vocabulary boxes"
```

When running examples, set safe output controls where practical:

```bash
yolo detect predict model=yolo26n.pt source=path/to/image.jpg device=cpu save=False
```

Avoid accidentally launching expensive operations:

- `train` can run for many epochs and write experiment directories.
- `export` can install/check backend packages and write model artifacts.
- `track` can process long media and may need tracker config or ReID assets.
- webcam integer sources can open local devices.

Route those workflows to their owning sibling sub-skills after model selection.
