# Models And Deployment Workflows

These recipes are no-download first. They prefer config objects, small random
models, and explicit CPU or CUDA selection only when the caller has verified the
backend.

## 1. Validate a model config without loading weights

Use this when you only need to confirm that the right builder/config surface is
available.

```python
from kornia.models.sam import SamConfig
from kornia.models.rt_detr import RTDETRConfig
from kornia.models.efficient_vit import EfficientViTConfig

sam_cfg = SamConfig("vit_b")
rtdetr_cfg = RTDETRConfig.from_name("rtdetr_r18vd", num_classes=10)
eff_cfg = EfficientViTConfig.from_pretrained("b1", 224)
```

Checklist:

- Prefer config objects over pretrained loaders for first-pass probes.
- Remember that `SamConfig` and `RTDETRConfig` live in their submodules.
- Treat `EfficientViTConfig.from_pretrained(...)` as a checkpoint locator, not a
  model download.

## 2. Smoke-test a raw classifier/backbone

Use the raw backbone when you need tensor shapes, not downstream heads.

```python
import torch
from kornia.models.vit import VisionTransformer
from kornia.models.vit_mobile import MobileViT
from kornia.models.tiny_vit import TinyViT

img = torch.rand(1, 3, 32, 32)
vit = VisionTransformer(image_size=32, patch_size=16, embed_dim=48, depth=1, num_heads=3)
vit_tokens = vit(img)

mvit = MobileViT(mode="xxs")
mvit_feats = mvit(torch.rand(1, 3, 64, 64))

tiny = TinyViT(img_size=32, embed_dims=(16, 32, 64, 128), depths=(1, 1, 1, 1), num_heads=(1, 2, 4, 4), window_sizes=(4, 4, 4, 4), num_classes=7)
cls_logits = tiny(torch.rand(1, 3, 32, 32))
```

Checklist:

- Keep inputs floating point.
- Use small images that satisfy the model's divisibility constraints.
- Add your own head for classification if the backbone returns tokens or
  features instead of labels.

## 3. Build a compact RT-DETR deployment trace

Use a small config when you want a deterministic no-download detector probe.

```python
import torch
from kornia.models.rt_detr import RTDETR, RTDETRConfig

config = RTDETRConfig("resnet18d", num_classes=3, head_num_queries=2)
model = RTDETR.from_config(config).eval()
logits, boxes = model(torch.rand(1, 3, 32, 32))
```

Checklist:

- `logits` are `B,Q,K`; `boxes` are `B,Q,4` in normalized coordinates.
- For deployment benchmarking, call `RepVggBlock.optimize_for_deployment()` on
  the relevant encoder blocks after loading weights and switching to eval mode.
- `RTDETR.to_onnx()` overrides the default exporter to preserve the dual-output
  names `pred_logits` and `pred_boxes`.

## 3b. Build optional config-only wrappers

Use these when you need the builder/config surface but not pretrained weights.

```python
from kornia.models.kimi_vl import KimiVLBuilder, KimiVLConfig
from kornia.models.kimi_vl.config import KimiVLProjectorConfig, MoonViTConfig

vision_config = MoonViTConfig(image_size=32, patch_size=4, hidden_size=32, num_hidden_layers=1, num_attention_heads=4, intermediate_size=64)
projector_config = KimiVLProjectorConfig(input_dim=32, hidden_dim=64, output_dim=64)
config = KimiVLConfig(vision_config=vision_config, projector_config=projector_config)
model = KimiVLBuilder.from_config(config)
```

```python
from kornia.models.segmentation.segmentation_models import SegmentationModelsBuilder

# Only if segmentation_models_pytorch is installed.
seg = SegmentationModelsBuilder.build(encoder_weights=None, classes=2)
```

Checklist:

- Keep the config small when you only need a shape or import probe.
- Use `KimiVLBuilder.from_pretrained_hf()` only when `huggingface_hub` and `safetensors` are available and remote weights are allowed.
- If `segmentation_models_pytorch` is installed, `SegmentationModelsBuilder.build(encoder_weights=None)` is the no-download wrapper path.

## 4. Run the end-to-end RT-DETR wrapper

Use the wrapper when you need resize and post-processing handled for you.

```python
from kornia.contrib.object_detection import RTDETRDetectorBuilder

model = RTDETRDetectorBuilder.build(
    model_name="rtdetr_r18vd",
    pretrained=False,
    image_size=32,
)
detections = model(torch.rand(1, 3, 64, 64))
```

Checklist:

- The wrapper returns a list of `D,6` tensors.
- `visualize(..., output_type="pil")` is for rendering, not tensor postprocessing.
- `confidence_filtering` mainly changes ONNX-export behavior; eager runs still apply the wrapper's confidence filtering path.
- Use `save()` when you want timestamped output files for inspection.

## 5. Run edge detection with safe defaults

```python
from kornia.contrib.edge_detection import EdgeDetectorBuilder

model = EdgeDetectorBuilder.build(pretrained=False, image_size=32).eval()
edges = model(torch.rand(1, 3, 48, 40))
```

Checklist:

- `EdgeDetectorBuilder` normalizes the input before DexiNed and applies a
  sigmoid after the model.
- The wrapper resizes predictions back to the original image size.
- Use `output_type="pil"` when you need visual overlays.

## 6. Inspect YuNet or face detection outputs

If you only need the raw network shape, use `YuNet` directly; the high-level
`FaceDetector` constructor downloads weights by default.

```python
import torch
from kornia.models.yunet import YuNet

model = YuNet("test", pretrained=False)
out = model(torch.rand(1, 3, 64, 64))
```

Checklist:

- Raw YuNet returns `loc`, `conf`, and `iou`.
- The high-level face detector returns one `N,15` tensor per image, which can
  be wrapped with `FaceDetectorResult`.
- If you need face detection in offline mode, avoid the default `FaceDetector()`
  constructor because it loads pretrained weights at init time.

## 7. Use promptable SAM safely

```python
from kornia.models.sam import Sam, SamConfig
from kornia.contrib.visual_prompter import VisualPrompter

config = SamConfig("vit_b")
prompter = VisualPrompter(config)
```

Checklist:

- Use `set_image(...)` once, then call `predict(...)` repeatedly with point,
  box, and/or mask prompts.
- Input images should be floating RGB tensors, usually in `[0,1]`.
- `predict(..., output_original_size=True)` maps logits back to the source image
  size after the internal resize/pad pipeline.
- The advertised manual tiny-SAM config branch is not a practical shortcut in
  0.9.0rc1; prefer named variants or the MobileSAM path for actual model use.

## 8. Export a model to ONNX

Use the model-specific `to_onnx` helper when it exists.

```python
from kornia.models.dexined import DexiNed
from kornia.models.rt_detr import RTDETR, RTDETRConfig
from kornia.models.sam import Sam, SamConfig

edge = DexiNed(pretrained=False)
edge.to_onnx("dexined.onnx", pseudo_shape=[1, 3, 32, 32])

rtdetr = RTDETR.from_config(RTDETRConfig("resnet18d", num_classes=3, head_num_queries=2))
rtdetr.to_onnx("rtdetr.onnx", pseudo_shape=[1, 3, 32, 32])

sam = Sam.from_config(SamConfig("vit_b"))
sam.to_onnx("sam_encoder.onnx", pseudo_shape=[1, 3, 1024, 1024])
```

Checklist:

- `DexiNed.to_onnx()` and `RTDETR.to_onnx()` export tensor-to-tensor graphs.
- `Sam.to_onnx()` exports the image encoder only; full prompt-to-mask Python
  flow is not directly exportable as a single ONNX graph.
- If you need to keep preprocessing or postprocessing in the deployment graph,
  export the wrapper class instead of the raw model.

## 9. Use ONNX wrappers and providers

```python
from kornia.onnx import ONNXModule, ONNXSequential
```

Checklist:

- `ONNXModule(op, providers=None, session_options=None, cache_dir=None, ...)`
  wraps one ONNX graph.
- `ONNXSequential(*ops, providers=None, session_options=None, io_maps=None, ...)`
  chains multiple graphs. `io_maps` maps adjacent graphs; each element of
  `io_maps` describes one boundary between neighboring models.
- Use `providers=["CUDAExecutionProvider", "CPUExecutionProvider"]` only when
  the runtime has matching ONNX Runtime GPU support installed.
- `auto_ir_version_conversion=True` converts models to IR 9 / opset 17 by
  default when graphs need compatibility smoothing.

## 10. Transpile Kornia to another framework

```python
import kornia

np_kornia = kornia.to_numpy()
# or: jax_kornia = kornia.to_jax()
# or: tf_kornia = kornia.to_tensorflow()
```

Checklist:

- The first call is lazy and can be slow because Ivy transpiles on demand.
- NumPy transpilation is for functions and classes, not trainable modules.
- Treat lazy transpilation as an optional deployment path; do not rely on it for
  the critical path unless it has been probed in the target environment.

## 11. Convert outputs for inspection or saving

```python
vis = detector.visualize(images, output_type="pil")
detector.save(images, directory="out")
```

Checklist:

- `output_type="torch"` keeps tensor outputs.
- `output_type="pil"` is for rendered previews.
- `save()` writes files and is best for inspection artifacts, not model logic.
