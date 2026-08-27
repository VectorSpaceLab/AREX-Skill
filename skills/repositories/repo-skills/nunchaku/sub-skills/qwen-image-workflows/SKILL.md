---
name: qwen-image-workflows
description: "Operate Qwen-Image, Qwen-Image-Edit, Lightning, 2509, ControlNet,
  and offload workflows with Nunchaku quantized transformers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Qwen Image workflows with Nunchaku

Use this sub-skill when a task involves Qwen-Image text-to-image, Qwen-Image-Edit, Qwen-Image-Edit-2509, Qwen Lightning variants, Qwen ControlNet, or Qwen-specific transformer offload in an installed `nunchaku` environment.

Do not use this sub-skill for FLUX-only LoRA/adapters or custom Qwen LoRA training/loading. The Qwen docs describe custom LoRA support as under development; use only the pre-quantized Lightning assets documented for Qwen workflows.

## Fast routing

| Need | Start here |
| --- | --- |
| Basic Qwen-Image generation | `references/qwen-workflows.md#text-to-image-workflows` |
| Qwen-Image-Lightning 4/8-step generation | `references/qwen-workflows.md#lightning-scheduler-and-step-counts` |
| Qwen-Image-Edit with one input image | `references/qwen-workflows.md#edit-workflows` |
| Qwen-Image-Edit-2509 or multi-image edit | `references/qwen-workflows.md#2509-edit-plus-workflows` |
| Qwen ControlNet Union routing | `references/qwen-workflows.md#controlnet-routing` |
| Low-VRAM Qwen inference | `references/qwen-workflows.md#offload-patterns` |
| Failure diagnosis | `references/troubleshooting.md` |
| Parameterized local template | `scripts/qwen_image_template.py` |

## Core operating pattern

1. Pick the Diffusers pipeline for the workflow (`QwenImagePipeline`, `QwenImageEditPipeline`, `QwenImageEditPlusPipeline`, or `QwenImageControlNetPipeline`).
2. Load a Nunchaku quantized transformer with `NunchakuQwenImageTransformer2DModel.from_pretrained(...)` and pass it into `pipeline.from_pretrained(..., transformer=transformer, torch_dtype=...)`.
3. Pass a single `.safetensors`/`.sft` checkpoint path or Hugging Face file path to `from_pretrained`; do not pass a model directory.
4. Choose `torch.float16` on Turing-class GPUs and usually `torch.bfloat16` elsewhere; set dtype during `from_pretrained`, not by casting the quantized model after load.
5. For low VRAM, prefer `transformer.set_offload(True, ...)`, append `"transformer"` to the pipeline CPU-offload exclusion list, and then call Diffusers sequential CPU offload.
6. For 2509 and ControlNet routing, require Diffusers APIs new enough for the Qwen classes; use `diffusers>=0.36` when those classes are needed.

## Minimal snippets

```python
import torch
from diffusers import QwenImagePipeline
from nunchaku import NunchakuQwenImageTransformer2DModel

transformer = NunchakuQwenImageTransformer2DModel.from_pretrained(
    "nunchaku-tech/nunchaku-qwen-image/svdq-int4_r32-qwen-image.safetensors",
    torch_dtype=torch.bfloat16,
)
pipe = QwenImagePipeline.from_pretrained(
    "Qwen/Qwen-Image", transformer=transformer, torch_dtype=torch.bfloat16
)
pipe.to("cuda")
image = pipe(prompt="a clean storefront sign that reads Nunchaku", num_inference_steps=50, true_cfg_scale=4.0).images[0]
```

For complete generation/edit templates and offload-safe variants, use `references/qwen-workflows.md` and `scripts/qwen_image_template.py`.

## Evidence base

Distilled from the Qwen usage docs, Qwen examples, Qwen native test candidates, live public API inspection, and `NunchakuQwenImageTransformer2DModel` source behavior. Native Qwen tests/examples are verification candidates for later integration; this sub-skill does not claim they were run during drafting.
