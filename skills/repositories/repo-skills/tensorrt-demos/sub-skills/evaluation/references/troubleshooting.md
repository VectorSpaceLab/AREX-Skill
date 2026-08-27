# Troubleshooting and blocked-help signals

Diagnose in layers. Preserve the original command, stderr, environment
versions, and whether the failure happened before image enumeration, during
inference, while writing results, or inside `COCOeval`. Do not turn an
unexecuted or partially executed run into a benchmark claim.

## Dependency and backend gates

### YOLO plugin missing

A YOLO import loads `./plugins/libyolo_layer.so` immediately. The repository's
explicit failure is equivalent to:

```text
ERROR: failed to load ./plugins/libyolo_layer.so. Did you forget to do a "make"
in the "./plugins/" subdirectory?
```

This is a truthful blocked signal, not evidence of a bad model or dataset.
Build the plugin only in an approved, compatible TensorRT/CUDA environment,
then rerun a safe import/help check before any dataset evaluation. Check the
current working directory: the loader uses the relative path
`./plugins/libyolo_layer.so`.

If the file exists but loading still fails, classify ABI/architecture or
TensorRT-version incompatibility rather than copying a host `.so` into the
skill or weakening the import. YOLO's implementation is documented for
TensorRT 6+ and uses legacy bindings.

### TensorFlow missing or incompatible for SSD

`eval_ssd.py` imports both `TrtSSD` and `TfSSD`, and `utils.ssd_tf` imports
TensorFlow at module import time. Therefore an absent TensorFlow package can
block the script before `--mode trt` is selected. Preserve the import error.
For `--mode tf`, use a TensorFlow 1.x-compatible environment and the graph/API
versions expected by the frozen `.pb` files; the README specifically advises
matching the UFF/TensorFlow 1.12-era stack for conversion, but that does not
make every modern Python/TensorFlow environment compatible.

Do not install or mutate system packages merely to clear a help check. Record
`BLOCKED_LEGACY_TENSORFLOW` when the required dependency cannot be prepared.
A successful tiny JSON check does not remove this block.

### CUDA, PyCUDA, TensorRT, OpenCV, and pycocotools

Both evaluators import `pycuda.autoinit`, so a CUDA driver/context is required.
Typical signals and actions:

- `pycuda._driver` or context initialization failure: classify as missing or
  incompatible CUDA driver/PyCUDA; do not retry with a large dataset.
- `tensorrt` import or engine deserialization failure: verify TensorRT version,
  engine provenance, bindings/API generation, and GPU architecture.
- `cv2.imread()` returning `None`: inspect file permissions, JPEG integrity, and
  the image directory; the script does not report this cleanly before detector
  code sees it.
- `No module named pycocotools`: install/prepare it in the approved evaluation
  environment; this is required for actual COCOeval, not for the bundled
  layout checker.
- `No module named progressbar`: install `progressbar2` in the approved
  environment. Do not replace progress reporting in a benchmark run without
  recording the change.

## Path and artifact failures

- `... is not a valid directory` or `... is not a valid file`: the evaluator's
  own `check_args()` rejected the path. Verify shell quoting and run from the
  intended checkout.
- SSD engine missing: `ssd/TRT_<model>.bin` is absent or not readable.
  TensorFlow mode similarly needs `ssd/<model>.pb`.
- YOLO engine missing: `ERROR: file (yolo/<model>.trt) not found!` means the
  exact `-m` string does not have a serialized engine at that path.
- A filename such as `image.jpg` with no numeric suffix causes `int(...)` to
  fail. Rename/copy into the evaluator's documented ID convention or use a
  separately tested adapter; do not silently guess IDs.
- Uppercase `.JPG`, PNG, and nested directories are not selected by the scripts.
- Results are written to `ssd/` or `yolo/`; a read-only checkout or missing
  directory can fail at serialization. Keep experiment outputs outside the
  managed skill tree and ensure the repository result directory is writable.

## Class and coordinate errors

### Low or zero AP with plausible detections

Check these before blaming FP16/INT8:

1. Result `image_id` values match annotation `images[].id`.
2. Result `category_id` values match annotation `categories[].id`.
3. YOLO standard COCO runs do **not** use `--non_coco`; the default mapping
   converts raw 0–79 class IDs to COCO IDs with gaps.
4. `--category_num` matches the engine and custom annotation vocabulary.
5. `-l` matches the model's letterbox behavior.
6. Boxes are original-image pixel coordinates in `[x, y, width, height]`, not
   normalized `[x1, y1, x2, y2]`.
7. The source images and annotations are the same split and revision.
8. The model was trained for the annotation classes; COCO engines should not
   be judged against an unrelated custom category list.

Inspect one serialized result and draw it on its source JPEG. The repository
uses inclusive-style `+1` width/height conversion from corner coordinates;
minor convention effects are different from a global x/y swap or raw-vs-COCO
category mismatch.

### Unexpected AP differences between TF and TRT SSD

Compare the same `model`, same images/annotations, and the complete summary.
The two paths use different preprocessing and inference implementations. Check
engine precision, plugin loading, TensorRT version, and whether model files
were rebuilt. A matching historical AP is a useful reference, not a hard gate
for every environment.

### YOLO letterbox behavior

Letterbox preprocessing rescales to fit while retaining aspect ratio, fills
padding with 127, and subtracts the computed offsets after detection. If the
flag is wrong, boxes can be shifted or stretched while still passing JSON
schema checks. Re-run one image with the intended mode and compare corners
before evaluating a split.

## COCOeval and result errors

- `COCO.loadRes()` errors often indicate malformed JSON, unknown image IDs,
  unknown category IDs, or invalid result structure. Run the tiny checker and
  inspect the annotation vocabulary.
- Empty results or a split with no matching detections may produce low recall
  or version-specific `pycocotools` behavior. Record the exact library version.
- A result file containing only a subset of images is not automatically a
  subset evaluation: the scripts set `cocoEval.params.imgIds` to all ground
  truth image IDs. Missing detections count against recall.
- Different AP numbers can result from a changed `pycocotools`/COCO API,
  annotation revision, result ordering, preprocessing, or engine build. Keep
  the complete `summarize()` output instead of comparing one rounded number.

## Stop and handoff labels

Use explicit labels in a report:

- `LAYOUT_BLOCKED`: tiny fixture contract failed;
- `DATASET_BLOCKED`: approved annotation/image split unavailable or inconsistent;
- `BLOCKED_YOLO_PLUGIN`: `libyolo_layer.so` missing or incompatible;
- `BLOCKED_LEGACY_TENSORFLOW`: required TF graph/runtime unavailable;
- `BLOCKED_CUDA_RUNTIME`: driver/PyCUDA/TensorRT context unavailable;
- `BLOCKED_ENGINE`: expected serialized engine or plugin artifact unavailable;
- `PARTIAL_HELP_ONLY`: CLI/parser inspection succeeded, but no inference ran;
- `EVALUATED`: full approved split ran and complete COCOeval output was saved.

Never label a run `EVALUATED` when any required backend, dataset, engine, or
semantic mapping gate remained unresolved.
