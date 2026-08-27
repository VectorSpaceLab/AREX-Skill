---
name: batch-prediction
description: "Plan and run ColabFold batch structure prediction workflows,
  including model choice, MSA-only/prediction splits, templates, AF3 JSON
  export, outputs, and prediction dependency failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Batch Prediction

Use this sub-skill when the user needs to run or plan `colabfold_batch` structure prediction, split MSA generation from GPU prediction, choose model/runtime flags, export AlphaFold3 JSON from ColabFold inputs, interpret prediction outputs, or recover from missing AlphaFold/JAX/GPU/parameter prerequisites.

## Route First

- For FASTA, CSV, A3M, AF3 non-protein syntax, query naming, or input validation, route to `../inputs-and-formats/SKILL.md`.
- For `colabfold_search`, local MMseqs2 databases, split/merge MSA directories, or MSA server deployment, route to `../msa-search/SKILL.md`.
- For Amber relaxation after prediction, `colabfold_relax`, output inspection, citations, and visualization details, route to `../relaxation-and-outputs/SKILL.md`.

## Core References

- Start with `references/cli-reference.md` for safe `colabfold_batch` command construction.
- Use `references/workflows.md` for common one-step, two-step, template, complex, and AF3 JSON workflows.
- Use `references/model-and-output-reference.md` for model type selection, parameter files, ranking metrics, and expected output files.
- Use `references/troubleshooting.md` when prediction fails before or during AlphaFold/JAX execution.

## Safe Planning Helper

Use the bundled dry-run helper to produce commands without running predictions, querying servers, or downloading model parameters:

```bash
python scripts/plan_colabfold_batch_command.py input_sequences.fasta out_dir --complex --two-step --templates --use-pallas
```

The helper only validates paths syntactically and prints command lines plus prerequisite notes. Treat generated commands as a plan: review hardware, input ownership, server policy, and output paths before execution.

## Default Prediction Rules

- Install the prediction extras before structure prediction: `pip install colabfold[alphafold]` plus a compatible `jax` build for the target CPU/GPU.
- `colabfold_batch input.fasta results/` queries the MSA server when the input lacks embedded A3M/MSA data and then runs prediction.
- `--msa-only` sets prediction models to zero and writes reusable MSA/template intermediates instead of structures.
- Re-running `colabfold_batch input.fasta results/` after `--msa-only` uses the output directory to continue into prediction.
- `--af3-json` generates AlphaFold3-compatible JSON and returns without structure prediction.
- `--model-type auto` resolves to `alphafold2_ptm` for monomers and `alphafold2_multimer_v3` for complexes.

## Safety Notes

- Do not run heavyweight model downloads, GPU predictions, public MSA server queries, or local database searches unless the user has approved those resources.
- Do not reference original repository notebooks, tests, or checkout paths at runtime; this sub-skill distills their behavior into the bundled references.
- Prefer planning commands first, then running the smallest representative job before scaling a batch.
