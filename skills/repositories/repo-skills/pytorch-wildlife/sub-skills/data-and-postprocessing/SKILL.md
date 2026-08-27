---
name: data-and-postprocessing
description: "Load PytorchWildlife image folders, apply inference transforms,
  serialize detection and classification results, create visualizations and
  crops, separate images safely, and process video or demo UI outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data and post-processing

Use this sub-skill after a detector or classifier has produced results, or when
preparing image inputs for those models. It covers public PytorchWildlife
1.3.0 data, transform, utility, video, and demo contracts. It does not choose
or construct models, train models, or run a web service.

## Route first

- Route detector construction, model versions, confidence semantics, and
  detector result generation to `detection`.
- Route classifier construction, class catalogs, and crop classification to
  `classification`; use this skill for the crop dataset and output boundary.
- Route audio, spectrogram, and bioacoustic files to `bioacoustics`.
- Route training, annotation splits, and legacy fine-tuning to `fine-tuning`.
- Keep this skill for folder loading, transforms, result files, visual output,
  video callbacks, and Gradio/Docker caveats.

Read the focused contracts before implementation:

- [data-formats.md](references/data-formats.md) — folder datasets, crop
  assumptions, extensions, RGB/path/size outputs, and transforms.
- [post-processing.md](references/post-processing.md) — visualizers, crop
  files, detection/dot/TimeLapse/classification JSON, and separation rules.
- [video-and-ui.md](references/video-and-ui.md) — callback/fps/codec contract,
  UI limits, security, installation, and Docker overview.
- [troubleshooting.md](references/troubleshooting.md) — predictable failures
  and recovery actions.
- [separate_detection_results.py](scripts/separate_detection_results.py) — a
  standard-library, validation-first copy helper for untrusted JSON.

## Dataset decision table

| Need | Use | Item contract |
| --- | --- | --- |
| Direct classifier images | `ClassificationImageFolder` | `(image, path)` |
| Detector image batches | `DetectionImageFolder` | `(image, path, (H, W))` |
| Classify detector animal boxes | `DetectionCrops` | `(crop, path)` |

`ClassificationImageFolder` and `DetectionImageFolder` recursively discover
case-insensitive `.jpg`, `.jpeg`, `.png`, `.ppm`, `.bmp`, `.pgm`, `.tif`,
`.tiff`, and `.webp` files. Both open and convert each image to RGB before the
optional transform. The detection dataset records original `(height, width)`
before transformation; the classification dataset does not return that size.
Paths are filesystem paths, not class labels. The native recursive discovery
order is not a stable dataset-order guarantee, so sort paths if reproducible
ordering matters.

`DetectionCrops` consumes detection result dictionaries containing `img_id`
and a `supervision.Detections` object. It selects detections whose
`class_id == animal_cls_id` (default `0`), resolves `path_head / img_id` when
provided, crops image-space `xyxy`, converts to RGB, and applies its transform.
It assumes files and boxes are valid and does not return detection indices;
keep crop and classifier result order aligned.

## Transform decision table

| Model input | Transform | Defaults and output |
| --- | --- | --- |
| MegaDetector v5 | `MegaDetector_v5_Transform` | target 1280, stride 32, CHW float tensor, letterbox/pad |
| Classifier inference | `Classification_Inference_Transform` | target 224, tensor, ImageNet normalization |

`letterbox` preserves aspect ratio, scales to `[0,1]`, and pads with
`114/255`; it accepts a PIL image or CHW tensor. `scaleup=False` prevents
upscaling. Classification resize is square and does not preserve aspect
ratio. Full parameters and coordinate cautions are in
[data-formats.md](references/data-formats.md).

## Result boundary

The usual result entry has `img_id`, `detections.xyxy`,
`detections.class_id`, `detections.confidence`, and model `labels`. Before
serializing, establish a portable image-id policy and validate that every
parallel array has the same length. Use `exclude_file_path` only when its
exact native path prefix is known; inspect output for machine-local paths.

Choose output deliberately:

1. `save_detection_images` for RGB images with boxes and labels.
2. `save_detection_images_dots` for dot-style annotations such as HerdNet.
3. `save_crop_images` for one crop per detection.
4. `save_detection_json` for integer `xyxy` boxes and parallel category and
   confidence lists.
5. `save_detection_json_as_dots` for center-point JSON.
6. `save_detection_timelapse_json` for normalized `xywh` TimeLapse boxes.
7. Classification serializers only after verifying detector/crop alignment.

These functions create output files/directories and do not remove source
images. Keep generated outputs outside recursively scanned input folders.
Use [post-processing.md](references/post-processing.md) for exact schemas,
empty-detection behavior, normalized-coordinate requirements, and the
current image-level classification association behavior.

## Safe image separation

The native `detection_folder_separation` copies each referenced image into
`Animal` or `No_animal`, preserving nested paths. Category `0` is positive only
when confidence is strictly greater than the supplied threshold; equality is
negative. Empty results are negative. For user-supplied JSON, prefer the
bundled script:

```bash
python scripts/separate_detection_results.py --json detections.json \
  --source-root /data/images --destination /data/separated --threshold 0.2
```

The helper requires relative non-traversing `img_id` values, validates lists
and source containment, aggregates duplicate image ids, copies with `copy2`,
refuses destinations inside the source tree, and refuses overwrite unless
`--overwrite` is explicit. Run its bounded fixture check with:

```bash
python scripts/separate_detection_results.py --self-test
```

## Video and demo UI

`process_video` invokes `callback(frame: numpy.ndarray, index: int) ->
numpy.ndarray` on RGB frames and writes an RGB result after converting for the
codec. `target_fps` can cause frame stride and `index` is the sampled-frame
index. Start model instances once outside the callback. `mp4v` is the default;
`avc1` may improve browser playback only with a compatible OpenCV build.

The Gradio demo supports single images, ZIP batches, folder separation, and
video with FPS/codec controls, but has no authentication and is not a
multi-tenant service. Keep it on loopback with `share=False`, bound temporary
files, upload sizes, and archive paths; do not launch it during verification.
Large uploads, Windows batch/video uploads, browser codecs, and missing ffmpeg
or OpenCV encoder support are known caveats. Installation and Docker are
reference-only deployment paths; do not pull images or launch services as a
routine data operation. See [video-and-ui.md](references/video-and-ui.md).
