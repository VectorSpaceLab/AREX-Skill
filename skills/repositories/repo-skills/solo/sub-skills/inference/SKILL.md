---
name: inference
description: "Run safe local image, video-frame, image-stream, and
  instance-segmentation inference with SOLO's legacy MMDetection APIs, interpret
  results, and save visualizations without relying on the source checkout."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Inference

Use this sub-skill when a researcher needs to load a SOLO/MMDetection model,
run prediction on an image or already-decoded video frame, inspect the returned
objects, or save a detection/instance-segmentation visualization. This is a
PyTorch/MMDetection v1-era interface, not a modern MMDetection 2/3 recipe.

## Preconditions and scope

- Have a compatible installed package environment: the repository documents
  Python 3.5+, PyTorch 1.1+, CUDA 9+, NCCL 2, and `mmcv==0.2.16`. In practice,
  use a version-matched legacy environment rather than assuming current PyTorch
  or MMCV works.
- Have an existing local config file and checkpoint. This skill never downloads
  weights, datasets, or dependencies. Check both paths before starting.
- Prefer a CUDA device for end-to-end detector/instance-segmentation inference;
  custom CUDA ops may be needed. A CPU import or config check does **not** prove
  CUDA kernels work. `--device cpu` is useful only where the selected model and
  installed extensions support it.
- From the generated skill root, use `scripts/infer_image.py` for a
  non-interactive single image. It has no source-checkout assumptions and fails
  early when prerequisites are absent.
- Do not start a webcam, GUI window, distributed job, full evaluation, or model
  download from this route. Read `references/api-and-workflows.md` for safe
  video-frame, async, webcam boundaries, result interpretation, and the exact
  legacy evaluation flags.

## Safe single-image procedure

1. Select a config/checkpoint pair from the same model family and training
   variant. A checkpoint may carry `CLASSES`; otherwise legacy initialization
   falls back to COCO classes with a warning.
2. Confirm the image is readable and the output path is writable. Keep the
   output separate from the input.
3. Confirm the device explicitly. `cuda:0` (or another visible index) must be
   available for a CUDA run; do not infer GPU kernel support from
   `torch.cuda.is_available()` alone.
4. Run the bundled helper, for example:

   ```bash
   python sub-skills/inference/scripts/infer_image.py \
     --config MODEL_CONFIG --checkpoint MODEL_CHECKPOINT \
     --image INPUT_IMAGE --output OUTPUT_IMAGE \
     --device cuda:0 --score-thr 0.25 --visualizer auto
   ```

   `--visualizer auto` uses `show_result_ins` for SOLO-style tensor mask
   results and otherwise uses `show_result`; use `--visualizer detection` or
   `--visualizer instance` to make the choice explicit.
5. Treat a successful saved image as a visualization smoke, not an accuracy
   result. Record config, checkpoint identity, device, threshold, package
   versions, and whether custom ops loaded.

## Public API route

The public exports are `init_detector`, `inference_detector`,
`async_inference_detector`, `show_result`, `show_result_pyplot`, and
`show_result_ins` from `mmdet.apis`. The core synchronous flow is:

```python
model = init_detector(config, checkpoint, device='cuda:0')
result = inference_detector(model, image_path_or_bgr_ndarray)
show_result(image_path_or_bgr_ndarray, result, model.CLASSES,
            score_thr=0.3, show=False, out_file='result.jpg')
```

`init_detector` sets `config.model.pretrained = None`, builds with the config's
`test_cfg`, loads the optional checkpoint, attaches `model.cfg`, moves the
model to `device`, and calls `eval()`. `inference_detector` reconstructs the
configured test pipeline after replacing its first loader with `LoadImage`,
collates/scatters one sample to the model device, and calls the model with
`return_loss=False, rescale=True` under `torch.no_grad()`.

For a video or image stream, decode one BGR frame at a time and pass the frame
array to `inference_detector`; reuse one initialized model. Save frames or use
`show_result(..., show=False, out_file=...)` for headless operation. Do not
assume a video path can be passed directly to `inference_detector`; the API
accepts an image path or loaded image array, while `mmcv.VideoReader` is the
source-documented frame iterator.

## Result and visualization routing

- Standard detector output is a list of per-class bounding-box arrays, each
  usually shaped `(N, 5)` with `x1, y1, x2, y2, score`; two-stage mask models
  return `(bbox_result, segm_result)`.
- SOLO/Decoupled SOLO/SOLOv2-style instance heads return a one-image list
  containing either `None` or `(seg_masks, cate_labels, cate_scores)` tensors.
  `seg_masks` are boolean-like masks, `cate_labels` are class indices, and
  `cate_scores` are post-NMS scores. Empty predictions can therefore be
  `None`, `[None]`, or an empty structure depending on the detector.
- `show_result` handles bbox and conventional `(bbox, segm)` results and can
  return an image only when both `show=False` and `out_file=None`.
- `show_result_ins` is for SOLO-style instance tensors; it thresholds scores,
  resizes masks to the input image, overlays deterministic colors, labels each
  mask, and writes with `out_file` or returns an array when no output is given.
  It is not a universal replacement for `show_result`.
- `show_result_pyplot` creates a Matplotlib figure and is unsuitable for a
  headless or strictly non-GUI check unless the environment has a backend.

## Recovery and escalation

- Missing config/checkpoint/image: stop and provide an explicit local path;
  do not download or silently substitute a model.
- Import or symbol errors: verify the active environment has the matching
  legacy package, `mmcv==0.2.16`, PyTorch 1.1+ compatibility, `pycocotools`,
  SciPy/OpenCV, and the installed SOLO package. Check `PYTHONPATH` only as a
  temporary, explicit environment choice; do not edit source during inference.
- Device or custom-op errors: retry only after confirming the requested CUDA
  device, PyTorch/CUDA compatibility, and extension build. A CPU retry can
  distinguish Python/config issues but cannot certify CUDA inference.
- Shape/pipeline errors: use the test pipeline in the chosen config, ensure the
  image is a readable color image, and check model/checkpoint family alignment.
  Do not bypass `inference_detector`'s configured normalization, resize, pad,
  and tensor conversion without a deliberate API-level adaptation.
- Empty or visually odd output: inspect `model.CLASSES`, score thresholds,
  SOLO test settings (`score_thr`, `mask_thr`, `update_thr`, `max_per_img`),
  image color/order, and checkpoint provenance before changing code.

## Verification boundary

Safe checks are API import/signature smoke, parser-help for the selected legacy
instance-evaluation entry point, and a tiny local-image inference only when a
local checkpoint already exists. Do not run downloads, webcam capture, GUI,
full dataset evaluation, or distributed testing. The repository's forward
smoke is a CUDA-required/optional final candidate: any CPU branch is not a
substitute for custom CUDA-kernel validation. See the bundled references for
source-derived signatures and difficult usability cases.
