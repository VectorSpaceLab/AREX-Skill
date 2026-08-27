---
name: serving
description: "Guide Otter controller, worker, Gradio, local CLI, endpoint,
  import, port, and load-bit serving workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Otter serving sub-skill

Use this sub-skill when the task is to expose Otter or Flamingo generation through a local controller/worker service, Gradio image/video UI, direct text-generation CLI, or HTTP streaming endpoint.

## Route here for

- Controller, model-worker, Gradio image UI, Gradio video UI, worker registration, heartbeats, and queue dispatch.
- Model-worker options such as `--checkpoint_path`, `--model_name`, `--num_gpus`, `--load_bit`, controller/worker URLs, and concurrency.
- Streaming request payloads containing `prompt`, optional base64 image/video frames, and `generation_kwargs`.
- Debugging known serving import problems, dependency/version issues, missing constants, bad ports, registration failures, and GPU/load-bit problems.
- Local text-only CLI generation with `--model-name`, `--device`, `--num-gpus`, and conversation templates.

## Route away

- Ad hoc package/API inference or YAML batch prompt files: [model-inference](../model-inference/SKILL.md).
- Training, finetuning, Accelerate/DeepSpeed, and checkpoint save cadence: [training](../training/SKILL.md).
- Benchmark configs and evaluator registries: [benchmark-evaluation](../benchmark-evaluation/SKILL.md).
- MIMIC-IT data conversion, Syphus, and schema validation: [data-preparation](../data-preparation/SKILL.md).

## Operating workflow

1. Decide whether the user needs a three-process web demo, a direct local CLI, or endpoint/API debugging.
2. Read [serving topology](references/serving-topology.md) for controller, worker, Gradio, and local CLI roles.
3. Generate safe command templates with [build_serving_commands.py](scripts/build_serving_commands.py). The helper prints commands only; it never starts servers or loads models.
4. Before launching anything, run [check_serving_imports.py](scripts/check_serving_imports.py) in the target environment. Use `--repo-root` only when the user is working in an Otter checkout and wants checkout-specific diagnostics.
5. For endpoint shapes and worker payloads, read [API reference](references/api-reference.md).
6. For failures involving `pipeline.constants`, Gradio versions, worker registration, GPU memory, image payloads, or stalled streaming, use [troubleshooting](references/troubleshooting.md).

## Quick reference map

| Need | Start with |
|---|---|
| Three-process controller + worker + Gradio plan | [serving topology](references/serving-topology.md#three-process-demo-topology) |
| Generate commands with custom ports/model path | [build_serving_commands.py](scripts/build_serving_commands.py) |
| Check imports without starting services | [check_serving_imports.py](scripts/check_serving_imports.py) |
| Understand controller/worker endpoints | [API reference](references/api-reference.md) |
| Diagnose missing `pipeline.constants` or `flamingo` import | [troubleshooting](references/troubleshooting.md#known-checkout-import-defects) |
| Choose `fp16`, `bf16`, `int8`, `int4`, or `fp32` | [serving topology](references/serving-topology.md#worker-model-loading-choices) |

## Safety boundary

Serving launches long-running processes, opens network ports, can download or load large checkpoints, and may allocate multiple GPUs. Do not start controller, worker, Gradio, or Flask services unless the user supplies the model/checkpoint, host/port policy, GPU budget, and explicit permission to launch them.
