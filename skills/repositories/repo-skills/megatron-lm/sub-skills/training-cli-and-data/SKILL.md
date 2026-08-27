---
name: training-cli-and-data
description: "Build Megatron-LM training commands, data preprocessing flows,
  launch templates, and training diagnostics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# training-cli-and-data

Use this sub-skill when the user asks to launch or debug Megatron-LM training, prepare text data, use mock data, scale data loading, or translate model/data/parallelism choices into a safe command.

## Read first

- For pretraining launch patterns, torchrun/SLURM/container templates, model-family examples, and validation outputs, read [references/training-workflows.md](references/training-workflows.md).
- For JSONL preprocessing, dataset merge/cache, object storage, and data-loader scale flags, read [references/data-workflows.md](references/data-workflows.md).
- For NCCL, tokenizer, data-cache, shape/batch, and launch failures, read [references/troubleshooting.md](references/troubleshooting.md).
- Use [scripts/render_pretrain_command.py](scripts/render_pretrain_command.py) to create a conservative command template.
- Use [scripts/create_tiny_preprocess_fixture.py](scripts/create_tiny_preprocess_fixture.py) to make a tiny JSONL fixture and display a preprocessing command.
- Use [scripts/run_minimal_mcore_smoke.sh](scripts/run_minimal_mcore_smoke.sh) only when a CUDA-capable Megatron environment and at least two GPUs are available.

## Route by task

| Task | Action |
|---|---|
| "Run a first training smoke" | Start with mock data and a tiny number of iterations; validate environment first with install-and-environment. |
| "Prepare my data" | Confirm JSONL keys/tokenizer, generate `.bin/.idx`, optionally merge and prebuild cache. |
| "Scale to multi-node" | Confirm shared worktree/data/checkpoint paths, compute TP/PP/CP/DP via core-models, then render torchrun/SLURM command. |
| "Training hangs at startup" | Distinguish dataset-cache barrier from NCCL/process group failure. |
| "Use LLaMA/Mixtral/Mamba/T5/BERT recipe" | Extract the model-family flags and validate hardware/optional dependency assumptions before launch. |

## Command construction checklist

1. Pull the user's desired model family, data source, checkpoint state, hardware, precision, and target runtime.
2. Route topology decisions to [../core-models-and-parallelism/SKILL.md](../core-models-and-parallelism/SKILL.md) before finalizing TP/PP/CP/EP/FSDP.
3. Decide data mode:
   - `--mock-data` for environment/performance ceiling checks.
   - Preprocessed `.bin/.idx` prefixes for real GPT-style data.
   - SFT/FIM/multimodal modes only when their schemas are explicitly selected.
4. Add save/load/log/tensorboard paths and intervals.
5. Use `python -m torch.distributed.run` / `torchrun` consistently with the selected environment.
6. Validate with a short run before increasing steps, GPUs, or model size.

## Boundaries

- Install/backend readiness is owned by [../install-and-environment/SKILL.md](../install-and-environment/SKILL.md).
- Model/config object details are owned by [../core-models-and-parallelism/SKILL.md](../core-models-and-parallelism/SKILL.md).
- Checkpoint format conversion and GPT-Hybrid migration are owned by [../checkpointing-and-conversion/SKILL.md](../checkpointing-and-conversion/SKILL.md).
- CI recipe/golden-value workflows are owned by [../testing-ci-and-maintenance/SKILL.md](../testing-ci-and-maintenance/SKILL.md).
