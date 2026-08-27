---
name: pipelines-and-inference
description: "Use Diffusers pipelines for loading, text-to-image,
  image-to-image, inpainting, control-conditioned inference, batching,
  callbacks, deterministic seeds, device/dtype/offload choices, and serving-safe
  invocation patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipelines and Inference

Use this sub-skill when the task is about running or wiring Diffusers inference pipelines: loading checkpoints, choosing pipeline classes, passing prompts/images/masks/control images, batching, reproducibility, callbacks, device placement, memory/offload settings, or serving pipelines behind an API.

## Route First

- For a new inference script, start with [references/pipeline-workflows.md](references/pipeline-workflows.md) and choose the smallest pipeline family that matches the inputs: text-only, image-to-image, inpainting, or control-conditioned generation.
- For loading, offline/local operation, dtype, device placement, memory, and reproducibility decisions, use [references/loading-and-runtime.md](references/loading-and-runtime.md).
- For installation, optional dependencies, device/dtype mistakes, local file failures, API misuse, inpainting shape issues, callback errors, and server concurrency problems, use [references/troubleshooting.md](references/troubleshooting.md).
- For a safe environment sanity check, run `python scripts/pipeline_env_check.py --help` or `python scripts/pipeline_env_check.py`.
- For a no-download invocation skeleton, run `python scripts/pipeline_invocation_template.py --help`; add `--allow-download` only when network/model downloads are intentional.

## Boundaries

- Training and fine-tuning recipes belong to `training-recipes`.
- Scheduler algorithm trade-offs and custom scheduler design belong to `schedulers`; this sub-skill only shows where to attach or clone a scheduler for inference.
- LoRA, IP-Adapter, textual inversion, and adapter weight mechanics belong to `adapters-and-loaders`; this sub-skill only routes control/image conditioning inputs at pipeline-call level.
- Modular pipeline block authoring belongs to `modular-pipelines`.
- Checkpoint conversion, repo maintenance, and CLI conversion utilities belong to `conversion-and-maintenance`.

## Default Inference Checklist

1. Import a concrete `AutoPipelineFor...` class when task type is known, otherwise use `DiffusionPipeline` for generic loading.
2. Load with `from_pretrained(model_or_path, **kwargs)`; use `local_files_only=True` for offline/local-only execution.
3. Choose device and dtype together: CPU uses default/float32; CUDA commonly uses `torch.float16` or `torch.bfloat16`; MPS usually loads then `.to("mps")` and may need memory-saving attention slicing.
4. Pass workflow-specific inputs by name: `prompt`, `image`, `mask_image`, `control_image`, `negative_prompt`, `height`, `width`, `strength`, `generator`, `callback_on_step_end`.
5. Use a fresh `torch.Generator(device="cpu").manual_seed(seed)` for repeatable single-image calls; use one generator per item for batched calls.
6. Treat output as a pipeline output object unless `return_dict=False`; generated images are usually in `result.images`.
