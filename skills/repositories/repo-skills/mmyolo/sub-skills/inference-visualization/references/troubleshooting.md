# Inference and visualization troubleshooting

Use this when an MMYOLO inference, LabelMe, video, SAHI, feature-map, or BoxAM/CAM workflow fails.

## Quick triage

1. Confirm the package stack imports: `mmyolo`, `mmdet`, `mmcv`, `mmengine`, `torch`.
2. Confirm the config and checkpoint are from the same model family and class set.
3. Confirm the input file list is non-empty before inference.
4. Force `--device cpu` unless CUDA availability and MMCV/PyTorch compatibility are already known.
5. Lower `--score-thr` if no detections appear.
6. For optional recipes, check the optional dependency first: `sahi` for large-image slicing, `grad-cam` for BoxAM/CAM, video codecs for video output.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `--to-labelme` used together with `--show` | LabelMe JSON writing and interactive display are mutually exclusive in image-demo semantics. | Choose one: remove `--show` for JSON export, or remove `--to-labelme` for displayed images. |
| `Cannot find image file.` or zero inputs | Source path is not a directory, URL, or supported image suffix. Directory may contain unsupported extensions only. | Check the path, file suffix, and URL. Supported image suffixes are `jpg`, `jpeg`, `png`, `ppm`, `bmp`, `pgm`, `tif`, `tiff`, and `webp`. |
| URL input unexpectedly downloads a file | `get_file_list` downloads URL inputs to the current working directory. | Prefer a local file path for deterministic runs, or obtain approval before URL use. Clean up downloaded files when appropriate. |
| CUDA device error or MMCV op error | Requested CUDA device is unavailable, or PyTorch/MMCV were installed for a different CUDA/CPU variant. | Retry with `--device cpu`. If GPU is required, rebuild/install a matching PyTorch + MMCV stack before claiming CUDA support. |
| `ModuleNotFoundError` for `mmdet`, `mmcv`, `mmengine`, or `mmyolo` | OpenMMLab core stack or MMYOLO package is not installed in the active environment. | Install/activate the correct environment and verify imports before running inference. Do not fix this inside a runtime command template. |
| Registry/model type is unknown | MMYOLO registries were not loaded or config scope is missing. | In API scripts, call `from mmyolo.utils import register_all_modules; register_all_modules(init_default_scope=True)` before `init_detector`. |
| Loaded checkpoint class names are missing or wrong | Config/checkpoint mismatch, checkpoint lacks dataset metadata, or custom dataset metainfo is incomplete. | Use a matching config/checkpoint pair. Inspect `model.dataset_meta.get('classes')` before class filtering or LabelMe export. |
| `--class-name` raises an error | Class names are case-sensitive and must be present in `model.dataset_meta['classes']`. | Print available classes and correct spelling/case. For custom models, verify dataloader `metainfo.classes` in the config. |
| Class-filtered visualized images still show other classes | MMYOLO image-demo-style `--class-name` filtering is used for LabelMe shape selection, while the visualizer uses `pred_score_thr`. | For rendered image class filtering, filter `result.pred_instances` manually before visualizer drawing; see `api-reference.md`. |
| No detections or empty LabelMe `shapes` | Score threshold too high, wrong checkpoint/config, unsupported object classes, or image preprocessing mismatch. | Lower `--score-thr`, verify the model classes, test a known image, and check config/checkpoint compatibility. |
| TTA assertion about missing `tta_model` or `tta_pipeline` | The config was not authored with test-time augmentation fields. | Use a TTA-enabled config or run without `--tta`. Do not add TTA fields blindly to an unknown config. |
| TTA output has shape/padding issues | `batch_shapes_cfg` or padded test pipeline conflicts with TTA behavior. | Remove `batch_shapes_cfg` from the resolved test dataset when applying the TTA pipeline, matching the MMYOLO recipe. |
| `--deploy` did not produce an ONNX/TensorRT/MMDeploy artifact | `--deploy` only switches compatible PyTorch blocks to deploy mode. | Route export/backend-artifact work to `deployment-conversion`. Use this sub-skill only for normal PyTorch inference/visualization. |
| LabelMe files are written but downstream tools complain about paths | LabelMe writer records the runtime image path and sets `imageData` to null. Some consumers require images to remain next to JSON files. | Keep JSON files and source images in a layout accepted by the downstream LabelMe/COCO conversion tool, or rewrite `imagePath` deliberately after export. |
| Video recipe asserts that no output operation was specified | Video inference requires either saving a video or showing frames. | Set an output video path or enable interactive show; prefer saved output on headless machines. |
| Output video cannot be opened or is blank | Codec/FourCC mismatch, invalid FPS/size, or RGB/BGR confusion. | Use a widely supported codec such as `mp4v`, preserve input frame size, and verify color conversion around the visualizer output. |
| Display window fails | Headless environment or missing GUI backend. | Disable `--show`; save images/video to an output directory/file instead. |
| `ImportError` asking to install `sahi` | Large-image slicing imports SAHI. | Install `sahi` only if the large-image workflow is required; otherwise use ordinary image inference. |
| Large-image merge assertion about lengths | Number of patch inference results does not match number of slice offsets. | Keep patch batching order intact and pass the same `sliced.starting_pixels` returned by the slicer. |
| Large-image duplicates or missing edge detections | Patch overlap or merge NMS threshold is unsuitable. | Increase overlap for boundary objects, tune `merge_iou_thr`, and inspect debug grid output on a small image. |
| Feature-map target layer does not exist | Layer string does not match the built model. | Preview/print the model first. Try broad targets like `backbone` or `neck`, then refine to paths such as `neck.out_layers[1]`. |
| Feature-map overlay looks shifted | YOLO resize/letterbox padding metadata does not align with naive feature-map upsampling. | Use a visualization-only config with simple resize/no padding metadata. Do not use that config for metric reporting. |
| `ImportError` asking to install `grad-cam` | BoxAM/CAM recipe needs the `pytorch_grad_cam` package provided by the `grad-cam` distribution. | Install the optional package only for CAM workflows, then verify import before model loading. |
| CAM run is very slow or out of memory | AblationCAM is expensive, image is large, too many detections/layers, or GPU memory is insufficient. | Prefer `gradcam`, reduce image size, set `--topk`, use `--max-shape`, lower batch size, or run on a smaller target layer. |
| CAM output is empty | No boxes survived `score_thr` or target layer did not receive activations. | Lower `score_thr`, confirm detector output first, and validate the target layer with a feature-map/preview pass. |
| Grad-based CAM errors around losses | Detection CAM target construction needs family-specific loss handling. | Test with a known-supported family and one image first. If using a custom family/head, inspect loss names before relying on CAM output. |

## When to stop and reroute

- If the user asks for training curves, AP/AR metrics, `--json-prefix`, `--out` prediction pickle files, or `--show-dir` from evaluator tests, route to `training-evaluation`.
- If the user asks to convert LabelMe/YOLO/COCO annotations before training, route to `data-tools`.
- If the user asks to export or run an ONNX/TensorRT/RKNN/MMDeploy/EasyDeploy backend artifact, route to `deployment-conversion`.
