---
name: llama-factory
description: "Use for LlamaFactory repository workflows: training configs,
  dataset/template preparation, model loading/export, inference/API/Web UI
  operations, and experimental USE_V1 flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LlamaFactory

Use this skill when a user asks for help with LlamaFactory (`llamafactory` package, `llamafactory-cli`, or `lmf`) rather than generic Hugging Face training. The default architecture is v0; route to `v1-experimental` only when the user explicitly sets or asks about `USE_V1=1` or v1-style configs.

## Start Here

1. Identify the requested surface: data/template, training config, model/export, inference/API, Web UI/ops, or v1.
2. If the task involves a runnable command, prefer static validation first: inspect config keys, render the intended command, or run a bundled helper with `--help` before starting training, downloads, API servers, or distributed launches.
3. Confirm optional dependencies and hardware before recommending vLLM, SGLang, DeepSpeed, FlashAttention, bitsandbytes, GPTQ, AWQ, HQQ, EETQ, Unsloth, Liger Kernel, KTransformers, NPU, Ray, FSDP, or Megatron-core paths.
4. Keep credentials and local machine paths out of reusable examples: hub tokens, tracker keys, private model paths, and dataset paths should be placeholders.
5. Read `references/troubleshooting.md` for cross-cutting install/import, dependency, CLI, data/config, backend, and environment-variable issues.

## Route By Task

| User request | Use |
| --- | --- |
| Registering datasets, fixing `dataset_info.json`, Alpaca/ShareGPT/OpenAI rows, multimodal columns, tool-calling rows, templates, preprocessing, packed data | `sub-skills/data-and-templates/` |
| Writing or debugging `llamafactory-cli train` YAML/JSON, CLI overrides, LoRA/QLoRA/full/freeze, SFT/PT/RM/PPO/DPO/KTO, distributed launch, logging | `sub-skills/training-and-configs/` |
| Using `ChatModel`, `chat`, `webchat`, `api`, OpenAI-compatible endpoints, streaming, scores, `infer_backend`, vLLM or SGLang inference | `sub-skills/inference-and-serving/` |
| Loading tokenizers/models/processors, adapter setup, LoRA merge/export, quantization, checkpoint conversion/init utilities, hub mirror behavior | `sub-skills/model-loading-and-export/` |
| Installing/running LlamaFactory, `help`, `version`, `env`, LlamaBoard `webui`, operational env vars, monitors, Docker/backend notes | `sub-skills/webui-and-ops/` |
| Experimental v1 trainer/core/plugin/config flows selected with `USE_V1=1` | `sub-skills/v1-experimental/` |

## CLI And Package Facts

- Package/distribution: `llamafactory`.
- Public version in this repo snapshot: `0.9.6.dev0`.
- Console scripts: `llamafactory-cli` and `lmf`, both dispatch to `llamafactory.cli:main`.
- v0 CLI routes include `train`, `chat`, `api`, `export`, `webchat`, `webui`, `env`, `version`, and `help`.
- Multi-GPU training may be wrapped in `torchrun` automatically when multiple devices are visible, or forced with `FORCE_TORCHRUN=1`.
- `USE_V1=1` switches the launcher to the experimental v1 architecture and changes supported commands/config shape.

## Minimal Checks

Use these checks after installing LlamaFactory in a real environment:

```bash
python - <<'PY'
import llamafactory
print(llamafactory.__version__)
PY
llamafactory-cli help
```

If the package is only partially installed, root imports may succeed while workflow imports fail later. Run the sanity helper in `sub-skills/webui-and-ops/scripts/llamafactory_sanity_check.py` to distinguish metadata/import/CLI/dependency problems.

## Bundled Helpers

- `sub-skills/data-and-templates/scripts/validate_dataset_entry.py` checks dataset registry entries and tiny row files without importing LlamaFactory.
- `sub-skills/training-and-configs/scripts/render_train_command.py` merges simple YAML/JSON overrides and prints a safe training command.
- `sub-skills/training-and-configs/scripts/eval_bleu_rouge.py` provides dependency-light prediction metric checks for generated JSONL outputs.
- `sub-skills/inference-and-serving/scripts/openai_api_smoke.py` probes an OpenAI-compatible local API when the user supplies server details.
- `sub-skills/inference-and-serving/scripts/vllm_batch_infer.py` wraps batch inference intent and requires the caller to provide an installed inference environment.
- `sub-skills/model-loading-and-export/scripts/check_export_config.py` flags static export/merge/quantization config pitfalls.
- `sub-skills/webui-and-ops/scripts/llamafactory_sanity_check.py` checks Python/package/CLI availability and common optional modules.
- `sub-skills/v1-experimental/scripts/check_v1_config_keys.py` warns about mixed v0/v1 config keys without importing LlamaFactory.

## Repo-Level References

- `references/repo-provenance.md` records the source snapshot and evidence paths used to build this skill.
- `references/troubleshooting.md` covers cross-cutting failures and points to the nearest owning sub-skill.

## Safety Notes

- Do not run model downloads, training, distributed launches, API servers, Web UI sessions, checkpoint conversion, or export jobs unless the user asks and the environment/hardware are suitable.
- Treat repo examples and tests as evidence, not runtime dependencies for this skill. The bundled references and scripts are the self-contained runtime material.
- For dependency-heavy native verification, use a full LlamaFactory installation with PyTorch and the selected optional backend packages.
