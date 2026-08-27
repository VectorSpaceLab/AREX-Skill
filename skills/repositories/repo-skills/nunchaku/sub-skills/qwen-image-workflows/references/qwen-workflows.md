# Qwen-Image operating workflows

This reference describes how to replace Diffusers Qwen transformer components with `NunchakuQwenImageTransformer2DModel` for Qwen-Image generation, Qwen-Image-Edit, Qwen-Image-Edit-2509, Lightning variants, ControlNet routing, and Qwen-specific offload.

## API facts to preserve

| API | Operating notes |
| --- | --- |
| `from nunchaku import NunchakuQwenImageTransformer2DModel` | Exported at package top level and also available from `nunchaku.models.transformers.transformer_qwenimage`. |
| `NunchakuQwenImageTransformer2DModel.from_pretrained(pretrained_model_name_or_path, **kwargs)` | Loads a quantized Qwen transformer. The source asserts that the argument is a local file or a path/name ending in `.safetensors` or `.sft`; pass a specific checkpoint file, not a model directory. Useful kwargs include `torch_dtype=...`, `device=...`, and `offload=...`. |
| `NunchakuQwenImageTransformer2DModel.set_offload(offload: bool, **kwargs)` | Enables/disables Nunchaku asynchronous CPU offload for transformer blocks. Useful kwargs include `use_pin_memory` and `num_blocks_on_gpu`. |
| `QwenImagePipeline` | Diffusers text-to-image pipeline for `Qwen/Qwen-Image`. |
| `QwenImageEditPipeline` | Diffusers edit pipeline for `Qwen/Qwen-Image-Edit`; usually one input image. |
| `QwenImageEditPlusPipeline` | Diffusers edit-plus pipeline used by `Qwen/Qwen-Image-Edit-2509`; examples pass one or a list of input images. Requires new Qwen classes in Diffusers; use `diffusers>=0.36`. |
| `QwenImageControlNetModel` + `QwenImageControlNetPipeline` | ControlNet routing for Qwen-Image. The native candidate guards this with `diffusers>=0.36`. |

## Precision, dtype, and rank

- Use `nunchaku.utils.get_precision()` to select the quantized asset family. The docs state FP4 assets for Blackwell/RTX 50-series and INT4 assets for other architectures; the Qwen transformer source maps `fp4` to its internal `nvfp4` patching path.
- Rank is encoded in checkpoint names such as `_r32` or `_r128`. Docs and examples use `rank=32` as a fast/default choice and note that increasing rank, for example to 128, can improve output quality.
- Pass `torch_dtype` when loading the transformer and the Diffusers pipeline. Native candidates choose `torch.float16` on Turing-class GPUs and `torch.bfloat16` otherwise. Avoid calling `.to(dtype=...)` after the quantized model is initialized; the source raises for dtype changes after quantization.
- Qwen examples typically use `torch.bfloat16` on non-Turing GPUs. Keep transformer and pipeline dtype aligned.

```python
import torch
from nunchaku import NunchakuQwenImageTransformer2DModel
from nunchaku.utils import get_precision

rank = 32
transformer = NunchakuQwenImageTransformer2DModel.from_pretrained(
    f"nunchaku-tech/nunchaku-qwen-image/svdq-{get_precision()}_r{rank}-qwen-image.safetensors",
    torch_dtype=torch.bfloat16,
)
```

## Text-to-image workflows

### Original Qwen-Image

| Field | Value |
| --- | --- |
| Base model | `Qwen/Qwen-Image` |
| Diffusers pipeline | `QwenImagePipeline` |
| Nunchaku transformer asset pattern | `nunchaku-tech/nunchaku-qwen-image/svdq-{precision}_r{rank}-qwen-image.safetensors` |
| Typical rank | `32`; try `128` when text/layout quality matters and assets are available |
| Typical generation kwargs from examples/tests | `negative_prompt=" "`, `num_inference_steps=20-50`, `true_cfg_scale=4.0`, explicit `width`/`height` as needed |

```python
import torch
from diffusers import QwenImagePipeline
from nunchaku import NunchakuQwenImageTransformer2DModel
from nunchaku.utils import get_precision

rank = 32
transformer = NunchakuQwenImageTransformer2DModel.from_pretrained(
    f"nunchaku-tech/nunchaku-qwen-image/svdq-{get_precision()}_r{rank}-qwen-image.safetensors",
    torch_dtype=torch.bfloat16,
)
pipe = QwenImagePipeline.from_pretrained(
    "Qwen/Qwen-Image", transformer=transformer, torch_dtype=torch.bfloat16
)
pipe.to("cuda")
image = pipe(
    prompt="Bookstore window display with a sign that reads New Arrivals This Week. Ultra HD, 4K.",
    negative_prompt=" ",
    width=1024,
    height=1024,
    num_inference_steps=50,
    true_cfg_scale=4.0,
).images[0]
```

## Lightning scheduler and step counts

Qwen Lightning examples use a `FlowMatchEulerDiscreteScheduler` with a fixed scheduler config from the Qwen-Image-Lightning reference. Use Lightning only with pre-quantized Nunchaku Lightning checkpoints; custom Qwen LoRA support is documented as under development.

| Workflow | Pipeline | Asset patterns from evidence | Steps | `true_cfg_scale` |
| --- | --- | --- | --- | --- |
| Qwen-Image-Lightning | `QwenImagePipeline` | `nunchaku-tech/nunchaku-qwen-image/svdq-{precision}_r{rank}-qwen-image-lightningv1.0-4steps.safetensors`; `...lightningv1.1-8steps.safetensors` | 4 or 8 | `1.0` |
| Qwen-Image-Edit-Lightning | `QwenImageEditPipeline` | `nunchaku-tech/nunchaku-qwen-image-edit/svdq-{precision}_r{rank}-qwen-image-edit-lightningv1.0-4steps.safetensors`; `...8steps.safetensors` | 4 or 8 | `1.0` |
| Qwen-Image-Edit-2509-Lightning | `QwenImageEditPlusPipeline` | Tests use `...qwen-image-edit-2509-lightningv2.0-{steps}steps.safetensors`; examples may use dated `lightning-251115/...-lightning-{steps}steps-251115.safetensors` assets. Check current asset availability. | 4 or 8 | `1.0` |

```python
import math
from diffusers import FlowMatchEulerDiscreteScheduler

scheduler_config = {
    "base_image_seq_len": 256,
    "base_shift": math.log(3),
    "invert_sigmas": False,
    "max_image_seq_len": 8192,
    "max_shift": math.log(3),
    "num_train_timesteps": 1000,
    "shift": 1.0,
    "shift_terminal": None,
    "stochastic_sampling": False,
    "time_shift_type": "exponential",
    "use_beta_sigmas": False,
    "use_dynamic_shifting": True,
    "use_exponential_sigmas": False,
    "use_karras_sigmas": False,
}
scheduler = FlowMatchEulerDiscreteScheduler.from_config(scheduler_config)
```

## Edit workflows

### Qwen-Image-Edit

| Field | Value |
| --- | --- |
| Base model | `Qwen/Qwen-Image-Edit` |
| Diffusers pipeline | `QwenImageEditPipeline` |
| Nunchaku transformer asset pattern | `nunchaku-tech/nunchaku-qwen-image-edit/svdq-{precision}_r{rank}-qwen-image-edit.safetensors` |
| Input image | Load as a PIL image and convert to RGB. Examples pass `image=image`. |
| Typical kwargs | `negative_prompt=" "`, `num_inference_steps=20-50`, `true_cfg_scale=4.0` for original; `true_cfg_scale=1.0` and 4/8 steps for Lightning. |

```python
import torch
from diffusers import QwenImageEditPipeline
from diffusers.utils import load_image
from nunchaku import NunchakuQwenImageTransformer2DModel
from nunchaku.utils import get_precision

rank = 128
transformer = NunchakuQwenImageTransformer2DModel.from_pretrained(
    f"nunchaku-tech/nunchaku-qwen-image-edit/svdq-{get_precision()}_r{rank}-qwen-image-edit.safetensors",
    torch_dtype=torch.bfloat16,
)
pipe = QwenImageEditPipeline.from_pretrained(
    "Qwen/Qwen-Image-Edit", transformer=transformer, torch_dtype=torch.bfloat16
).to("cuda")
input_image = load_image("input.png").convert("RGB")
result = pipe(
    image=input_image,
    prompt="change the sign text to read Nunchaku Qwen Image Edit",
    negative_prompt=" ",
    num_inference_steps=50,
    true_cfg_scale=4.0,
).images[0]
```

## 2509 edit-plus workflows

`Qwen/Qwen-Image-Edit-2509` uses `QwenImageEditPlusPipeline`. The usage docs explicitly require `diffusers` version `0.36.0` or higher for the 2509 example. Evidence examples show both single-image and multi-image edit inputs; for multi-reference edits pass a list of RGB PIL images as `image=[image1, image2, ...]` and write prompts that refer to image positions.

| Field | Value |
| --- | --- |
| Base model | `Qwen/Qwen-Image-Edit-2509` |
| Diffusers pipeline | `QwenImageEditPlusPipeline` |
| Nunchaku transformer asset pattern | `nunchaku-tech/nunchaku-qwen-image-edit-2509/svdq-{precision}_r{rank}-qwen-image-edit-2509.safetensors` |
| Lightning variants | Use Lightning scheduler and 4/8-step pre-quantized assets; verify the exact dated or v2.0 asset name exists before running. |
| Input image | One RGB PIL image or a list of RGB PIL images. |

```python
from diffusers import QwenImageEditPlusPipeline

pipe = QwenImageEditPlusPipeline.from_pretrained(
    "Qwen/Qwen-Image-Edit-2509", transformer=transformer, torch_dtype=torch.bfloat16
)
# image may be a single PIL image or a list of PIL images for multi-reference edits.
```

## ControlNet routing

Qwen ControlNet routing keeps the Nunchaku Qwen transformer as the image transformer and adds a Diffusers Qwen ControlNet component.

| Field | Value |
| --- | --- |
| Base model | `Qwen/Qwen-Image` |
| ControlNet model | `InstantX/Qwen-Image-ControlNet-Union` |
| Pipeline | `QwenImageControlNetPipeline` |
| Extra pipeline input | `control_image=...`, plus `controlnet_conditioning_scale=...` |
| Version gate | Use `diffusers>=0.36`; native candidates skip when Qwen ControlNet classes are missing. |

```python
import torch
from diffusers import QwenImageControlNetModel, QwenImageControlNetPipeline
from diffusers.utils import load_image

controlnet = QwenImageControlNetModel.from_pretrained(
    "InstantX/Qwen-Image-ControlNet-Union", torch_dtype=torch.bfloat16
)
pipe = QwenImageControlNetPipeline.from_pretrained(
    "Qwen/Qwen-Image",
    transformer=transformer,
    controlnet=controlnet,
    torch_dtype=torch.bfloat16,
)
control_image = load_image("control.png").convert("RGB")
image = pipe(
    prompt="a minimalist living room, following the depth layout",
    negative_prompt=" ",
    control_image=control_image,
    controlnet_conditioning_scale=1.0,
    num_inference_steps=30,
    true_cfg_scale=4.0,
).images[0]
```

The transformer source accepts `controlnet_block_samples` in `forward`, matching the residual routing required by Qwen ControlNet pipelines.

## Offload patterns

Qwen Nunchaku offload is not the same as Diffusers module offload. When combining them, exclude the Nunchaku transformer from Diffusers sequential CPU offload and let `set_offload` manage the transformer blocks.

### High-VRAM convenience path

Examples use Diffusers model CPU offload on larger GPUs:

```python
pipe.enable_model_cpu_offload()
```

### Low-VRAM Nunchaku transformer offload

```python
transformer.set_offload(True, use_pin_memory=False, num_blocks_on_gpu=1)
if "transformer" not in pipe._exclude_from_cpu_offload:
    pipe._exclude_from_cpu_offload.append("transformer")
pipe.enable_sequential_cpu_offload()
```

Notes:

- Increase `num_blocks_on_gpu` when there is spare VRAM; examples/tests use values from `1` to `20` depending on memory budget.
- `set_offload(True)` can also be requested at load time with `offload=True`, but explicit post-load calls make the offload policy easier to read.
- If offload is enabled, the transformer source deliberately skips moving the model to GPU through `.to(device)` and emits a warning.
- Disable offload with `transformer.set_offload(False)` when switching to a non-offload run; this clears the offload manager and releases CUDA cache.

## Parameterized template

The bundled template supports basic generation/edit runs without checkout-local paths:

```bash
python scripts/qwen_image_template.py \
  --mode txt2img \
  --transformer nunchaku-tech/nunchaku-qwen-image/svdq-int4_r32-qwen-image.safetensors \
  --base-model Qwen/Qwen-Image \
  --prompt "a storefront sign that reads Nunchaku" \
  --output qwen.png \
  --device cuda \
  --dtype bf16

python scripts/qwen_image_template.py \
  --mode edit \
  --transformer nunchaku-tech/nunchaku-qwen-image-edit/svdq-int4_r128-qwen-image-edit.safetensors \
  --base-model Qwen/Qwen-Image-Edit \
  --prompt "replace the sign text with Nunchaku" \
  --image input.png \
  --output edit.png \
  --device cuda \
  --dtype bf16 \
  --offload
```

## Native verification candidates, not executed here

- `tests/v1/qwenimage/test_qwenimage.py` for base text-to-image ranks and dtype routing.
- `tests/v1/qwenimage/test_qwenimage_lightning.py` for Lightning scheduler and 4/8-step assets.
- `tests/v1/qwenimage/test_qwenimage_edit.py` and `test_qwenimage_edit_lightning.py` for edit inputs and Lightning edit routing.
- `tests/v1/qwenimage/test_qwenimage_edit_2509.py` and `test_qwenimage_edit_2509_lightning.py` for 2509 edit-plus routing.
- `tests/v1/qwenimage/test_qwenimage_controlnet.py` for ControlNet routing and the `diffusers>=0.36` gate.
