---
name: core-models-and-parallelism
description: "Use Megatron Core model APIs, process groups, and parallelism/FSDP
  choices safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# core-models-and-parallelism

Use this sub-skill when the user is constructing Megatron Core modules, choosing TP/PP/CP/EP/DP/FSDP layouts, reviewing model-provider code, or diagnosing model-parallel/process-group errors.

## Read first

- For public objects, signatures, and relationships, read [references/api-reference.md](references/api-reference.md).
- For TP/PP/CP/EP/DP/FSDP formulas and decision rules, read [references/parallelism-reference.md](references/parallelism-reference.md).
- For shape, divisibility, process-group, FSDP, CUDA stream, and optional-kernel issues, read [references/troubleshooting.md](references/troubleshooting.md).
- To inspect live API availability in an installed environment, run [scripts/inspect_core_api.py](scripts/inspect_core_api.py).

## Route by task

| Task | Route |
|---|---|
| Build a tiny GPT/Hybrid model or inspect `TransformerConfig` | Use [references/api-reference.md](references/api-reference.md). |
| Select parallel sizes for a training job | Use [references/parallelism-reference.md](references/parallelism-reference.md), then hand launch details to [../training-cli-and-data/SKILL.md](../training-cli-and-data/SKILL.md). |
| Diagnose TP/PP/CP/EP/FSDP shape errors | Start with [references/troubleshooting.md](references/troubleshooting.md). |
| Convert GPTModel checkpoints or migrate to HybridModel | Route to [../checkpointing-and-conversion/SKILL.md](../checkpointing-and-conversion/SKILL.md). |
| Use high-level dynamic inference APIs | Route to [../inference-and-serving/SKILL.md](../inference-and-serving/SKILL.md). |

## Core workflow

1. Pull the user's artifact first: model-provider function, config dataclass, parallel sizes, training command, traceback, or checkpoint metadata.
2. Determine whether the task is a library API task or a Megatron-LM training entrypoint task.
3. Check the total topology:

   ```text
   total GPUs = TP × PP × CP × DP
   MoE adds EP constraints; expert/data dimensions must still be compatible.
   ```

4. Validate divisibility: hidden size and attention heads with TP, layer counts with PP/layout, sequence length with CP, experts with EP/ETP.
5. Check backend constraints before recommending flags. For example, `CUDA_DEVICE_MAX_CONNECTIONS=1` helps some pre-Blackwell TP/CP non-FSDP paths but is wrong for FSDP and expert-overlap cases.
6. If the answer becomes a launch command, cross-link to `training-cli-and-data` so data/checkpoint/logging details are handled there.

## Key facts

- `GPTModel` remains available but emits a deprecation warning: new architecture work should consider HybridModel and the migration route.
- Current `GPTModel` construction requires a `TransformerConfig`, a layer `ModuleSpec`, `vocab_size`, and `max_sequence_length`.
- `TransformerConfig` extends model-parallel configuration; many constructor fields control TP/PP/CP/EP/FSDP as well as transformer architecture.
- Prefer passing explicit process groups or `ProcessGroupCollection` through library code rather than adding new direct global process-group reads in `megatron/core` production code.

## Boundaries

This sub-skill owns model/core API and topology reasoning. It does not own data preprocessing, command-line launch assembly, checkpoint conversion, or CI test selection.
