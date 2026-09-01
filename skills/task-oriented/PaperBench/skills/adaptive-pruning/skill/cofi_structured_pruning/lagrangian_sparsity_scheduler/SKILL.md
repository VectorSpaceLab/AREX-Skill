---
name: lagrangian_sparsity_scheduler
description: Compute CoFi target-sparsity warmup, expected sparsity, and Lagrangian penalty/update diagnostics for pruning runs.
---

# lagrangian_sparsity_scheduler

Use this skill when reconstructing the CoFi structured-pruning method or a mechanism-faithful reduced recovery. Do not use it as evidence for full GLUE/SQuAD reproduction unless it is embedded in a real pretrained-model training pipeline.

## Inputs

- Small Python lists or JSON-compatible dictionaries describing model layers, masks, states, sparsity budgets, or proxy batches.
- For recovery, an attempt directory where logs and result files can be written.

## Outputs

- Deterministic dictionaries containing mask composition, sparsity penalties, layer alignments, losses, parameter updates, or recovery traces.
- The scripts never read the original CoFi source repository.

## Workflow

1. Import the script from `scripts/` or invoke it through a recovery harness with the skill `scripts` directories on `PYTHONPATH`.
2. Validate all inputs are tiny, explicit, and JSON-compatible.
3. Execute the CoFi mechanism represented by this module and save any diagnostics needed by downstream recovery.
4. For proxy recovery, clearly mark the run as reduced and keep full-model training booleans false.

## Validation

Run `python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests`.

## Limitations

This skill captures reusable CoFi mechanisms and deterministic tests. It is not a replacement for full BERT fine-tuning, GLUE/SQuAD preprocessing, or GPU latency benchmarking.
