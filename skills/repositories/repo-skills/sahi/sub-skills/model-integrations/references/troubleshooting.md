# Troubleshooting SAHI model integrations

Use this file after choosing a `model_type` from [model-matrix.md](model-matrix.md) and checking optional packages with [optional-dependencies.md](optional-dependencies.md).

## First split: dependency, weight, credential, or config?

1. Run the safe checker:

   ```bash
   python ../scripts/check_model_dependencies.py --model-type <model_type>
   ```

2. If packages are missing, fix dependencies first; do not change `model_path` yet.
3. If packages are present but the wrapper says the path is invalid, check local file existence, remote/cache behavior, and weight/config pairing.
4. If the model source is private, hosted, or gated, check credentials separately from dependency status.
5. If predictions load but categories are wrong or missing, check `category_mapping` key types and `category_remapping` semantics.

## Failure matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError` from `MODEL_TYPE_TO_MODEL_CLASS_NAME` | Unsupported or misspelled `model_type`. | Use a value in the model matrix. Remember that `yolov8`, `yolov11`, `yolo11`, and `yolo26` are aliases for `ultralytics`. |
| `ImportError: The following packages are required...` | Optional framework packages are missing. | Install only the packages for the selected route. Use the checker to identify the missing group. |
| `torch is required to use device='cuda:0'` or similar | Torch is absent but a torch-backed device was explicitly requested. | Install torch or switch to `device="cpu"`. Then verify `torch.cuda.is_available()` or MPS availability outside SAHI if GPU is required. |
| Model silently runs on CPU after requesting CUDA/MPS | Torch is present but backend is unavailable or hidden. | Inspect backend availability in the runtime. SAHI's device selection falls back to CPU when the requested accelerator cannot be selected. |
| `model_path is not a valid Ultralytics model path` | Missing local file, unsupported export format/runtime, unsupported YOLOE/YOLO-World class in installed Ultralytics, or implicit remote download blocked. | Use a local `.pt`/exported model that Ultralytics can load. For ONNX, also install an ONNX runtime. For YOLOE/YOLO-World, verify the Ultralytics release supports that class. |
| `Category names not available. Please provide category_mapping for ONNX models.` | Exported Ultralytics model lacks embedded names. | Pass `category_mapping` with string id keys, for example `{"0": "person", "2": "car"}`. |
| `Not a yolov5 model` | A preloaded `model` object is not from the expected YOLOv5 module. | Pass `model_path` to the YOLOv5 package loader or provide a compatible YOLOv5 model object. |
| `model_path is not a valid rtdetr model path` | The SAHI RT-DETR wrapper uses Ultralytics RTDETR, but the path/source is for another ecosystem or missing. | For Ultralytics RT-DETR use `model_type="rtdetr"`; for HuggingFace RT-DETR checkpoints use `model_type="huggingface"`. |
| `AttributeError` mentioning `YOLOWORLDDetectionModel` | The inspected auto-map spells the YOLO-World class differently from the wrapper class. | Check whether the installed SAHI version has patched the auto-map. If not, patch the class name or use a compatible release before treating this as a dependency problem. |
| `hugging_face_universal_segmentation` fails to import a wrapper | The inspected auto-map declares this value but no matching wrapper class was found. | Use `model_type="huggingface_segmentation"` with `SegmentationType` unless your installed release adds and verifies the universal class. |
| HuggingFace load fails for a private/gated model | Missing token or token lacks access. | Pass `token=...` at runtime or set `HF_TOKEN`; do not hard-code tokens in reusable files. |
| GroundingDINO raises that `text_labels` or `text_prompt` is required | Zero-shot detector needs text input. | Prefer `text_labels=[...]` for stable ids and filtering of combined phrases; use `text_prompt` for open-ended dynamic labels. |
| GroundingDINO returns unexpected category ids or combined phrases | Dynamic phrase labels were used, or fixed labels did not match returned phrases. | Use `text_labels` for known classes. SAHI drops combined phrases not in the fixed list and assigns stable ids to the labels. |
| HuggingFace segmentation returns one mask per class rather than per object | Semantic segmentation mode was selected. | Use `SegmentationType.INSTANCE_SEGMENTATION` for instance masks. Semantic segmentation intentionally merges all pixels of the same class. |
| TorchVision tries to download weights | No `model_path` was given, so the wrapper uses default weights for the selected architecture. | Provide a local `model_path` state dict and a matching `config_path`, or use a preloaded `model`. |
| TorchVision state dict load fails | `config_path` architecture/`num_classes` does not match the state dict. | Match YAML `model_name` and `num_classes` to the trained checkpoint; use a preloaded model if construction is custom. |
| MMDetection wrapper cannot even import | `torch`, `mmdet`, `mmcv`, or `mmengine` is missing or incompatible. | Install a compatible OpenMMLab stack. Treat Python, torch, CUDA, mmcv, mmengine, and mmdet versions as one stack, not independent packages. |
| MMDetection config pipeline errors such as missing `LoadImageFromFile` or `Resize` | Config does not have the test pipeline shape the SAHI wrapper expects. | Use a standard MMDetection inference config or adapt the test pipeline before loading. Keep `config_path` and checkpoint from the same model family. |
| Detectron2 wheel cannot install/import | Detectron2 wheels are platform, Python, torch, and CUDA sensitive. | Use a matching wheel/source build in an isolated environment, or choose another backend if Detectron2 is not required. |
| Detectron2 categories become numeric strings | Metadata lookup failed and SAHI fell back to configured class count. | Pass an explicit `category_mapping` or register dataset metadata before loading. |
| Roboflow says authorization failed | The route is Roboflow Universe and lacks a valid API key. | Pass `api_key=...` at runtime or set `ROBOFLOW_API_KEY`. If you intended local RF-DETR, use an exact RF-DETR class name such as `RFDETRSegMedium`, a class object, or an instance. |
| Roboflow local RF-DETR says it cannot resolve a model | `model` was `None`, a non-RF-DETR string, or an unsupported object. | For local RF-DETR use exact class-name strings (`RFDETRBase`, `RFDETRSegMedium`, etc.), classes, or instances. Any other string is treated as a Universe id. |
| Local RF-DETR custom classes are `None` or head size mismatches | Missing or wrong `category_mapping`, key type, or resolution. | Provide integer-key `category_mapping` for local RF-DETR custom classes and match `image_size`/resolution to training when using local weights. |
| `category_remapping` raises a key error | Mapping keys do not match old category ids as strings. | Use id-string keys such as `{"2": 0}`. Do not key by category name unless you have verified a wrapper-specific path that supports it. |
| Categories have correct names but unexpected ids | `category_remapping` changed ids after conversion. | Remove remapping or update downstream expectations; it preserves the existing category name while changing the category id. |

## Model path versus config path checklist

| Framework | `model_path` should be | `config_path` should be |
| --- | --- | --- |
| Ultralytics / YOLOE / YOLO-World | Weight/export path or model name. | Optional Ultralytics cfg forwarded at inference time. |
| YOLOv5 | YOLOv5-supported weight source. | Usually unused. |
| RT-DETR | Ultralytics RT-DETR weight source. | Usually unused. |
| HuggingFace detection/segmentation | Hub id or local model directory. | Usually unused by SAHI. |
| TorchVision | Optional state dict path. If absent, default weights may be used. | YAML selecting `model_name` and `num_classes`; defaults to Faster R-CNN with COCO classes when absent. |
| MMDetection | Checkpoint weights. | MMDetection config for the same checkpoint. |
| Detectron2 | Checkpoint path or model-zoo weight source. | Detectron2 config file/name for the same architecture. |
| Roboflow Universe | Usually unused. | Usually unused. Use `model` for the hosted id. |
| Local RF-DETR | Local RF-DETR weights when not using built-in/pretrained initialization. | Usually unused. Use `model` for the RF-DETR class/class name/instance. |

## Hardest diagnostic cases

- **Open-vocabulary failure triage:** `model_type="yolo-world"` can fail because of the source auto-map class spelling, missing/old `ultralytics`, or missing model weights. Check in that order before changing prompts.
- **Roboflow string ambiguity:** `model="rfdetr-base"` is a Universe id and needs an API key; `model="RFDETRBase"` is a local RF-DETR class name and needs local RF-DETR dependencies plus category mapping for custom classes.
- **HuggingFace zero-shot labels:** A missing `text_labels`/`text_prompt` is not a model-weight failure. A token error is not a dependency failure. Treat text input, token access, and package versions as separate gates.
