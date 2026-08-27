# Auto-labeling model overview

X-AnyLabeling exposes AI-assisted annotation models through a model registry of
YAML configs. In the verified package environment, ModelManager loaded 204
built-in configs after the normal config/work-directory initialization. Selecting
or custom-loading a model does more than parse YAML: it chooses a `type`,
instantiates that type's adapter, resolves local paths or downloads files, and
then returns shapes/descriptions for the annotation UI.

Use this overview to choose a model family before editing configs or debugging
backends. For exact fields and custom loading, continue to
[custom-models.md](custom-models.md). For cache, downloads, and runtime extras,
continue to [backend-and-downloads.md](backend-and-downloads.md).

## Model-family map

| Need | Model families / registry types | Typical output or interaction | Notes |
|---|---|---|---|
| Image-level or shape-level classification | `yolov5_cls`, `yolov8_cls`, `yolo11_cls`, `internimage_cls`, `pulc_attribute` | image/shape label or attributes | PULC configs cover person/vehicle attributes. Route UI classifier panel details to the annotation UI sub-skill. |
| Horizontal object detection | `yolov5`, `yolov6`, `yolov7`, `yolov8`, `yolov9`, `yolov10`, `yolo11`, `yolo12`, `yolo26`, `yolox`, `yolo_nas`, `damo_yolo`, `gold_yolo`, `rtdetr`, `rtdetrv2`, `rfdetr`, `dfine`, `deimv2`, `u_rtdetr`, `upn` | rectangles, optional class filtering, confidence/IoU thresholds | YOLO-family configs are the common starting point for adapted custom detection. |
| Instance/semantic segmentation | `yolov5_seg`, `yolov8_seg`, `yolo11_seg`, `yolo26_seg`, `rfdetr_seg`, `dfine_seg`, `rmbg`, segmentation-capable remote models | polygons/masks, matting outputs, optional mask fineness | `rmbg` is matting/background removal rather than ordinary instance segmentation. |
| Pose and face | `yolov8_pose`, `yolo11_pose`, `yolo26_pose`, `rtmdet_pose`, `yolox_dwpose`, `scrfd`, `yolov6_face` | keypoints, face landmarks, optional rectangles | Pose class lists can be dictionaries of object class to keypoint names. |
| Multi-object tracking | `yolov5_det_track`, `yolov8_det_track`, `yolo11_det_track`, `yolo26_det_track`, matching `*_seg_track`, `*_obb_track`, `*_pose_track`, SAM2/3 video, `remote_server` video modes | frame-by-frame tracked shapes | Trackers include ByteTrack, BoT-SORT, and TrackTrack depending on config. Reset tracker support is model-type gated. |
| Oriented bounding boxes | `yolov5_obb`, `yolov8_obb`, `yolo11_obb`, `yolo26_obb`, `rio_detr` | rotated boxes / quadrilaterals | Useful for DOTA-like aerial/remote-sensing datasets. Route conversion to DOTA formats to the conversion sub-skill. |
| Depth | `depth_anything`, `depth_anything_v2` | depth visualizations / depth annotations | CPU import was verified; actual model inference requires model files. |
| Segment Anything / promptable segmentation | `segment_anything`, `segment_anything_2`, `segment_anything_3`, `segment_anything_2_video`, `sam_hq`, `sam_med2d`, `edge_sam`, `efficientvit_sam`, `mobile_sam`-style configs, `grounding_sam`, `grounding_sam2`, `yolov5_sam`, `yolov8_sam2` | masks from points/boxes/text/auto-grid; video propagation for video variants | These usually need encoder/decoder model paths and are sensitive to backend/provider setup. |
| Matting/background removal | `rmbg` | cutout or thumbnail-rendered PNG-like results | X-AnyLabeling has thumbnail render routing for RMBG outputs. |
| RAM/tagging and captioning | `ram`, `yolov5_ram`, `yolow_ram`, `florence2` | tags, descriptions, captions, open-vocabulary outputs | Florence2 may use a Hugging Face model id or local path, not just an ONNX file. |
| OCR/text recognition | `ppocr_v4`, `ppocr_v5`, `ppocr_v6`, `doclayout_yolo`, remote PaddleOCR-capable services | OCR boxes/text, layout blocks, document regions | PaddleOCR document parsing panel can use official API keys or remote services; see backend notes for token/service concerns. |
| Layout and document parsing | `doclayout_yolo`, PaddleOCR panel models, `remote_server` with `ppocr_pipeline` capability | layout categories, parsed document blocks | Full annotation/editing of document results belongs in annotation UI guidance. |
| Vision-language / grounding | `florence2`, `open_vision`, `grounding_dino`, `grounding_dino_api`, `grounding_sam`, `grounding_sam2`, `yolow`, `yoloe`, SAM3/LocateAnything-style remote or example workflows | text-prompted detection/segmentation, captions, region-to-text, open vocabulary labels | API and remote models require tokens/network; some model families require additional optional packages. |
| Counting | `geco`, CountGD/GeCo-style remote/example workflows | object counts plus boxes/masks depending adapter | Built-in GeCo config uses separate encoder/decoder files. |
| Lane detection | `clrnet` | lane polylines | Configs carry original image geometry and lane-specific thresholds. |

## Built-in configs versus custom configs

Built-in configs are listed in the packaged model registry. Each registry entry
points at a resource YAML file whose `name` is the internal identifier and whose
`display_name` is shown in the UI. Loading a built-in config can trigger a model
file download when the referenced local file is not already cached.

Custom configs split into two cases:

- **Adapted custom model**: the `type` already exists in X-AnyLabeling. Copy the
  nearest config pattern, change paths/classes/thresholds, then load it through
  the custom model loader. No source-code changes are needed.
- **Unadapted model**: the `type` does not exist yet. Add a config, add a
  registry entry, add the type to the relevant UI/model-type lists, and
  implement a `Model` subclass. This is a development task; route export and
  packaging support to the developer-workflows sub-skill.

## Local, remote, and API-backed models

- **Local ONNX / DNN / TensorRT models** resolve files from `model_path` or other
  path fields, optionally downloading from a URL first. ONNX Runtime CPU was the
  only verified execution provider during construction.
- **Remote server models** use the `remote_server` type. The client discovers
  models from `/v1/models`, predicts through `/v1/predict`, and can handle video
  prompt endpoints for supported server models. Configure server URL and API key
  through settings/environment before assuming connectivity.
- **API-backed models** include `grounding_dino_api` and PaddleOCR official API
  document parsing. These require valid tokens/API keys and network access.

## Registry facts useful for inspection

- Verified package version: `x-anylabeling-cvhub` 4.0.2.
- Verified built-in registry count after config initialization: 204 configs.
- The packaged YAML directory contained 205 YAML files during construction; the
  registry file determines which ones load in the UI.
- Built-in registry names had no duplicates in the inspected package.
- The custom-capable type allow-list contained 93 model types in the inspected
  code.
- Use `scripts/inspect_model_configs.py` for future count/type inspection; it
  intentionally does not instantiate model classes or load weights.
