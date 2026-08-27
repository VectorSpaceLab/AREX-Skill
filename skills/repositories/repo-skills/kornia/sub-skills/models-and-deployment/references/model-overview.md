# Models And Application API Overview

This reference is for Kornia 0.9.0rc1-style model/deployment work. Kornia is a
PyTorch differentiable computer-vision library; the model APIs here are PyTorch
modules or wrappers around PyTorch/ONNX modules. The minimum runtime verified for
this skill had `torch`, `numpy`, `packaging`, and `kornia-rs`; Pillow,
requests, ONNX Runtime, ONNX, Ivy, transformers, and diffusers were optional and
not part of the minimum installation.

## Import and download policy

Use explicit submodule imports for model configs and builders:

```python
from kornia.models.sam import Sam, SamConfig
from kornia.models.rt_detr import RTDETR, RTDETRConfig
from kornia.models.dexined import DexiNed
from kornia.models.vit import VisionTransformer
from kornia.models.vit_mobile import MobileViT
from kornia.models.tiny_vit import TinyViT
from kornia.models.efficient_vit import EfficientViT, EfficientViTConfig
from kornia.models.kimi_vl import KimiVLBuilder, KimiVLConfig
from kornia.models.segmentation.segmentation_models import SegmentationModelsBuilder
from kornia.contrib.edge_detection import EdgeDetectorBuilder
from kornia.contrib.face_detection import FaceDetector, FaceDetectorResult
from kornia.contrib.object_detection import RTDETRDetectorBuilder, results_from_detections
from kornia.contrib.visual_prompter import VisualPrompter
```

Do **not** call `from_pretrained`, `load_checkpoint`, builder defaults with
`pretrained=True`, `FaceDetector()`, `VisualPrompter()` with no config, or remote
`hf://` ONNX loaders unless pretrained weights/network/cache use is intentional.
No-download probes should use `pretrained=False`, raw configs, or small randomly
initialized modules.

## Core model map

| Surface | Best use | Safe no-download construction | Output contract | Download/optional caution |
|---|---|---|---|---|
| `Sam`, `SamConfig` | Promptable segmentation and MobileSAM/SAM model creation. Use `VisualPrompter` for high-level preprocessing and prompt transforms. | `SamConfig("vit_b")` or `SamConfig("mobile_sam")` is safe; building named models is no-download when `pretrained=False`. Avoid full forwards in smoke tests because named encoders expect 1024-side inputs. | Raw `Sam.forward(images, batched_prompts, multimask_output)` returns a list of `SegmentationResults`; logits are low-resolution mask logits, commonly `K,C,256,256`. | `SamConfig(..., pretrained=True)` or a checkpoint URL/path loads weights. `Sam.to_onnx()` exports only the image encoder subgraph, not full prompt-to-mask Python output. |
| `VisualPrompter` | High-level SAM workflow: set one image/batch once, cache image embeddings, issue point/box/mask prompts repeatedly. | `VisualPrompter(SamConfig("vit_b"))` avoids weight download but still builds a large SAM model; do not call `set_image` in tiny probes. | `predict()` returns `SegmentationResults` with logits, scores, `binary_masks`, and optional original-size logits. | `VisualPrompter()` with no config defaults to a pretrained SAM-H path and can download. `compile()` compiles submodules, not the whole prompt pipeline. |
| `RTDETR`, `RTDETRConfig` | Raw object detector logits/boxes for training, custom postprocessing, or model export. | `RTDETR.from_config(RTDETRConfig("resnet18d", num_classes, head_num_queries=small))`. | `forward(images)` returns `(logits, boxes)`: logits `B,Q,K`, boxes `B,Q,4` normalized. | `RTDETR.from_pretrained(model_name)` and configs with `checkpoint` load weights. `to_onnx()` emits `pred_logits` and `pred_boxes`. |
| `RTDETRDetectorBuilder`, `ObjectDetector` | End-to-end detection with resize, postprocess, optional confidence filtering, drawing, save, and wrapper ONNX export. | `RTDETRDetectorBuilder.build("rtdetr_r18vd", pretrained=False, image_size=small)`. | Calling the wrapper returns one detection tensor per image, shaped `D,6` as `(class_id, score, x, y, w, h)` after postprocessing. | Default builder behavior can use pretrained RT-DETR if no config/model is provided or if `pretrained=True`; eager builds still apply the wrapper's confidence-filtering path. |
| `DexiNed` | Raw deep edge map model. | `DexiNed(pretrained=False)`. | `forward(B,3,H,W)` returns fused edge response `B,1,H,W`. | `pretrained=True` loads DexiNed weights. `to_onnx()` is available when ONNX packages are installed. |
| `EdgeDetectorBuilder`, `EdgeDetector` | End-to-end DexiNed edge detection with resize, normalization, sigmoid, visualization, save, and wrapper ONNX export. | `EdgeDetectorBuilder.build(pretrained=False, image_size=small)`. | Wrapper returns resized-back edge maps; visualization can return torch tensors or PIL images. | Builder default is `pretrained=True`; set it explicitly to avoid downloads. |
| `YuNet` | Raw face detection network used by the high-level face detector. | `YuNet("test", pretrained=False)` with at least a modest input size such as `64x64`. | Raw output is a dict with `loc`, `conf`, and `iou` tensors. | `YuNet(..., pretrained=True)` loads weights. |
| `FaceDetector`, `FaceDetectorResult` | High-level YuNet face detection, NMS, result fields, and facial keypoint access. | No safe high-level default: `FaceDetector()` constructs a pretrained YuNet. Probe raw `YuNet(pretrained=False)` instead. | `FaceDetector(image)` returns a list of `N,15` tensors. `FaceDetectorResult` exposes bbox corners, score, width/height, and five keypoints. | Requires pretrained weights for useful detections and triggers loading at construction. |
| `VisionTransformer` | ViT token backbone for classification heads, detection/segmentation heads, and feature extraction. | `VisionTransformer(image_size=32, patch_size=16, embed_dim=48, depth=1, num_heads=3)`. | Output is token embeddings `B,N,D`; `encoder_results` keeps per-block tokens. | `from_config(variant, pretrained=True)` downloads AugReg weights for supported variants. No classification head is included by default. |
| `MobileViT` | Mobile-friendly convolution/transformer backbone. | `MobileViT(mode="xxs")` on small divisible inputs. | For `256x256`, output is a final feature map such as `B,320,8,8` for `xxs`. | No built-in pretrained loader in this surface. Attach your own head for classification. |
| `TinyViT` | Tiny vision transformer classifier or MobileSAM image encoder backbone. | `TinyViT(img_size=32, embed_dims=(16,32,64,128), depths=(1,1,1,1), num_heads=(1,2,4,4), window_sizes=(4,4,4,4), num_classes=small)`. | Normal mode returns class logits `B,num_classes`; `mobile_sam=True` returns feature maps for SAM. | `TinyViT.from_config(..., pretrained=True)` downloads variant-specific checkpoints and may reset mismatched classification heads. |
| `EfficientViT`, `EfficientViTConfig`, `efficientvit_backbone_*` | EfficientViT feature backbones for dense prediction/deployment experiments. | `kornia.models.efficient_vit.backbone.efficientvit_backbone_b0()` is no-download; `EfficientViTConfig.from_pretrained(...)` only creates a checkpoint URL config. | Backbones return a dict including `input`, stage outputs, and `stage_final`. | `EfficientViT.from_config(config)` loads weights from `config.checkpoint`; do not call it in offline probes unless the checkpoint is local/cached. |
| `SegmentationModelsBuilder` | Optional segmentation-model wrapper for classical encoder/decoder deployment. | `SegmentationModelsBuilder.build(encoder_weights=None, classes=small)` is the no-download shape-check path when `segmentation_models_pytorch` is installed. | Wrapper returns a `SemanticSegmentation` module with preprocessing and identity postprocessing. | Default `encoder_weights="imagenet"` can download encoder weights; `segmentation_models_pytorch` itself is optional. |
| `KimiVLBuilder`, `KimiVLConfig` | Kimi-VL vision-projector builder for config-only or pretrained HF weight loading. | `KimiVLBuilder.from_config(KimiVLConfig(...small MoonViT...))` is safe; use a tiny config for smoke checks. | `KimiVLModel` returns vision-language projector embeddings rather than class logits. | `from_pretrained_hf()` requires `huggingface_hub` and `safetensors` and downloads the supported checkpoint. |

## Output conversion and save behavior

- `ModelBaseMixin._tensor_to_type(output, output_type)` accepts only
  `"torch"` and `"pil"`. It returns tensors unchanged for `"torch"` and PIL
  images for `"pil"`; unsupported strings raise a runtime error.
- `ModelBaseMixin.save(output, directory)` creates the directory and writes one
  image per tensor/list item using a timestamped filename. It is for image-like
  tensors, not arbitrary logits or dictionaries.
- Application wrappers usually expose `visualize(..., output_type="torch")` and
  `save(...)`. Use `visualize(..., output_type="pil")` when a downstream tool
  expects PIL images, then keep file writing under your own explicit output
  directory.
- `SegmentationResults.binary_masks` thresholds either original-size logits (if
  `original_res_logits(...)` has been called) or the low-resolution logits.
- `results_from_detections(detections, format)` converts a `D,6` RT-DETR-style
  tensor into typed `ObjectDetectorResult` records.

## Pretrained model catalog cautions

Kornia maintains a model-weight catalog for tests and docs. It includes weights
for DexiNed, YuNet, RT-DETR, ViT, TinyViT, MobileSAM/SAM-related paths, and many
feature-model weights. Treat catalog membership as evidence that a download path
exists, not as permission to download. Before calling a pretrained path, confirm:

1. the task needs real pretrained predictions rather than API/shape checks;
2. network/cache access is allowed or a local checkpoint is provided;
3. expected device, dtype, and memory are available;
4. the model is not actually a feature-matching model that belongs to
   [features-and-matching](../../features-and-matching/SKILL.md).
