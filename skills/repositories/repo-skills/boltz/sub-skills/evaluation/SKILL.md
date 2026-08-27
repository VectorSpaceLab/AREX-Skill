---
name: evaluation
description: "Evaluate and summarize Boltz prediction outputs, benchmark result
  tables, and legacy OpenStructure-based evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation

Use this sub-skill when the task is to interpret Boltz output metrics, summarize prediction result files, diagnose benchmark/evaluation folder layout, or reason about legacy CASP/PDB evaluation workflows.

## Start Here

- For local prediction-output summaries, use the bundled script: [`scripts/boltz_evaluation_summary.py`](scripts/boltz_evaluation_summary.py).
- For benchmark reproduction planning, read [`references/evaluation-workflows.md`](references/evaluation-workflows.md) before running anything external.
- For confidence, affinity, structural, ligand, and physical-validity metric meanings, read [`references/metrics-and-outputs.md`](references/metrics-and-outputs.md).
- For missing dependencies, unavailable Boltz-2 evaluation assets, folder mismatches, metric mismatches, overlap caveats, and affinity interpretation traps, read [`references/troubleshooting.md`](references/troubleshooting.md).

## Routing Boundaries

- Use this sub-skill for: evaluating Boltz outputs, aggregating evaluation CSVs, interpreting affinity/confidence metrics, CASP/PDB benchmark layout, OpenStructure requirements, and top-1 versus oracle summaries.
- Route raw `boltz predict` setup, YAML/FASTA input authoring, MSA server use, model checkpoints, and inference options to the prediction sub-skill.
- Route training/evaluation jobs launched through PyTorch Lightning or Hydra training configs to the training sub-skill.
- Route CCD, MSA, mmCIF preprocessing, dataset split construction, and benchmark input layout preparation to the data-preparation sub-skill.

## Safe Defaults

- Treat Boltz-2 benchmark evaluation files, setup, and scripts as not yet published when using the documented repository state.
- Treat the available evaluation scripts as legacy Boltz-1 benchmark references unless newer Boltz-2 assets are supplied by the user.
- Do not claim a local confidence or affinity JSON summary is a reproduced structural benchmark; structural benchmark metrics need targets, aligned benchmark folders, and OpenStructure.
