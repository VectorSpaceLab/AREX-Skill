---
name: llm-vla-and-services
description: "Use TorchRL LLM post-training, VLA data/actions, services,
  rendering, and weight-update surfaces safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TorchRL LLM, VLA, Services, and Rendering

Use this sub-skill when a task mentions TorchRL LLM post-training, RLHF, GRPO,
SFT, chat environments, LLM inference wrappers, tool execution services,
Vision-Language-Action data, action tokenizers, service registry/lifecycle,
rendering, video outputs, or LLM/VLA weight synchronization.

## Route by task

- For `ChatEnv`, `History`, `PromptData`, reward data, `LLMCollector`,
  `TransformersWrapper`, `vLLMWrapper`, `SGLangWrapper`, GRPO, SFT,
  distillation, policy version tracking, or vLLM/SGLang weight sync, read
  [LLM and RLHF workflows](references/llm-and-rlhf-workflows.md).
- For `validate_vla_tensordict`, VLA canonical TensorDict keys,
  `RobotDatasetMetadata`, action chunking, `UniformActionTokenizer`,
  `VocabTailActionTokenizer`, `ActionScaling`, `TinyVLA`, LeRobot, or OpenX,
  read [VLA data and actions](references/vla-data-and-actions.md) and run
  [check_vla_schema.py](scripts/check_vla_schema.py) for a CPU-safe schema
  smoke test.
- For `Service`, `get_services`, owner/client lifecycles, direct/process/Ray
  placement, `PythonExecutorService`, `PythonInterpreter`, `rlrender`, render
  checkpoint loading, or video output, read
  [services and rendering](references/services-and-rendering.md) and run
  [smoke_services.py](scripts/smoke_services.py) for import/lifecycle checks.
- For optional extras, model downloads, GPU serving memory, tokenizer/template
  mismatch, policy-version drift, Ray cleanup, VLA shape/key failures, render
  codecs, or display issues, read [troubleshooting](references/troubleshooting.md).

## Boundaries

This sub-skill owns TorchRL's LLM/VLA/service/render-specific surfaces and the
safe checks bundled here. Route generic collector topology, replay buffers, and
weight updaters that are not LLM-specific to the collectors-and-replay area.
Route generic actor/critic/key wiring to modules-and-policies, and generic loss
module or trainer workflows to objectives-and-training.

Optional GPU serving backends, downloaded model checkpoints, Ray clusters,
robot datasets, and codec/display stacks are reference-only here unless the user
explicitly provisions those dependencies and hardware.
