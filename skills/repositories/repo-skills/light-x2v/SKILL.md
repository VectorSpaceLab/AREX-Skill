---
name: "light-x2v"
description: "Routes LightX2V generation, serving, disaggregation, and
  weight-preparation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LightX2V

LightX2V is a lightweight image/video generation framework with direct Python pipelines, a CLI entry point, a FastAPI service layer, and disaggregated multi-process deployment helpers.

Use this skill when a request mentions LightX2V, `LightX2VPipeline`, `python -m lightx2v.infer`, `python -m lightx2v.server`, `python -m lightx2v.disagg.*`, LoRA preparation, quantized checkpoints, or a LightX2V model family such as Wan, Qwen Image, HunyuanVideo, LTX, MiniMax-H3, WorldMirror, WorldPlay, or SeedVR.

## Start here

- Read [`references/overview.md`](references/overview.md) for the high-level model-family map and the major workflow surfaces.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) before debugging imports, optional backends, server startup, or weight-conversion failures.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) when you need to check whether this skill still matches the checkout that produced it.
- Run [`scripts/check_install.py`](scripts/check_install.py) after installing the package to confirm the core import path and report optional backend availability.
- Use [`scripts/setup_env.sh`](scripts/setup_env.sh) when you want a shell wrapper for the standard LightX2V runtime variables.

## Install and verify

1. Install the package with the repository's normal editable install:
   - `pip install -v -e .`
2. Use the repo's documented CUDA-capable PyTorch stack for real generation, serving, and disaggregated runs.
3. Verify the environment with:
   - `python scripts/check_install.py`
   - `python -m lightx2v.infer --help`
   - `python -m lightx2v.server --help`
   - `bash scripts/setup_env.sh --help`

The package supports many optional backends. A CPU-only import check is useful, but it does not prove that CUDA, quantization kernels, or distributed deployment are ready.

## Route map

### `sub-skills/inference/`
Use this route for direct generation or model-preparation requests that start from `LightX2VPipeline` or `lightx2v.infer`.

Typical triggers:
- "generate a video/image with LightX2V"
- "which `model_cls` and `task` should I use?"
- "how do I call `create_generator()` or `generate()`?"
- "how do I turn on offload, parallel, quantization, or LoRA loading?"
- "how should I lay out the model directory for Wan, Qwen Image, HunyuanVideo, LTX, MiniMax-H3, WorldMirror, or WorldPlay?"

Read when the task is about local generation, prompt/image/video inputs, `config_json`, model-family selection, output paths, `enable_offload`, `enable_parallel`, `enable_quantize`, `enable_lightvae`, or direct runner configuration.

### `sub-skills/serving/`
Use this route for FastAPI service startup, request submission, task polling, result download, OpenAI-compatible image endpoints, presigned uploads, queue status, and stop/cancel flows.

Typical triggers:
- "start the LightX2V server"
- "call `/v1/tasks` or `/v1/images`"
- "poll task status or download the result"
- "use the sync image endpoint"
- "stop a running task"
- "debug server status or queue pressure"

Read when the task is about `python -m lightx2v.server`, `FileService`, `TaskManager`, `/v1/service`, `/v1/files`, `/v1/tasks`, or the Gradio UI that sits on top of the same serving stack.

### `sub-skills/disagg/`
Use this route for disaggregated controller/encoder/transformer/decoder deployment, Mooncake/RDMA/ZMQ plumbing, and multi-node scheduling.

Typical triggers:
- "run the disaggregated LightX2V stack"
- "launch controller/encoder/transformer/decoder"
- "debug Mooncake, RDMA, or ZMQ setup"
- "single-node vs multi-node disaggregation"
- "understand `run_dynamic.sh` or `run_baseline.sh`"

Read when the task is about `python -m lightx2v.disagg.examples.run_service`, `run_controller`, `run_user`, service roles, port planning, or distributed topology choices.

### `sub-skills/conversion/`
Use this route for LoRA extraction/merging, dummy-meta export, and weight-format or quantization-adjacent preparation.

Typical triggers:
- "extract a LoRA from two checkpoints"
- "merge LoRA weights into a base model"
- "export dummy meta safetensors"
- "convert or quantize model weights"
- "understand the model-format and LoRA key conventions"

Read when the task is about checkpoint surgery, diff-based weights, safetensors metadata, or the LightX2V conversion tooling.

## Boundary note

The advanced `lightx2v_train` package is not routed here as a primary workflow. Its training entry point still has an import/package-layout gap, so treat it as an out-of-scope maintenance surface unless the user explicitly asks for it and accepts the limitation.

## How to choose quickly

- Direct prompt/image/video generation → `sub-skills/inference/`
- HTTP API, queueing, or result download → `sub-skills/serving/`
- Controller/encoder/transformer/decoder or RDMA/Mooncake deployment → `sub-skills/disagg/`
- LoRA, dummy-meta, or weight conversion → `sub-skills/conversion/`

If the request spans more than one route, start with the more specific sub-skill and then cross-read the other route's references.
