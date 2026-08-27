---
name: models-and-deployment
description: "Use Kornia models, application builders, ONNX deployment, output
  conversion, and multi-framework transpilation safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kornia Models And Deployment

Use this sub-skill when a task mentions Kornia model builders, pretrained model
configuration, high-level application wrappers, model output conversion, ONNX
export/runtime composition, `torch.compile` deployment, or Ivy-backed
multi-framework conversion.

## Read first

- For the model/API map and no-download defaults, read
  [references/model-overview.md](references/model-overview.md).
- For task recipes around SAM, RT-DETR, DexiNed, YuNet, ViT-family backbones,
  output conversion, and application wrappers, read
  [references/workflows.md](references/workflows.md).
- For ONNXModule, ONNXSequential, `to_onnx`, ONNX Runtime providers, and
  `to_numpy`/`to_jax`/`to_tensorflow`, read
  [references/onnx-and-transpiler.md](references/onnx-and-transpiler.md).
- For adding or changing public models and deployment surfaces, read
  [references/development-notes.md](references/development-notes.md).
- For missing optional packages, weight/cache/network problems, device/dtype
  mismatches, export issues, and lazy-transpilation limits, read
  [references/troubleshooting.md](references/troubleshooting.md).
- To probe an installed Kornia runtime without downloads, run
  [scripts/model_runtime_probe.py](scripts/model_runtime_probe.py) and
  [scripts/optional_dependency_probe.py](scripts/optional_dependency_probe.py).

## Fast routing

Choose this sub-skill for:

- `kornia.models.*` model classes, configs, builders, and model-specific
  `from_config`, `from_name`, `from_pretrained`, `load_checkpoint`, or
  `to_onnx` questions.
- `Sam`, `SamConfig`, `VisualPrompter`, promptable segmentation outputs,
  `SegmentationResults`, and MobileSAM setup.
- `RTDETR`, `RTDETRConfig`, `RTDETRDetectorBuilder`, `ObjectDetector`,
  detection output conversion, drawing, saving, and ONNX export.
- `YuNet`, `FaceDetector`, `FaceDetectorResult`, `DexiNed`, `EdgeDetector`,
  and `EdgeDetectorBuilder` application-model usage.
- `VisionTransformer`, `MobileViT`, `TinyViT`, `EfficientViT`, backbone feature
  outputs, classification-head attachment, and no-download model smokes.
- `ModelBaseMixin.save`, `visualize(..., output_type=...)`, `output_type="pil"`,
  `output_type="torch"`, and application wrapper `save()` behavior.
- `kornia.onnx.ONNXModule`, `kornia.onnx.ONNXSequential`, ONNX loader/cache
  behavior, providers, `io_maps`, IR/opset conversion, and export metadata.
- `kornia.to_numpy()`, `kornia.to_jax()`, `kornia.to_tensorflow()`, and optional
  dependency errors involving `onnx`, `onnxruntime`, `onnxscript`, `ivy`,
  `transformers`, `diffusers`, `huggingface_hub`, `safetensors`, or model
  backend packages.

Route away when the main problem is not model/deployment orchestration:

- Low-level image filtering, color conversion, morphology, or enhancement ops:
  use the relevant image-processing sub-skill from the Kornia root.
- Geometric warps, camera models, pose/epipolar/depth geometry, and coordinate
  conventions: [geometry-vision](../geometry-vision/SKILL.md).
- Local feature detection, descriptors, LoFTR/LightGlue-style matching, and
  matcher-pretrained weights: [features-and-matching](../features-and-matching/SKILL.md).
- Random augmentation containers and synchronized masks/boxes/keypoints before a
  model sees data: use the augmentation-pipelines sub-skill from the Kornia root.

## Operating rules

1. Do not trigger pretrained downloads by default. Use `pretrained=False`, config
   objects, or randomly initialized models for probes unless the user explicitly
   approves weights, network/cache access, and model size.
2. Prefer documented submodule imports for configs: import `SamConfig` from
   `kornia.models.sam` and `RTDETRConfig` from `kornia.models.rt_detr`; do not
   assume every config is re-exported from top-level `kornia.models`.
3. Keep image tensors as PyTorch tensors, usually `B,C,H,W` or `C,H,W`; use
   floating RGB data in `[0,1]` for application wrappers that normalize, draw,
   prompt, or save visualizations.
4. Keep model parameters, image tensors, prompts, boxes, and post-processing
   tensors on the same device and compatible dtype. Use `float32` first for
   model/debug work; treat CUDA, MPS, float16, and bfloat16 as optional backend
   paths that need explicit verification.
5. Use application builders when you need preprocessing/postprocessing included;
   use raw model classes when you need tensor-level logits, features, training,
   or custom processors.
6. Treat `output_type` as a visualization conversion choice, not a model-output
   datatype contract. Kornia model mixins support `"torch"` and `"pil"`; they do
   not convert outputs to NumPy.
7. For ONNX work, verify optional packages and providers before exporting or
   running. `ONNXSequential` requires ONNX/ONNX Runtime at construction time and
   remote `hf://` inputs can download unless already cached.
8. For Ivy transpilation, expect lazy first-call conversion and limited compiler
   compatibility. Probe a small function before committing a whole model path.
