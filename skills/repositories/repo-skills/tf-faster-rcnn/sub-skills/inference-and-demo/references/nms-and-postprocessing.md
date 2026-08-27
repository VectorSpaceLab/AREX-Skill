# NMS and Postprocessing

The inference path has two layers of suppression/postprocessing:

1. `lib/model/test.py` turns an image into a blob, runs the network, rescales boxes back to the original image size, and applies bbox regression.
2. `tools/demo.py` or `tools/test_net.py` then applies non-maximum suppression and a score threshold to the per-class detections.

## Image and box flow

- `utils/blob.py` subtracts `cfg.PIXEL_MEANS` from BGR images and packs them into a 4D blob.
- `model.test.im_detect` expects a single BGR image array and asserts that only one image scale is active.
- The returned `boxes` are rescaled back into input-image coordinates before class-wise filtering.
- If `cfg.TEST.BBOX_REG` is enabled, `bbox_transform_inv` and `clip_boxes` run before the final per-class NMS step.

## Demo thresholds

The demo script hardcodes:

- `CONF_THRESH = 0.8`
- `NMS_THRESH = 0.3`

These values are not exposed as CLI flags in `tools/demo.py`.
Changing them requires editing the script or making a local copy.

## Repository NMS defaults

From `lib/model/config.py`:

- `cfg.USE_GPU_NMS = True`
- `cfg.TEST.NMS = 0.3`
- `cfg.TEST.MODE = 'nms'`

`cfg.TEST.MODE = 'top'` is the alternate proposal-selection path; it is not the demo default.

## Dispatch caveat

`lib/model/nms_wrapper.py` imports both `nms.gpu_nms` and `nms.cpu_nms` at module import time.
That means:

- `cfg.USE_GPU_NMS=False` only changes which function is called.
- It does **not** prevent the `nms.gpu_nms` import from being attempted.
- A missing `nms.gpu_nms` module is therefore an installation/build issue, not a config-only issue.

If the import fails, route the problem to `../installation-and-configuration/SKILL.md`.

## Expected detection shape

The post-NMS path works with arrays shaped like:

- `N x 5` for `[x1, y1, x2, y2, score]`
- `all_boxes[class_index][image_index]` for dataset evaluation in `test_net.py`

`tools/demo.py` applies per-class NMS to one image at a time and then visualizes the surviving rows.

## Visualization expectations

- `tools/demo.py` uses matplotlib and its own `vis_detections` helper.
- `lib/utils/visualization.py` is for TensorBoard GT summaries, not for demo display.
- `draw_bounding_boxes` expects the batch-first image tensor used by `Network._add_gt_image()`.
- That training-summary path expects RGB order after the OpenCV-to-RGB conversion in `Network._add_gt_image()`.

## When to switch to the evaluation sub-skill

If the task is no longer about per-image demo inference but about dataset-wide metrics, `detections.pkl`, or `imdb.evaluate_detections`, move to `training-and-evaluation`.
