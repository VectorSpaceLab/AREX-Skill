---
name: v1-experimental
description: "Use for LlamaFactory experimental v1 flows selected with USE_V1=1,
  including v1 trainer architecture, v1 config parsing, v1 core engines,
  samplers, plugin configs, and migration caveats from v0 configs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# V1 Experimental

Use this sub-skill only when the user explicitly asks for LlamaFactory v1, `USE_V1=1`, v1 examples/tests, v1 plugin configs, or the experimental trainer/core architecture.

## Route Here

- CLI sessions where `USE_V1=1` is required before `llamafactory-cli` or `lmf`.
- v1 commands: `sft`, `train`, `rm`, `chat`, and `merge` under the v1 launcher.
- v1 YAML/JSON keys: `model`, `model_class`, `train_dataset`, `micro_batch_size`, `global_batch_size`, `peft_config`, `dist_config`, `kernel_config`, `quant_config`, `init_config`, `sample_backend`, and v1 batching keys.
- v1 internals: `DataEngine`, `ModelEngine`, `BaseTrainer`, `SFTTrainer`, `RMTrainer`, `BaseSampler`, plugin registry behavior, FSDP2/DeepSpeed plugin configs, and rendering plugins.
- Migration reviews that compare a v0 config to v1 and identify incompatible keys or missing v1 plugin blocks.

## Route Elsewhere

- Default LlamaFactory training without `USE_V1=1`: use `training-and-configs`.
- v0 dataset registration, `dataset_info.json`, data templates, packing, and multimodal schemas: use `data-and-templates`.
- v0 model loading, adapter merge/export, quantization, and model patching: use `model-loading-and-export`.
- v0 chat/API/Web UI/vLLM/SGLang serving or inference configs: use `inference-and-serving`.

## Start With

1. Confirm v1 intent: ask whether `USE_V1=1` is intended if the request mixes v1 examples with v0 fields.
2. Read `references/v1-architecture.md` to identify the launcher route, supported commands, and core engine ownership.
3. Read `references/v1-configs.md` before editing YAML/JSON because v1 uses a smaller plugin-oriented config surface than v0.
4. Run `scripts/check_v1_config_keys.py CONFIG.yaml` for static mixed-key warnings before proposing a v1 run.
5. Read `references/troubleshooting.md` for v1-specific parser, plugin, kernel, distributed, and dependency failures.

## Bundled Helper

- `scripts/check_v1_config_keys.py` statically inspects YAML or JSON configs without importing LlamaFactory. It reports likely v0-only keys, v1-only keys, missing plugin `name` fields, unsupported enum-like values, and command hints.

## Safety And Scope

- Label v1 as experimental and avoid claiming parity with the default v0 stack.
- Do not translate a complete v0 config mechanically; v1 has different field names, plugin blocks, datasets, trainer coverage, and backend assumptions.
- Do not run downloads, training, distributed launch, or adapter merge unless the user explicitly approves.
- Prefer static inspection and tiny smoke-test suggestions; many native v1 tests require specific accelerator, Transformers, bitsandbytes, FSDP2, DeepSpeed, or kernel support.
