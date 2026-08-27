# SAHI model integration matrix

This reference routes SAHI model loading only. For prediction calls, slicing, batch options, and postprocessing, leave this sub-skill and use the owning inference/postprocess sub-skills.

## `AutoDetectionModel.from_pretrained` contract

`AutoDetectionModel.from_pretrained(...)` normalizes a small set of aliases, imports a wrapper class from `sahi.models.<model_type>`, and forwards common arguments to that wrapper.

Common arguments:

| Argument | Use | Notes |
| --- | --- | --- |
| `model_type` | Selects the wrapper family. | Values and aliases are listed below. Unknown values raise `KeyError` before any model load. |
| `model_path` | Weight path, checkpoint path, model name, Hub id, or framework-specific source. | A name that is not a local file may trigger a framework download when the wrapper loads. Use local paths for offline runs. |
| `model` | Preloaded object or, for Roboflow, an overloaded model id/class/instance. | Useful when a model is already initialized or customized. Some direct wrapper classes accept extra objects such as a HuggingFace `processor` through `**kwargs`. |
| `config_path` | Configuration path/name for MMDetection, Detectron2, TorchVision, and Ultralytics cfg forwarding. | Do not swap weights and configs: many `model_path is not valid` errors are actually wrong `config_path`/`model_path` pairing. |
| `device` | `"cpu"`, `"cuda"`, `"cuda:0"`, `"mps"`, etc. | SAHI uses torch device selection. If torch is absent, only CPU can be selected; explicit CUDA/MPS requires torch plus the backend. |
| `mask_threshold` | Pixel mask threshold. | Used by segmentation-capable wrappers when converting masks to polygons. |
| `confidence_threshold` | Minimum score retained by wrapper conversion. | Default in the base loader is `0.3`; docs often show `0.25` or model-specific values. |
| `category_mapping` | Maps raw class ids to names. | Key type is wrapper-sensitive; see [category mapping rules](#category-mapping-and-remapping). |
| `category_remapping` | Remaps class ids after prediction conversion. | Current base code keys this mapping by old class id string, for example `{"0": 1, "1": 2}`. It changes ids, not names. |
| `load_at_init` | Load weights immediately. | Set `False` when you need to construct the wrapper before installing weights or when a later step will call `.load_model()`. |
| `image_size` | Override model input resolution. | Exact semantics are wrapper-specific: Ultralytics uses `imgsz`, TorchVision adjusts transform sizes, MMDetection changes resize scale, HuggingFace sets processor size, RF-DETR can use it as resolution with local weights. |
| `**kwargs` | Wrapper-specific extras. | Examples: Ultralytics `task`/`fuse`, HuggingFace `token`/`text_labels`, HuggingFace segmentation `segmentation_type`, MMDetection `scope`, Roboflow `api_key`. |

## Loader map and family notes

| `model_type` input | Wrapper class | Main packages | Weight/config source | Notes and caveats |
| --- | --- | --- | --- | --- |
| `ultralytics` | `UltralyticsDetectionModel` | `ultralytics` | `model_path` can be `.pt`, `.onnx`, OpenVINO, NCNN, TorchScript, or a framework model name. | Supports detection, segmentation, and oriented boxes through Ultralytics metadata or filename hints. Aliases `yolov8`, `yolov11`, `yolo11`, and `yolo26` normalize to this same wrapper. `.pt` models are moved to `device`; exported runtimes need their own runtime packages. |
| `yoloe` | `YOLOEDetectionModel` | `ultralytics` | `model_path` or default YOLOE model name. | Open-vocabulary/prompt-free YOLOE route. After loading, text prompts are set on the underlying Ultralytics model, for example via `detection_model.model.set_classes(...)`. Use local weights to avoid implicit downloads. |
| `yolo-world` | Declared auto-map class: `YOLOWORLDDetectionModel`; wrapper source class: `YOLOWorldDetectionModel`. | `ultralytics` | `model_path` or default YOLO-World model name. | Open-vocabulary YOLO-World route. In the inspected source, the auto-map class spelling does not match the wrapper class spelling; if `AutoDetectionModel` raises an `AttributeError`, check the installed SAHI version or load through a patched wrapper. |
| `yolov5` | `Yolov5DetectionModel` | `yolov5`, `torch` | `model_path` passed to `yolov5.load(...)`. | Classic YOLOv5 route. Wrapper sets `model.conf` from `confidence_threshold`; segmentation is not supported by this wrapper. |
| `rtdetr` | `RTDetrDetectionModel` | `ultralytics` | `model_path` or default Ultralytics RT-DETR model name. | This SAHI wrapper uses `ultralytics.RTDETR`. If you want HuggingFace RT-DETR checkpoints, route through `model_type="huggingface"` instead. |
| `huggingface` | `HuggingfaceDetectionModel` | `torch`, `transformers` plus model-dependent extras such as `timm`. | HuggingFace model id or local model directory in `model_path`; optional `token` or `HF_TOKEN`. | Supports DETR-style detection and GroundingDINO-style zero-shot detection. GroundingDINO requires `text_labels` or `text_prompt`; `text_threshold` controls phrase matching. |
| `huggingface_segmentation` | `HuggingfaceSegmentationModel` | `torch`, `transformers` plus model-dependent extras such as `timm`. | HuggingFace model id or local model directory in `model_path`; optional `token` or `HF_TOKEN`. | Supports MaskFormer, Mask2Former, and OneFormer instance/semantic/panoptic heads. Use `segmentation_type`, `min_segment_area`, `overlap_mask_area_threshold`, and `label_ids_to_fuse` as needed. |
| `hugging_face_universal_segmentation` | Declared in the auto-map, but no matching wrapper class was found in inspected source. | Treat as unresolved. | Prefer `huggingface_segmentation`. | If an installed release adds this class, verify it directly; otherwise this value is expected to fail. |
| `torchvision` | `TorchVisionDetectionModel` | `torch`, `torchvision`, `pyyaml` | `config_path` YAML with `model_name`/`num_classes`, optional `model_path` state dict, or a preloaded `model`. | Built-in models include Faster R-CNN, Mask R-CNN, RetinaNet, SSD, SSDLite, FCOS. Without `model_path`, TorchVision default weights may be requested. |
| `mmdet` | `MmdetDetectionModel` | `torch`, `mmdet`, `mmcv`, `mmengine` | Local MMDetection config in `config_path` plus checkpoint in `model_path`. | Import of the wrapper module itself checks the OpenMMLab stack. Version, Python, CUDA, torch, mmcv, and mmengine must be compatible. |
| `detectron2` | `Detectron2DetectionModel` | `torch`, `detectron2` | Detectron2 model-zoo config name or local config in `config_path`; weights in `model_path`. | Platform and wheel compatibility are the usual blockers. A model-zoo name may fetch configured weights; use local config/weights for offline work. |
| `roboflow` | `RoboflowDetectionModel` | Universe route: `inference`; local RF-DETR route: `rfdetr` plus its transitive packages. | `model` selects the route. Plain strings are Universe ids except exact RF-DETR class names; class objects/instances are local RF-DETR. | Universe ids need `api_key` or `ROBOFLOW_API_KEY`. Local RF-DETR custom weights need `model_path`, `category_mapping`, and usually `image_size` matching training resolution. |

Run [`../scripts/check_model_dependencies.py`](../scripts/check_model_dependencies.py) to see which optional packages are importable in the current runtime. See [optional-dependencies.md](optional-dependencies.md) before installing frameworks.

## Open-vocabulary routing

| Requirement | Best first route | Why | Watch for |
| --- | --- | --- | --- |
| Prompt-free or promptable YOLO segmentation/detection with Ultralytics weights | `model_type="yoloe"` | SAHI wraps Ultralytics YOLOE and keeps segmentation support through the Ultralytics conversion path. | Need a recent Ultralytics release with YOLOE support; prompts are set on the underlying model after load. |
| Text-conditioned YOLO-World classes | `model_type="yolo-world"` if the installed auto-map is patched; otherwise patched/direct wrapper loading. | SAHI includes a YOLO-World wrapper based on Ultralytics. | The inspected auto-map has a class-name spelling mismatch; distinguish this from missing `ultralytics` or missing weights. |
| Stable text labels with HuggingFace GroundingDINO | `model_type="huggingface"` with `text_labels=[...]` | SAHI assigns stable category ids to fixed labels and filters combined phrases not in the label set. | Requires `transformers` new enough for GroundingDINO, torch, text labels or a text prompt, and token access for gated models. |
| Hosted Roboflow model id | `model_type="roboflow"`, `model="workspace/model/version"` or similar | SAHI uses the Roboflow `inference` SDK for Universe models. | Any non-RF-DETR string is treated as a Universe id and requires an API key. |

## Preloaded model patterns

Use preloaded objects when a framework model has already been customized, loaded from a nonstandard registry, or patched for prompts.

```python
from sahi import AutoDetectionModel

# Ultralytics example: preloaded model object.
detection_model = AutoDetectionModel.from_pretrained(
    model_type="ultralytics",
    model=preloaded_yolo_model,
    confidence_threshold=0.25,
    device="cuda:0",
)
```

Wrapper-specific notes:

- HuggingFace direct wrapper usage may pass both a `model` and `processor`; `AutoDetectionModel` forwards extra keyword arguments such as `processor`.
- TorchVision accepts a preloaded detection model and moves it to the selected device.
- Roboflow uses `model` as a selector: Universe id string, RF-DETR class name string, RF-DETR class object, or RF-DETR instance.
- `load_at_init=False` is useful for constructing a wrapper first and calling `.load_model()` after credentials, local files, or prompts are ready.

## Category mapping and remapping

SAHI converts framework-native category ids into `ObjectPrediction` categories. Key types differ by wrapper:

| Wrapper family | Recommended `category_mapping` keys | Reason |
| --- | --- | --- |
| Ultralytics, YOLOv5, MMDetection, Detectron2, TorchVision | String ids such as `{"0": "person", "2": "car"}` when overriding defaults. | Conversion code indexes with `str(category_id)`. |
| HuggingFace detection/segmentation | Usually provided by model config as integer `id2label`; for zero-shot, SAHI creates integer ids from `text_labels` or returned phrases. | Do not force string keys unless you also verify conversion. |
| Roboflow Universe | Usually not needed; class names come from the API response. | API predictions include `class_id` and `class_name`. |
| Local RF-DETR through Roboflow wrapper | Integer ids are safest, for example `{0: "cat", 1: "dog"}`. | Local conversion uses `category_mapping.get(int(class_id), None)`. |

`category_remapping` is applied after wrapper conversion by the base class. In the inspected implementation it expects old category ids as strings and new category ids as integers, for example:

```python
category_remapping={"0": 1, "1": 2, "2": 0}
```

It preserves the existing category name while changing the id. If you need both ids and names changed, set a correct `category_mapping` before inference and then apply id remapping only if necessary.
