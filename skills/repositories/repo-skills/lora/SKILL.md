---
name: lora
description: "Use the LoRA repository and loralib package to add low-rank
  adapters to PyTorch modules, fine-tune RoBERTa or DeBERTa on GLUE tasks, or
  reproduce the repository's GPT-2 data-to-text workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LoRA

Use this repo skill when a task involves the `loralib` PyTorch package, low-rank
adaptation, LoRA-only checkpoints, trainable-parameter selection, merged
attention projections, RoBERTa/DeBERTa GLUE fine-tuning, or the repository's
GPT-2 E2E/WebNLG/DART examples.

## First checks

- Read [repository provenance](references/repo-provenance.md) before deciding
  whether this skill still matches a checkout or should be refreshed.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) for
  missing PyTorch, state-dict mismatches, optional dependencies, CUDA/data
  assumptions, and stale-skill concerns.
- Run the safe [core smoke helper](scripts/check_lora_core.py) before changing
  a model or debugging an import. It uses a tiny CPU fixture and does not
  download models, data, or checkpoints.
- Install the distribution with `python -m pip install loralib`; for a local
  source checkout, `python -m pip install -e .` is the editable equivalent.
  The public import is `import loralib as lora`.

## Route by task

- **Direct PyTorch integration**: read
  [core-lora-api](sub-skills/core-lora-api/SKILL.md) for `Linear`, `Embedding`,
  `MergedLinear`, convolution wrappers, trainable-parameter marking, LoRA-only
  checkpoint state, bias policies, fan-in/fan-out weights, and eval-time
  merging.
- **RoBERTa/DeBERTa GLUE**: read
  [nlu-glue-adaptation](sub-skills/nlu-glue-adaptation/SKILL.md) for the
  LoRA-specific `run_glue.py` flags, query/value insertion points, checkpoint
  transfer, launcher construction, and CUDA/multi-GPU caveats.
- **GPT-2 data-to-text**: read
  [nlg-gpt2-adaptation](sub-skills/nlg-gpt2-adaptation/SKILL.md) for
  `MergedLinear` QKV adaptation, E2E/WebNLG/DART JSONL formats, training and
  beam-search command construction, decoding, and evaluation-file validation.

## Shared operating rules

1. Decide whether the task is package use or repository maintenance. The
   generated skill is self-contained; do not require the original checkout for
   ordinary package use.
2. Keep the base model weights separate from the LoRA state. Load the base
   checkpoint first, then load LoRA parameters with `strict=False`; save only
   the adapter state when the goal is a small task-specific artifact.
3. Treat `r=0` as the no-adapter case. A positive rank creates `lora_A` and
   `lora_B`; `lora_alpha / r` is the scaling factor.
4. Treat the large NLU/NLG recipes as optional, resource-heavy workflows. They
   assume model/data downloads and, for the documented benchmark settings,
   CUDA and distributed launchers. Do not claim benchmark reproduction from a
   CPU import or a command-only check.
5. Prefer the bundled helpers and the references in this skill over opening
   source-repository scripts. The original shell scripts are evidence, not
   runtime dependencies.

## Quick smoke check

```bash
python scripts/check_lora_core.py --json
```

The helper checks the public import, tiny forwards for the supported layer
families, eval/train merge transitions, trainable-parameter filtering, and the
keys returned by `lora_state_dict`. Read its sub-skill references before
changing defaults or using a nonstandard bias policy.

## Common request patterns

Use this skill for requests such as:

- "add LoRA to this PyTorch model"
- "save only the adapter weights"
- "why do my LoRA keys not load"
- "build the GLUE LoRA command"
- "prepare the GPT-2 LoRA data-to-text flow"

If the user asks for a specific route, jump directly to the owning sub-skill
instead of reading all three routes. If the user asks for a general question
about rank, scaling, or merged weights, start in `core-lora-api`.

## Out of scope

This skill does not replace modern PEFT/Transformers documentation, does not
ship model weights or benchmark datasets, and does not make external download,
Java/perl metric, credential, or multi-GPU actions safe by default. Those
limits are intentional so future agents can reuse the guidance without
mistaking historical benchmark settings for always-safe defaults.
