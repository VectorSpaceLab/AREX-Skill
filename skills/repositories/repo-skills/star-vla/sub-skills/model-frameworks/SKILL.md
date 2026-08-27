---
name: model-frameworks
description: "Choose and inspect StarVLA model frameworks, registry names,
  baseframework APIs, action heads, backbones, checkpoint compatibility, and
  safe model-level smoke plans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StarVLA model frameworks

Use this sub-skill when the task is to choose, identify, inspect, or debug a StarVLA model family or framework config. It covers VLM4A, VM4A, and WM4A framework names, the `baseframework` contract, action-head/backbone compatibility, checkpoint config overrides, and safe model-level smoke planning.

## Start here

1. For a framework choice or registry-name question, read [references/model-families.md](references/model-families.md).
2. For API, checkpoint, config override, or `from_pretrained` questions, read [references/framework-api.md](references/framework-api.md).
3. For backbone/action-head/dimension compatibility, read [references/action-heads-and-backbones.md](references/action-heads-and-backbones.md).
4. For errors, read [references/troubleshooting.md](references/troubleshooting.md) and then the root [troubleshooting reference](../../references/troubleshooting.md) when install or backend issues are cross-cutting.
5. To inspect an installed StarVLA environment without loading model weights, run [scripts/inspect_framework_registry.py](scripts/inspect_framework_registry.py).

## Safe operating pattern

- Prefer config/registry inspection before model construction. Listing the registry or reading `framework.name` never needs checkpoint downloads.
- Instantiate a model only after confirming the requested framework key, VLM/world-model weight location, action/state dimensions, action horizon, backend, and download policy.
- Treat framework source `__main__` demos as reference-only unless the user explicitly allows pretrained-weight access and the required GPU/accelerator setup.
- `framework.name` is the current build selector. Older docs or scripts may contain stale names such as `framework.framework_py`; translate to `framework.name` before using `build_framework`.

## Route elsewhere

- Training launcher, optimizer, Accelerate/DeepSpeed, freezing, and LR-group details: [training-config](../training-config/SKILL.md).
- Dataset registry, LeRobot data layout, `data_mix`, `modality.json`, and statistics ownership: [data-integration](../data-integration/SKILL.md).
- Policy servers, clients, `unnorm_key`, and served action response contracts: [policy-deployment](../policy-deployment/SKILL.md).
- Benchmark simulator environments and two-terminal evaluation plans: [benchmark-evaluation](../benchmark-evaluation/SKILL.md).
