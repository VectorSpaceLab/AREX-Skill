---
name: torchtune
description: "Use torchtune for PyTorch-native LLM post-training, recipe/config
  workflows, datasets, models, evaluation, quantization, checkpointing, and RLHF
  utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# torchtune

Use this repo skill when a task names torchtune, the `tune` CLI, torchtune recipes/configs, PyTorch-native LLM post-training, LoRA/QLoRA/DPO/PPO/KD/QAT workflows, torchtune datasets, model builders, generation, Eleuther evaluation, quantization, checkpointing, or torchtune RLHF utilities.

Torchtune development wound down in 2025, so prefer current checkout/package evidence over older examples. This skill captures the repository state in [repo provenance](references/repo-provenance.md); read it before deciding whether the skill needs refresh.

## Install And Import Check

For public use, install the documented PyTorch prerequisites and torchtune package in an isolated environment:

```bash
pip install torch torchvision torchao
pip install torchtune
python - <<'PY'
import torchtune
from torchtune._recipe_registry import get_all_recipes
print("torchtune import ok", len(get_all_recipes()), "recipes")
PY
tune --help
```

Notes:

- `torchao` is required at top-level import time in this checkout; install it alongside PyTorch even though it is not listed in `pyproject.toml` runtime dependencies.
- Use CPU import checks for documentation/config work. Actual training, generation, evaluation, and quantization can require GPUs, large checkpoints, gated model credentials, optional packages, and explicit user approval.
- Do not import the `recipes` package directly. Torchtune intentionally raises from `recipes/__init__.py`; launch recipes through `tune run`, inspect with `tune cat`, copy with `tune cp`, or use registry metadata.

## Route By Task

| User task | Read |
| --- | --- |
| Use `tune ls`, `tune cp`, `tune cat`, `tune validate`, `tune run`, model download flags, config overrides, `_component_`, or registry inspection | [cli-and-config](sub-skills/cli-and-config/SKILL.md) |
| Build or validate dataset configs, message rows, prompt templates, packing, multimodal rows, preference data, or collators | [data-and-datasets](sub-skills/data-and-datasets/SKILL.md) |
| Select/adapt SFT, full finetune, LoRA/QLoRA/DoRA, DPO, PPO, KD, QAT, distributed, or multi-node training recipes | [post-training-recipes](sub-skills/post-training-recipes/SKILL.md) |
| Generate text, run EleutherAI evaluation, quantize checkpoints, or route trained checkpoints into eval/generation | [inference-evaluation-quantization](sub-skills/inference-evaluation-quantization/SKILL.md) |
| Choose public model/tokenizer builders, PEFT modules, LoRA utilities, losses, model conversion helpers, or module APIs | [models-and-modules](sub-skills/models-and-modules/SKILL.md) |
| Debug checkpointing, precision, memory/distributed utilities, schedulers, logging/profiling, RLHF helpers, or experimental GRPO/async RL boundaries | [training-utilities-and-rlhf](sub-skills/training-utilities-and-rlhf/SKILL.md) |

## Safe Workflow

1. Start in [cli-and-config](sub-skills/cli-and-config/SKILL.md) to inspect registry names, copy configs, and build non-executing command shapes.
2. Validate data shape in [data-and-datasets](sub-skills/data-and-datasets/SKILL.md) before wiring datasets into recipe configs.
3. Choose recipe/config families in [post-training-recipes](sub-skills/post-training-recipes/SKILL.md), using bundled command builders before launching expensive jobs.
4. Use [models-and-modules](sub-skills/models-and-modules/SKILL.md) when configs need model/tokenizer/adapter public dotpaths.
5. Use [training-utilities-and-rlhf](sub-skills/training-utilities-and-rlhf/SKILL.md) for checkpoint, dtype, distributed, logging, profiling, and RLHF runtime details.
6. After a checkpoint exists, use [inference-evaluation-quantization](sub-skills/inference-evaluation-quantization/SKILL.md) for generation/eval/quantization plans.

## Bundled Helpers

- `sub-skills/cli-and-config/scripts/inspect_tune_registry.py` lists built-in recipes/configs without importing recipe modules.
- `sub-skills/cli-and-config/scripts/validate_config_shape.py` applies torchtune-style overrides/removals and reports `_component_` nodes without launching recipes.
- `sub-skills/data-and-datasets/scripts/validate_messages_jsonl.py` validates small JSONL message/input-output/chat/preference fixtures without importing torch.
- `sub-skills/post-training-recipes/scripts/build_tune_command.py` prints safe `tune run` training commands without executing them.
- `sub-skills/inference-evaluation-quantization/scripts/build_inference_eval_command.py` prints safe generate/eval/quantize commands without model work.
- `sub-skills/models-and-modules/scripts/inspect_model_builders.py` lists public model-family callable exports without instantiating large models.
- `sub-skills/training-utilities-and-rlhf/scripts/check_training_runtime.py` reports torch/CUDA/torchao/torchtune/RLHF import health without distributed initialization.

## Guardrails

- Do not run training, download gated models, start distributed jobs, initialize Ray/vLLM, run Eleuther tasks, or quantize checkpoints without explicit approval and confirmed resources.
- Do not embed Hugging Face/Kaggle tokens, local cache paths, checkpoint directories, environment names, or machine-specific paths in reusable configs.
- Do not tell future agents to open or run original repo docs, tests, recipe files, or configs. Use the bundled references/scripts in this skill.
- Treat `torchtune.dev` and async RL/GRPO surfaces as experimental and optional-extra dependent.
- If current repo code, public configs, CLI behavior, dependencies, or docs differ from [repo provenance](references/repo-provenance.md), run `refresh-repo-skill` before relying on this skill.

## Shared References

- [Repository provenance](references/repo-provenance.md) records the source snapshot and refresh baseline.
- [Routing metadata](references/repo-routing-metadata.json) is consumed by `repo-skills-router` during managed import.
- [Cross-cutting troubleshooting](references/troubleshooting.md) covers install/import, optional dependencies, stale registry snapshots, and known current-code issues.
