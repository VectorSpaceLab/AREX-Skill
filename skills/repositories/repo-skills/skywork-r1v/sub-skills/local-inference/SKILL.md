---
name: local-inference
description: "Run or adapt local Skywork-R1V3 inference commands with safe
  Transformers/vLLM guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Local Skywork-R1V3 inference

Use this sub-skill when a user wants to run, adapt, or debug local Skywork-R1V3 multimodal inference with either the Transformers entrypoint or the vLLM entrypoint.

Do not use this sub-skill for Skywork-R1V4 API batch testing; route that workflow to `r1v4-api-testing`. Do not use it for VLMEvalKit, EMMA, MMK12, or benchmark reproduction; route those workflows to `evaluation-reproduction`.

## Operating posture

- Treat full Skywork-R1V3-38B inference as a heavy CUDA workflow. The safe helpers in this subtree do not load models, download checkpoints, initialize vLLM, import torch, or touch GPUs.
- Default model identity for local inference is `Skywork/Skywork-R1V3-38B`; allow a local checkpoint path or compatible model id when the user has already prepared weights.
- Confirm the backend first: Transformers for direct `model.chat()` behavior and explicit image patch lists; vLLM for tensor-parallel generation using chat templates.
- Confirm image count and prompt tags before running. Multi-image prompts need one image token per image unless the backend helper already adds them.
- Be explicit that native full-run verification is optional/unexecuted unless the user supplies model weights, CUDA dependencies, GPUs, and runtime budget.

## Fast routing checklist

1. Need a command without loading the model? Use [`scripts/build_inference_command.py`](scripts/build_inference_command.py).
2. Need to estimate image tiling/patch pressure without torch? Use [`scripts/check_image_grid.py`](scripts/check_image_grid.py).
3. Need command and setup details? Read [`references/workflows.md`](references/workflows.md).
4. Need exact flags and defaults? Read [`references/api-and-parameters.md`](references/api-and-parameters.md).
5. Hit CUDA, model-loading, vLLM, image-tag, or OOM errors? Read [`references/troubleshooting.md`](references/troubleshooting.md).

## Minimal safe helper examples

```bash
python scripts/build_inference_command.py --backend transformers \
  --image-path demo.png \
  --question "Describe the image and reason step by step."

python scripts/check_image_grid.py --width 1600 --height 900 --thumbnail
```

The generated command is only a command string for the user to run in their prepared inference environment; it is not executed by the helper.
