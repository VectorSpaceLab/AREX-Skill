---
name: cli-and-tools
description: "Operate XTuner legacy command routing, old config-zoo discovery,
  model conversion planning, chat/evaluation/preprocess tools, and
  HuggingFace-trainer examples while separating them from V1 direct CLIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XTuner legacy CLI and tools

Use this sub-skill when a task is about the legacy top-level `xtuner MODE ...` router, old predefined config names, old utility scripts, model conversion command planning, legacy chat/evaluation/preprocess commands, or the HuggingFace `Trainer` example scripts.

Do **not** use this sub-skill for XTuner V1 direct workflows. Route V1 SFT/pretraining/MLLM training to the `training` sub-skill, V1 RL/GRPO to `reinforcement-learning`, V1 JSONL/data protocol details to `data-preparation`, and V1 model/backend sizing to `model-backends`.

## Fast routing rules

- **Legacy CLI**: command begins with `xtuner list-cfg`, `copy-cfg`, `log-dataset`, `check-custom-dataset`, `train`, `test`, `chat`, `convert`, `preprocess`, `mmbench`, `eval_refcoco`, or `list-dataset-format`.
- **V1 direct CLI**: command mentions direct SFT/RL scripts, `--model-cfg`, `--chat_template`, `GRPO`, Ray rollout engines, FSDP/TP/EP/HSDP, or V1 config classes. Route away from this sub-skill.
- **Config-zoo search/copy**: use the bundled helper instead of importing XTuner or reading every config file body.
- **Model conversion**: keep converters as reference-only plans unless the user supplies local model/checkpoint/adapter paths, resource approval, and a safe execution environment.
- **Chat/evaluation/preprocess**: require explicit local assets before execution; these tools can trigger model loads, benchmark reads, or network downloads.

## Operating procedure

1. Classify the task as legacy or V1 using the routing rules above.
2. For old config names, search with `scripts/find_legacy_configs.py` and an explicit config root supplied by the user or environment:

   ```bash
   python scripts/find_legacy_configs.py --config-root /path/to/legacy-configs qlora alpaca --limit 20
   python scripts/find_legacy_configs.py --config-root /path/to/legacy-configs --exact internlm_7b_qlora_alpaca_e3 --copy-to ./configs
   ```

3. For command syntax and tool behavior, consult [legacy CLI reference](references/legacy-cli.md).
4. For `convert pth_to_hf`, `convert merge`, or `convert split`, consult [model conversion reference](references/model-conversion.md) and explain required inputs before proposing execution.
5. Before running legacy tools, verify the executable path. The current package may not install a console entry point named `xtuner`; if `xtuner` is missing, either use a source checkout's legacy tool script explicitly or ask for a checkout/package that includes the legacy router.
6. Apply [troubleshooting](references/troubleshooting.md) for missing command entry points, path-vs-snapshot errors, adapter/base mismatches, benchmark asset gaps, distributed-router surprises, and unsafe network/credential risks.

## Safety and boundaries

- Never assume this generated skill contains XTuner's original config zoo or converter source. It only contains references and a lightweight search/copy helper.
- Do not crawl unrelated directories for configs. Require an explicit `--config-root`.
- Do not run GPU-heavy conversion, chat, training, or evaluation commands without user approval and concrete local paths.
- Do not pass secrets, HuggingFace tokens, or private storage credentials into legacy tools unless the user explicitly scopes how to handle them.
- If a task asks for legacy `xtuner train` mechanics, explain the old command surface here; if it asks for V1 training design, route to `training`.

## Difficult cases this sub-skill supports

- Search old config names for tokens such as `qlora` and `alpaca` from a supplied config root without importing XTuner or loading hundreds of source files.
- Explain why a legacy adapter merge needs a base LLM or CLIP snapshot path, an adapter path, a save path, and optional `--is-clip` for visual-encoder adapters.
