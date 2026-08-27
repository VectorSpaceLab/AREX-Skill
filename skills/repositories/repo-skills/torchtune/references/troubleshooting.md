# Cross-Cutting Troubleshooting

Use this reference when a torchtune task fails before it clearly belongs to one sub-skill, or when the same symptom crosses CLI/config, data, model, recipe, checkpoint, and runtime layers.

## Install And Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: torchao not installed` during `import torchtune` | This checkout imports `torchao` at package import time, but `pyproject.toml` does not list it as a runtime dependency | Install `torchao` matching the PyTorch build, then rerun the import check. |
| `import recipes` raises `ModuleNotFoundError` by design | `recipes/__init__.py` intentionally prevents treating recipes as a public package | Use `tune run`, `tune cp`, `tune cat`, `tune validate`, or registry metadata through `cli-and-config`. |
| `tune validate` fails importing a component | The selected config references optional packages such as `bitsandbytes`, `lm_eval`, W&B, Comet, Ray, vLLM, or async RL extras | Decide whether the workflow needs that optional surface; otherwise run shape-only bundled validators or choose a config without that component. |
| A command works in docs but not current checkout | Torchtune is no longer actively maintained and examples may drift | Prefer bundled helper checks plus current registry/config evidence; refresh this skill if source provenance differs. |

## Expensive Or Unsafe Workflows

Before running any `tune run` command that trains, evaluates, generates, quantizes, downloads model files, starts distributed workers, or uses external services:

1. Confirm model/checkpoint/tokenizer paths and credentials.
2. Confirm device, dtype, GPU memory, distributed world size, and output directory.
3. Build a non-executing command with the relevant bundled helper.
4. Run `tune validate` only when optional component dependencies are installed.
5. Ask before starting network, gated-download, multi-GPU, cluster, long-running, or destructive-output work.

## Current-Code Notes From Live Inspection

- `torchtune.rlhf.loss` import failed in this checkout because `torchtune/rlhf/loss/dpo.py` references typing/dataclass names before importing them. The runtime skill records this as a current-code issue; use public `torchtune.rlhf` utilities and source/test evidence for RLHF routing until the repo is refreshed or repaired.
- The package version from `version.txt` is `0.7.0`, while editable installed metadata reports `0.0.0` because `torchtune.__version__` is empty in the checkout. Treat provenance commit and evidence paths as the stronger freshness signal.
- A setup helper can report a false import-root failure for `recipes`; this is expected because packaging metadata lists `recipes` as top-level while `recipes/__init__.py` intentionally raises.

## Sub-Skill Escalation

- CLI syntax, registry, config overrides, and component validation: `../sub-skills/cli-and-config/SKILL.md`.
- JSONL/message/dataset shape, packing, image rows, and collators: `../sub-skills/data-and-datasets/SKILL.md`.
- Training recipe choice, distributed launch, QLoRA/QAT/KD/DPO/PPO: `../sub-skills/post-training-recipes/SKILL.md`.
- Generation, Eleuther evaluation, quantization, and checkpoint-to-inference routing: `../sub-skills/inference-evaluation-quantization/SKILL.md`.
- Model builders, tokenizers, adapters, losses, conversion, and module APIs: `../sub-skills/models-and-modules/SKILL.md`.
- Checkpointing, precision, memory/distributed utilities, logging/profiling, RLHF/GRPO runtime checks: `../sub-skills/training-utilities-and-rlhf/SKILL.md`.
