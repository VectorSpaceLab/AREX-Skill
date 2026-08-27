# X-AnyLabeling Conversion CLI Reference

This reference distills the verified `xanylabeling convert` registry and `LabelConverter` API for package `x-anylabeling-cvhub` 4.0.2. The prepared CPU environment verified package import, the `xanylabeling` CLI, a 19-task conversion registry, and ONNX Runtime CPU availability. CUDA, TensorRT, model downloads, and training are not required for these conversion workflows and were not verified here.

## CLI Shape

```bash
xanylabeling convert                          # list all conversion tasks
xanylabeling convert --task <task>            # show task-specific help
xanylabeling convert --task <task> [options]  # run conversion
```

Common options:

| Option | Meaning |
|---|---|
| `--task <name>` | Conversion task id, for example `yolo2xlabel` or `xlabel2coco`. |
| `--images <dir>` | Image directory. Directory scanning is non-recursive. |
| `--labels <path>` | Label directory or label file, depending on task. For several image-paired tasks this defaults to `--images` when omitted. |
| `--output <path>` | Output directory for most tasks; `xlabel2vlmr1` expects a JSONL file path. Some tasks default this path when omitted, but explicit output is safer. |
| `--classes <file>` | One class name per line, 0-indexed. Required for YOLO detect/segment/OBB, COCO detect/segment, MOT/MOTS, and ODVG export. |
| `--pose-cfg <file>` | YAML pose config. Required for YOLO/COCO pose modes instead of `--classes`. |
| `--mode <mode>` | Mode for tasks with modes, such as `detect`, `segment`, `obb`, `pose`, `rec`, or `kie`. |
| `--mapping <file>` | JSON mask mapping table for `mask2xlabel` and `xlabel2mask`. |
| `--skip-empty-files` | Only supported by `xlabel2yolo` and `xlabel2voc`; prevents empty output files for images without annotations. |

## Registry Summary

### Import to XLABEL

| Task | Modes | Required inputs | Conditional inputs | Notes |
|---|---:|---|---|---|
| `yolo2xlabel` | `detect`, `segment`, `obb`, `pose` | `--images`, `--labels`, `--output`, `--mode` | `--classes` for `detect`/`segment`/`obb`; `--pose-cfg` for `pose` | Creates one `.json` per matched image/label pair. If `--labels` or `--output` is omitted, the implementation can default to the image directory; explicit paths are recommended. |
| `voc2xlabel` | `detect`, `segment` | `--labels`, `--output`, `--mode` | none | Reads `.xml` files from the label directory. XML `filename` and `size` drive XLABEL image metadata. |
| `coco2xlabel` | `detect`, `segment`, `pose` | `--labels`, `--output`, `--mode` | `--classes` for `detect`/`segment`; `--pose-cfg` for `pose` | `--labels` is a COCO `.json` file, not a directory. |
| `dota2xlabel` | none | `--images`, `--output` | none | Uses `.txt` DOTA label files from `--labels` if supplied, otherwise the image directory. |
| `mot2xlabel` | none | `--labels`, `--images`, `--output`, `--classes` | none | `--labels` points to the MOT annotation text file such as `gt.txt`; `--images` points to video frames. |
| `ppocr2xlabel` | `rec`, `kie` | `--labels`, `--images`, `--output`, `--mode` | none | `--labels` is a PaddleOCR label text file. |
| `mask2xlabel` | none | `--images`, `--output`, `--mapping` | none | Mask files are resolved by image stem from `--labels` when supplied, otherwise from `--images`. `.png` is checked first, then `.jpg`. |
| `vlmr12xlabel` | none | `--images`, `--output` | none | Reads one text/JSON-ish label file per image stem from `--labels` if supplied, otherwise from `--images`. |
| `odvg2xlabel` | none | `--labels`, `--output` | none | `--labels` is an ODVG JSONL file containing per-image detection instances. |

### Export from XLABEL

| Task | Modes | Required inputs | Conditional inputs | Notes |
|---|---:|---|---|---|
| `xlabel2yolo` | `detect`, `segment`, `obb`, `pose` | `--images`, `--labels`, `--output`, `--mode` | `--classes` for `detect`/`segment`/`obb`; `--pose-cfg` for `pose` | `--labels` defaults to `--images` if omitted. Supports `--skip-empty-files`. CLI maps modes to API modes `hbb`, `seg`, `obb`, `pose`. |
| `xlabel2voc` | `detect`, `segment` | `--images`, `--labels`, `--output`, `--mode` | none | Supports `--skip-empty-files`. Detection exports rectangles; segmentation mode also writes polygon elements for polygon shapes. |
| `xlabel2coco` | `detect`, `segment`, `pose` | `--images`, `--labels`, `--output`, `--mode` | `--classes` for `detect`/`segment`; `--pose-cfg` for `pose` | Writes `coco_detection.json`, `coco_instance_segmentation.json`, or `coco_keypoints.json`. |
| `xlabel2dota` | none | `--images`, `--labels`, `--output` | none | Exports rotation shapes only. Out-of-bounds rotation points are skipped. |
| `xlabel2mask` | none | `--images`, `--labels`, `--output`, `--mapping` | none | Exports `.png` semantic masks from polygon shapes using grayscale or RGB mapping. |
| `xlabel2mot` | none | `--labels`, `--output`, `--classes` | none | `--labels` is a directory of XLABEL JSON files. Writes `seqinfo.ini`, `det.txt`, and `gt.txt`. |
| `xlabel2mots` | none | `--labels`, `--output`, `--classes` | none | `--labels` is a directory of XLABEL JSON files. Writes `seqinfo.ini` and `custom_gt.txt`; requires polygon shapes. |
| `xlabel2odvg` | none | `--images`, `--labels`, `--output`, `--classes` | none | Writes `label_map.json` and `od.json` in the output directory. |
| `xlabel2vlmr1` | none | `--images`, `--labels`, `--output` | optional `--classes` at API level is not exposed by the CLI parser for this task | `--output` must be a JSONL file path. Images with no labels are skipped when no class filter is loaded. |
| `xlabel2ppocr` | `rec`, `kie` | `--images`, `--labels`, `--output`, `--mode` | none | Rec mode writes `Label.txt`, `rec_gt.txt`, and `crop_img/`; KIE mode writes `ppocr_kie.json` and a sorted `class_list.txt` when labels are found. |

## Canonical Command Recipes

### YOLO detection to XLABEL

```bash
xanylabeling convert \
  --task yolo2xlabel \
  --mode detect \
  --images ./images \
  --labels ./labels \
  --output ./xlabel \
  --classes ./classes.txt
```

### XLABEL to YOLO segmentation, skipping missing/empty labels

```bash
xanylabeling convert \
  --task xlabel2yolo \
  --mode segment \
  --images ./images \
  --labels ./xlabel \
  --output ./labels-yolo \
  --classes ./classes.txt \
  --skip-empty-files
```

### YOLO pose to XLABEL

```bash
xanylabeling convert \
  --task yolo2xlabel \
  --mode pose \
  --images ./images \
  --labels ./labels \
  --output ./xlabel \
  --pose-cfg ./pose.yaml
```

The pose YAML root must be a mapping with a non-empty `classes` mapping. `has_visible` defaults to `true` when omitted.

### XLABEL pose to COCO keypoints

```bash
xanylabeling convert \
  --task xlabel2coco \
  --mode pose \
  --images ./images \
  --labels ./xlabel \
  --output ./annotations \
  --pose-cfg ./pose.yaml
```

Every pose instance in XLABEL should have a rectangle carrying the object class and point shapes carrying keypoint names. The rectangle and all points for one instance must share the same integer-like `group_id`.

### VOC XML to XLABEL

```bash
xanylabeling convert \
  --task voc2xlabel \
  --mode detect \
  --labels ./Annotations \
  --output ./xlabel
```

For segmentation-style VOC XML, use `--mode segment`; polygon objects become XLABEL polygons and bounding boxes remain rectangles.

### COCO detection JSON to XLABEL

```bash
xanylabeling convert \
  --task coco2xlabel \
  --mode detect \
  --labels ./annotations/instances.json \
  --output ./xlabel \
  --classes ./classes.txt
```

### DOTA to XLABEL and back

```bash
xanylabeling convert --task dota2xlabel --images ./images --labels ./labelTxt --output ./xlabel
xanylabeling convert --task xlabel2dota --images ./images --labels ./xlabel --output ./labelTxt-out
```

DOTA lines use `x1 y1 x2 y2 x3 y3 x4 y4 class_name difficult`.

### Mask to XLABEL and back

```bash
xanylabeling convert \
  --task mask2xlabel \
  --images ./images \
  --labels ./masks \
  --output ./xlabel \
  --mapping ./mask_map.json

xanylabeling convert \
  --task xlabel2mask \
  --images ./images \
  --labels ./xlabel \
  --output ./masks-out \
  --mapping ./mask_map.json
```

The mapping file is JSON:

```json
{"type": "grayscale", "colors": {"cat": 1, "dog": 2}}
```

or:

```json
{"type": "rgb", "colors": {"cat": [255, 0, 0], "dog": [0, 255, 0]}}
```

### MOT / MOTS

```bash
xanylabeling convert \
  --task mot2xlabel \
  --labels ./gt.txt \
  --images ./frames \
  --output ./xlabel \
  --classes ./classes.txt

xanylabeling convert --task xlabel2mot --labels ./xlabel --output ./mot-out --classes ./classes.txt
xanylabeling convert --task xlabel2mots --labels ./xlabel --output ./mots-out --classes ./classes.txt
```

MOT uses rectangle shapes and `group_id` as track id. MOTS uses polygon shapes and `group_id` as track id.

### PaddleOCR rec/KIE

```bash
xanylabeling convert --task ppocr2xlabel --mode rec --labels ./Label.txt --images ./images --output ./xlabel
xanylabeling convert --task xlabel2ppocr --mode rec --images ./images --labels ./xlabel --output ./ppocr-rec
xanylabeling convert --task xlabel2ppocr --mode kie --images ./images --labels ./xlabel --output ./ppocr-kie
```

Rec mode exports cropped word images for recognition training. KIE mode preserves labels, `group_id`, and `kie_linking` when present.

### ODVG and VLM-R1-OVD

```bash
xanylabeling convert --task odvg2xlabel --labels ./od.jsonl --output ./xlabel
xanylabeling convert --task xlabel2odvg --images ./images --labels ./xlabel --output ./odvg --classes ./classes.txt

xanylabeling convert --task vlmr12xlabel --images ./images --labels ./vlmr1-labels --output ./xlabel
xanylabeling convert --task xlabel2vlmr1 --images ./images --labels ./xlabel --output ./vlmr1.jsonl
```

`xlabel2vlmr1` writes JSONL conversation records whose assistant answer embeds detected boxes. `vlmr12xlabel` accepts content that can be parsed as a list of `{"bbox_2d": [x1, y1, x2, y2], "label": "..."}` objects, either directly or inside an `<answer>...</answer>` span.

## Python API Signatures

Verified signatures:

```python
LabelConverter(classes_file=None, pose_cfg_file=None)

LabelConverter.yolo_to_custom(input_file, output_file, image_file, mode)
LabelConverter.yolo_obb_to_custom(input_file, output_file, image_file)
LabelConverter.yolo_pose_to_custom(input_file, output_file, image_file)
LabelConverter.custom_to_yolo(input_file, output_file, mode, skip_empty_files=False, obb_boundary_policy="skip")

LabelConverter.voc_to_custom(input_file, output_file, image_filename, mode)
LabelConverter.coco_to_custom(input_file, output_dir_path, mode)
LabelConverter.custom_to_coco(image_list, input_path, output_path, mode)

LabelConverter.mask_to_custom(input_file, output_file, image_file, mapping_table)
LabelConverter.custom_to_mask(input_file, output_file, mapping_table)

LabelConverter.ppocr_to_custom(input_file, output_path, image_path, mode)
LabelConverter.custom_to_ppocr(image_file, label_file, save_path, mode)

run_conversion(task, images=None, labels=None, output=None, classes_file=None,
               pose_cfg_file=None, mode=None, mapping_file=None,
               skip_empty_files=False)
```

Mode values for API calls are slightly different from CLI values in a few places:

| CLI mode | API mode used internally |
|---|---|
| `yolo2xlabel --mode detect` | `yolo_to_custom(..., mode="hbb")` |
| `yolo2xlabel --mode segment` | `yolo_to_custom(..., mode="seg")` |
| `xlabel2yolo --mode detect` | `custom_to_yolo(..., mode="hbb")` |
| `xlabel2yolo --mode segment` | `custom_to_yolo(..., mode="seg")` |
| `xlabel2yolo --mode obb` | `custom_to_yolo(..., mode="obb")` |
| `xlabel2yolo --mode pose` | `custom_to_yolo(..., mode="pose")` |
| `voc2xlabel --mode detect` | `voc_to_custom(..., mode="rectangle")` |
| `voc2xlabel --mode segment` | `voc_to_custom(..., mode="polygon")` |
| `xlabel2voc --mode detect` | `custom_to_voc(..., mode="rectangle")` |
| `xlabel2voc --mode segment` | `custom_to_voc(..., mode="polygon")` |
| COCO `detect`/`segment`/`pose` | `rectangle`/`polygon`/`pose` |

### API Example: Strict Single-File YOLO Detection Import

```python
import json
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter(classes_file="classes.txt")
converter.yolo_to_custom(
    input_file="labels/img_001.txt",
    output_file="xlabel/img_001.json",
    image_file="images/img_001.png",
    mode="hbb",
)

with open("xlabel/img_001.json", encoding="utf-8") as f:
    data = json.load(f)
assert data["shapes"] and data["shapes"][0]["shape_type"] == "rectangle"
```

### API Example: Catch Pose Association Errors

```python
from anylabeling.views.labeling.label_converter import (
    LabelConverter,
    PoseClassError,
    PoseGroupError,
)

converter = LabelConverter(pose_cfg_file="pose.yaml")
try:
    converter.custom_to_yolo("xlabel/person.json", "labels/person.txt", "pose")
except (PoseGroupError, PoseClassError) as exc:
    raise RuntimeError(
        "Fix pose group_id/class labels before exporting YOLO pose"
    ) from exc
```

## Operational Limits

- Directory scanning for images and labels is non-recursive. Flatten nested datasets or run separate conversions per directory.
- Direct non-XLABEL-to-non-XLABEL conversion is not exposed. Use XLABEL as the intermediate format.
- Some examples in CLI help rely on defaults for `--labels` or `--output`; explicit paths are more reproducible.
- The CLI imports Qt-related package modules even for conversion. Non-fatal multimedia/display warnings may appear on headless systems; they are not conversion failures unless the process exits nonzero.
