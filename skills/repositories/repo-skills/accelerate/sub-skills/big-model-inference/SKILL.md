---
name: big-model-inference
description: "Use Accelerate big-model inference utilities for meta
  initialization, device-map planning, checkpoint dispatch, CPU/disk offload,
  hooks, pipeline inference, and memory sizing without triggering downloads or
  heavyweight runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Big Model Inference

Use this sub-skill when an agent needs to load, inspect, partition, or troubleshoot models that may not fit in a single device's memory. It covers Accelerate's `init_empty_weights`, `infer_auto_device_map`, `load_checkpoint_and_dispatch`, `dispatch_model`, CPU/disk offload helpers, hook behavior, `prepare_pippy`, and model-size estimation concepts.

## Route First

- For generic `accelerate launch`, `accelerate config`, or `accelerate estimate-memory` CLI syntax, route to `../configuration-and-cli/`.
- For DeepSpeed ZeRO-3 training/inference tradeoffs, route to `../distributed-training-backends/`.
- For normal `Accelerator.prepare` training loops, route to the training-oriented sub-skill instead of using big-model dispatch primitives.

## Core References

- Read `references/workflows.md` for safe workflows: meta-device construction, device-map planning, checkpoint dispatch, CPU/disk offload, distributed inference, and pipeline parallelism.
- Read `references/api-reference.md` for public APIs, key parameters, and import locations.
- Read `references/troubleshooting.md` when device maps, offload folders, checkpoint indexes, meta tensors, split points, or optional model libraries fail.
- Use `scripts/big_model_api_smoke.py --help` or run the script directly to verify tiny CPU/meta-device API availability without downloads.

## Safety Defaults

- Prefer tiny synthetic `torch.nn.Module` models for inspection and examples.
- Do not call `from_pretrained`, `snapshot_download`, or heavyweight model examples unless the user explicitly wants network/model downloads.
- Treat disk offload as requiring a real writable offload folder and clean it up after experiments.
- Never call `.to("cpu")`, `.cuda()`, or a forward pass on a model still initialized on `meta`; load or set real tensors first.
