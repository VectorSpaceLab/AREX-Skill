# Inference and visualization recipes

This reference covers MMYOLO v0.6-style image/video inference, LabelMe export, large-image slicing, feature-map visualization, and BoxAM/CAM analysis. All runnable patterns use installed Python packages and bundled skill files, not source-checkout demo scripts.

## Prerequisites

- MMYOLO, MMDetection, MMCV, MMEngine, PyTorch, and the model family used by the config must be importable.
- Have a compatible MMYOLO config file and checkpoint file. Config/checkpoint mismatch is the most common cause of missing classes or incompatible head weights.
- Prefer `--device cpu` for CPU-only validation. Use `cuda:0` only when CUDA PyTorch/MMCV ops are available.
- Do not download checkpoints, images, videos, or URLs unless the user has explicitly approved that network/data access.

## Image, folder, and URL inference

The image inference semantics accept three positional inputs:

```text
<img-or-dir-or-url> <config.py> <checkpoint.pth>
```

Supported image inputs:

- Single image with extension `jpg`, `jpeg`, `png`, `ppm`, `bmp`, `pgm`, `tif`, `tiff`, or `webp`.
- Directory: recursively traversed for supported image extensions; output filenames flatten relative paths by replacing `/` with `_`.
- URL: downloaded to the current working directory by the MMYOLO utility before inference. Treat URLs as network side effects.

Core options:

| Option | Meaning |
| --- | --- |
| `--out-dir DIR` | Save visualized images or LabelMe JSON files under `DIR` when not showing interactively. |
| `--device cpu` or `--device cuda:0` | Device passed to `init_detector`. CPU is safer for portability; CUDA needs a matching backend stack. |
| `--show` | Display results interactively instead of writing normal visualized images. Do not use on headless machines. |
| `--deploy` | Switch RepVGG-style blocks in the loaded PyTorch model to deploy mode. This is not ONNX/TensorRT/MMDeploy backend inference. |
| `--tta` | Enable test-time augmentation. The config must contain both `tta_model` and `tta_pipeline`; otherwise the run should fail before inference. |
| `--score-thr FLOAT` | Confidence threshold used to keep predictions for LabelMe and to draw predictions in visualized images. |
| `--class-name NAME ...` | Validate selected class names against `model.dataset_meta['classes']`; in image-demo semantics, selected classes are applied when writing LabelMe shapes. |
| `--to-labelme` | Write one `.json` LabelMe file per image instead of rendered images. Mutually exclusive with `--show`. |

### Safe command builder

Use the bundled helper to emit a runnable shell heredoc that performs image/folder/URL inference through installed MMYOLO APIs:

```bash
python scripts/mmyolo_infer_image_command.py \
  "images/" "model_config.py" "checkpoint.pth" \
  --device cpu \
  --out-dir "pred_labelme" \
  --to-labelme \
  --class-name cat dog \
  > run_mmyolo_image_infer.sh
bash run_mmyolo_image_infer.sh
```

For visualized image output instead of LabelMe JSON:

```bash
python scripts/mmyolo_infer_image_command.py \
  "image.jpg" "model_config.py" "checkpoint.pth" \
  --device cpu \
  --score-thr 0.5 \
  --out-dir "pred_vis" \
  > run_mmyolo_image_infer.sh
bash run_mmyolo_image_infer.sh
```

The helper itself does no inference. It validates the `--show` / `--to-labelme` conflict and emits a template that imports `init_detector`, `inference_detector`, `get_file_list`, `LabelmeFormat`, and the MMYOLO visualizer from installed packages.

### Image output semantics

- Normal visualization writes images under `--out-dir` unless `--show` is set.
- LabelMe mode replaces the image suffix with `.json` and writes rectangle shapes with class labels and two corner points.
- LabelMe JSON uses `imageData: null`, records the original image width/height from prediction metadata, and uses the image path reported by the runtime metadata.
- If the input is a directory, output basenames are derived from relative input paths with path separators replaced by `_`.
- If `--class-name` is supplied, each name is case-sensitive and must exist in the model's dataset classes. Use the API recipe in [api-reference.md](api-reference.md) when you need class-filtered rendered images instead of class-filtered LabelMe shapes.

### TTA and deploy semantics

TTA modifies the loaded config before model construction:

1. Require `tta_model` and `tta_pipeline` in the config.
2. Wrap the original model config with the TTA model config.
3. Replace the final test dataset pipeline with `tta_pipeline`.
4. Remove `batch_shapes_cfg` from the resolved test dataset because it is incompatible with TTA.

`--deploy` calls MMYOLO's deploy switch on in-memory PyTorch modules after model construction. For exported engines, ONNXRuntime, TensorRT, RKNN, or MMDeploy backend artifacts, route to `deployment-conversion`.

## Video inference recipe

Video inference is reference-only here because it depends on codecs, media files, and checkpoint-backed inference. A self-contained implementation should follow this API pattern:

1. Build the model with `init_detector(config, checkpoint, device=device)`.
2. Change the first test pipeline transform to `mmdet.LoadImageFromNDArray` because frames are NumPy arrays, not image paths.
3. Compose the test pipeline with `mmcv.transforms.Compose`.
4. Read frames with `mmcv.VideoReader` or an equivalent video reader.
5. For each frame, call `inference_detector(model, frame, test_pipeline=test_pipeline)`.
6. Draw with the MMYOLO visualizer and either display frames or write an output video with OpenCV.

Validation points:

- Require at least one output mode: save to a video file or show interactively.
- Use `--score-thr` for drawn boxes.
- On headless systems, prefer writing an output video over `--show`.
- If frames are the wrong color, check BGR/RGB conversion around the visualizer/video writer boundary.

## Large-image / SAHI slicing recipe

Large-image inference slices a large image into overlapping patches, runs normal MMYOLO inference per patch, shifts patch predictions back to the original coordinate space, and merges boxes by NMS.

Optional dependency: `sahi`. Do not claim this recipe is runnable unless `sahi` imports successfully.

Key options and defaults from the MMYOLO recipe:

| Option | Purpose |
| --- | --- |
| `--patch-size 640` | Patch height and width. Lower values reduce memory but may miss large context. |
| `--patch-overlap-ratio 0.25` | Fractional overlap between neighboring patches. Higher overlap reduces boundary misses but increases runtime. |
| `--merge-iou-thr 0.25` | IoU threshold for final NMS merge. |
| `--merge-nms-type nms` | NMS type passed into MMCV batched NMS. |
| `--batch-size 1` | Number of patch images forwarded per inference call; must be at least 1. |
| `--debug` | Save a debug visualization of slice grids and shifted patch results. |
| `--save-patch` | Save per-patch result images only when debug output is enabled. |

Implementation outline:

```python
from sahi.slicing import slice_image
from mmdet.apis import inference_detector
from mmyolo.utils.large_image import merge_results_by_nms

sliced = slice_image(
    image,
    slice_height=patch_size,
    slice_width=patch_size,
    auto_slice_resolution=False,
    overlap_height_ratio=overlap_ratio,
    overlap_width_ratio=overlap_ratio,
)

patch_results = []
for start in range(0, len(sliced), batch_size):
    batch = sliced.images[start:start + batch_size]
    patch_results.extend(inference_detector(model, batch))

merged = merge_results_by_nms(
    patch_results,
    sliced.starting_pixels,
    src_image_shape=(height, width),
    nms_cfg={"type": merge_nms_type, "iou_threshold": merge_iou_thr},
)
```

## Feature-map visualization recipe

Feature-map visualization hooks one or more target layers during normal detector inference, overlays reduced feature maps on the image, and saves or shows the result.

Common target layer strings:

- `backbone`
- `neck`
- `backbone.stage3`
- `backbone.stage4`
- `neck.out_layers[0]`, `neck.out_layers[1]`, `neck.out_layers[2]`

Use a preview step first: build the model, print it, and confirm the target layer path exists. In the MMYOLO recipe, invalid layer strings raise a `layer does not exist` error after printing the model.

Feature-map controls:

| Option | Meaning |
| --- | --- |
| `--target-layers LAYER ...` | One or more model attributes to hook. |
| `--preview-model` | Print model structure and exit; use this before expensive CAM/feature runs. |
| `--channel-reduction select_max` | Select the channel with maximum spatial activation. |
| `--channel-reduction squeeze_mean` | Mean-reduce channels to one map. |
| `--channel-reduction None` | Do not reduce; use `--topk` and `--arrangement`. |
| `--topk 4` | Number of channels to show when there is no channel reduction. |
| `--arrangement R C` | Grid layout for top-k feature maps. |

Alignment caveat: YOLO test pipelines often include keep-ratio resize, letterbox padding, or pad metadata. Directly upsampled feature maps can be visually misaligned with the original image. For visualization-only analysis, use a temporary config variant whose test pipeline uses a simple resize and metadata without padding fields; do not reuse that visualization-only config for evaluation claims.

## BoxAM / Grad-CAM recipe

BoxAM and CAM visualizations are optional, checkpoint-backed analysis recipes. They are not bundled as runnable scripts here because they require `grad-cam`, target-layer choices, and potentially large memory.

Supported method names in this MMYOLO version:

- Grad-based: `gradcam`, `gradcam++`
- Grad-free: `ablationcam`, `eigencam`

Important controls:

| Option | Purpose |
| --- | --- |
| `--target-layers neck.out_layers[2]` | Default BoxAM target layer; validate with a model preview. |
| `--method gradcam` | CAM method. `ablationcam` is usually much slower. |
| `--topk -1` | Use all detections by default; set a positive value to visualize only top predictions. |
| `--score-thr 0.3` | Filter detections before CAM target creation. |
| `--max-shape -1` | Optional scaling limit to save memory; one or two integers. |
| `--norm-in-bbox` | Normalize/display activation inside predicted boxes. |
| `--batch-size` and `--ratio-channels-to-ablate` | AblationCAM-specific speed/memory controls. |

Validation workflow for a target-layer request:

1. Confirm `grad-cam` imports before planning BoxAM.
2. Build the model on the requested device and preview the module tree.
3. Resolve every requested target layer against the model before running CAM.
4. Run a low-threshold detection sanity check. If no boxes survive `--score-thr`, CAM output will be empty.
5. For memory errors, reduce image size, use `--max-shape`, lower `--topk`, or switch from AblationCAM to a grad-based method.

Known family-specific behavior: the BoxAM implementation ignores some loss terms for different YOLO families when constructing score targets. This is an internal compatibility detail, so validate on a small image before relying on CAM explanations for a new config family.

## Output validation checklist

Before treating inference/visualization output as valid, check:

- The input file list is non-empty and matches the intended images.
- Config and checkpoint correspond to the same model family/classes.
- The device actually exists and imports required ops.
- `score_thr` is in a reasonable range; very high thresholds can produce no boxes.
- Class filters are case-sensitive and present in `model.dataset_meta['classes']`.
- LabelMe mode produced one JSON per input image and each JSON has expected `shapes` entries.
- Feature-map or CAM target layers were previewed and resolved before running expensive visualization.
- Optional recipes (`sahi`, `grad-cam`, video codecs) passed dependency checks before execution.
