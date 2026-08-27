# Inference API and workflow reference

This is a bundled, source-derived reference for the legacy inference surface.
It intentionally contains no checkout-dependent commands beyond the names of
legacy entry points whose help can be inspected when a researcher has a local
copy. The runtime helper in `scripts/infer_image.py` is the portable image
entry point.

## Exact public signatures

The inference API module defines these call shapes:

```python
init_detector(config, checkpoint=None, device='cuda:0')
inference_detector(model, img)
async_inference_detector(model, img)  # async coroutine
show_result(img, result, class_names, score_thr=0.3, wait_time=0,
            show=True, out_file=None)
show_result_pyplot(img, result, class_names, score_thr=0.3,
                   fig_size=(15, 10))
show_result_ins(img, result, class_names, score_thr=0.3,
                sort_by_density=False, out_file=None)
```

`config` may be a filename or an `mmcv.Config`; anything else raises
`TypeError`. The checkpoint is optional at the API level, but a model without
weights is not a meaningful pretrained inference run. `img` is an image path
or a loaded NumPy/BGR image array. The implementation is effectively
single-sample: it collates one item and scatters it to the device selected from
the first model parameter.

### Initialization semantics

`init_detector` does the following in order:

1. Reads a filename with `mmcv.Config.fromfile`, or accepts an `mmcv.Config`.
2. Sets `config.model.pretrained = None` so an inference initialization does
   not separately load a backbone pretrain declared by the config.
3. Builds the detector with `config.model` and `config.test_cfg`.
4. Loads the checkpoint if supplied. If checkpoint metadata contains `CLASSES`,
   those names are assigned to `model.CLASSES`; otherwise it warns and uses
   COCO class names.
5. Attaches the config as `model.cfg`, moves the model to `device`, and calls
   `model.eval()`.

A checkpoint and config from a different detector family can load partially or
fail with a state-dict/shape error. Treat that as a pairing error, not as a
reason to edit the checkpoint or silently switch the config.

### Synchronous pipeline

`inference_detector(model, img)` copies the configured test pipeline, replaces
its first image-loading transform with the API's `LoadImage`, applies the
remaining transforms, collates one sample, scatters it to the model device,
and calls:

```python
model(return_loss=False, rescale=True, **data)
```

The configured test pipeline therefore controls resize, normalization, padding,
format conversion, and metadata. A loaded BGR array is accepted and avoids
re-reading the same frame, but it must be a valid image array. The API does not
accept a video filename as a video stream abstraction.

### Async pipeline

`async_inference_detector(model, img)` mirrors the synchronous preprocessing,
then disables gradients and awaits `model.aforward_test(rescale=True, **data)`.
The repository's async documentation restricts this interface to Python 3.7+
and demonstrates it with `asyncio`, CUDA streams, and a concurrency context.
The model's async forward path supports one augmentation and asserts one image
per GPU; augmented async inference is not a fallback path. Use async only when
an application already has an explicit event-loop/stream design. For one image,
the synchronous helper is simpler and safer.

## Output shapes and interpretation

### Conventional detector and mask detector

For a standard bbox detector, `result` is a list indexed by class. Each item
is commonly an `N x 5` NumPy array with `[x1, y1, x2, y2, score]`. A two-stage
mask detector returns `(bbox_result, segm_result)`, where `bbox_result` has the
per-class arrays and `segm_result` is the corresponding per-class mask list.
`show_result` accepts either this tuple or a bbox-only list.

The bbox score is the last column. `show_result` creates labels by repeating a
class index for each per-class row, then passes boxes/labels to MMCV's bbox
renderer. With a mask tuple it decodes masks and overlays only boxes whose
score exceeds `score_thr`.

### SOLO-family instance segmentation

SOLO-family single-stage instance detectors call their head's `get_seg` and
return a one-image list. Its non-empty item is:

```text
(seg_masks, cate_labels, cate_scores)
```

where `seg_masks` is a boolean mask tensor after configured mask thresholding
and resizing, `cate_labels` is a tensor of zero-based class indices, and
`cate_scores` is the score after the head's filtering/NMS. The item may instead
be `None` when no candidate survives, so callers must handle `result == [None]`
or equivalent empty output.

For the legacy SOLO head, configured test values such as `score_thr`,
`mask_thr`, `update_thr`, `nms_pre`, `kernel`, `sigma`, and `max_per_img` affect
which masks reach the API result. `show_result_ins` applies a second
visualization score filter, resizes masks to the loaded image dimensions,
optionally sorts by mask density, overlays colors, and writes with MMCV. It
expects the SOLO-style tuple rather than a conventional bbox/mask tuple.

A visual result is not a metric. For reproducible comparisons, record the
checkpoint, config, class names, score threshold, test settings, input image,
and output renderer.

## Image, video, and image-stream recipes

### One image, headless

```python
from mmdet.apis import init_detector, inference_detector, show_result

model = init_detector('model.py', 'model.pth', device='cuda:0')
result = inference_detector(model, 'image.jpg')
show_result('image.jpg', result, model.CLASSES, show=False,
            score_thr=0.3, out_file='image.result.jpg')
```

For SOLO-style outputs, replace `show_result` with
`show_result_ins(..., out_file=...)`. Do not use a GUI just to verify that the
API works.

### Video or image stream

The documented pattern is to create one model, iterate decoded BGR frames from
an `mmcv.VideoReader` or another trusted decoder, call `inference_detector`
for each frame, and render each frame. Use `show_result(frame, ..., wait_time=1)`
only when an interactive display is intentionally available. For headless
runs, set `show=False` and provide a unique output filename per frame. The
bundled helper handles images only; it does not open a video, camera, or GUI.

### Webcam boundary

The legacy webcam demo parses a config, checkpoint, integer CUDA device, camera
id, and score threshold, then opens `cv2.VideoCapture`, reads frames, calls
inference, displays a window, and exits on Escape or `q`/`Q`. This is a
hardware/GUI side effect and is not a safe default. Before attempting it,
confirm a camera, display server, OpenCV GUI build, CUDA model, and a manual
stop path. A parser/help check is the only native candidate here; do not run it
as an automated verification case.

## Instance-segmentation CLI flags

These are the flags in the legacy instance-segmentation evaluation entry point.
They are reference-only because the command requires a configured dataset and
a checkpoint; no data download or evaluation should be started by this skill.

| Argument | Meaning and safe-use note |
|---|---|
| `config checkpoint` | Required positional test config and local weights. |
| `--out FILE` | Pickle output; must end in `.pkl` or `.pickle`. |
| `--json_out PREFIX` | COCO JSON prefix; a trailing `.json` is stripped. |
| `--eval TYPE ...` | One or more of `proposal`, `proposal_fast`, `bbox`, `segm`, `keypoints`. |
| `--show` | Display results; needs a GUI and is unsafe for headless automation. |
| `--gpu_collect` | Distributed GPU result collection; requires a distributed CUDA run. |
| `--tmpdir DIR` | Temporary directory for distributed CPU collection. |
| `--launcher` | `none`, `pytorch`, `slurm`, or `mpi`; non-`none` starts distributed behavior. |
| `--local_rank INT` | Local distributed rank; copied into `LOCAL_RANK` if absent. |

The script asserts that at least one of `--out`, `--show`, or `--json_out` is
provided. It sets `cfg.model.pretrained = None` and test mode, builds the test
dataset/data loader, loads the checkpoint to CPU first, then uses GPU 0 for the
non-distributed `MMDataParallel` path. Do not interpret `--out` as a safe
single-image prediction file: it stores dataset results and may trigger
COCO evaluation when `--eval` is provided.

The source-era visualization entry point exposes the same positional
config/checkpoint and largely the same output/evaluation/distributed flags,
plus:

| Argument | Meaning and safe-use note |
|---|---|
| `--score_thr FLOAT` | Visualization threshold, default `0.3`. |
| `--save_dir DIR` | Directory for per-dataset visualized JPEGs; create/inspect it explicitly. |

Its visualization path converts normalized tensors with `tensor2imgs`, uses
COCO class names, and writes numbered images. It asserts non-distributed use
in the main path, but still constructs a dataset and requires checkpoint/data;
use `--help` only for a safe CLI smoke.

## Safe checks

- Import/signature smoke: import the public names and inspect `help()` or
  `inspect.signature` without constructing a model.
- CLI help: run the selected installation's reviewed legacy instance-evaluation
  and visualization entry points with `--help`. Help parsing does not validate
  custom ops, checkpoint compatibility, dataset paths, or CUDA inference.
- Local image case: from the generated skill root, run
  `sub-skills/inference/scripts/infer_image.py` only with an already-present
  config, checkpoint, and tiny local image. Never add a download step.
- The repository's forward smoke remains a final CUDA-required/optional
  candidate; CPU skips or pure model construction do not certify custom CUDA
  kernels.
