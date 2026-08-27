---
name: prediction-cli
description: "Guide local AlphaFold prediction CLI workflows, flags, presets,
  MSA reuse, relaxation choices, random seeds, and output expectations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold Prediction CLI

Use this sub-skill when an agent needs to construct, review, or diagnose a local installed `run_alphafold` prediction command without launching full inference.

## Read First

- Start with [references/cli-reference.md](references/cli-reference.md) for required flags, preset compatibility, database path expectations, and output file patterns.
- Use [references/workflows.md](references/workflows.md) for complete direct-CLI command templates, MSA reuse, random seed handling, and Docker-to-direct CLI conversion.
- Use [references/troubleshooting.md](references/troubleshooting.md) when a command fails before inference, produces surprising output folders, or misuses relaxation, benchmark, or MSA reuse flags.
- Run [scripts/check_prediction_inputs.py](scripts/check_prediction_inputs.py) to validate FASTA paths, duplicate target names, preset/database flag combinations, path expectations, and common safety caveats before proposing an inference run.

## Routing Boundaries

- Route Docker image builds, container mounts, GPU runtime setup, and data download planning to `../docker-and-data-setup/`.
- Route FASTA contents, sequence/MSA/template formats, parser behavior, and chain validation to `../input-data-and-formats/`.
- Route PDB/mmCIF files, `ranking_debug.json`, pLDDT, pTM, ipTM, and PAE interpretation to `../outputs-and-confidence/`.
- Route Amber/OpenMM internals, relaxation backend failures, and structural violation details to `../relaxation/`.

## Safe Operating Rules

- Do not run full AlphaFold inference as a validation step; it can require large databases, external tools, GPU memory, and hours of runtime.
- Prefer validating a command with the bundled dry-run checker, then hand the command to the user with explicit resource and database assumptions.
- Keep `--fasta_paths` basenames unique because each FASTA stem becomes the target output subdirectory.
- Treat `--use_precomputed_msas=true` as a manual cache-reuse decision; AlphaFold does not prove the cached MSAs match the current sequence, databases, or flags.
- Treat `--random_seed` as a reproducibility aid, not a determinism guarantee, because GPU inference and input data changes can still alter results.
