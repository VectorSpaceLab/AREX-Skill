# Protein-ligand workflows

The DiG protein-ligand subtree has the heaviest operational footprint of the
DiG collection. It relies on a prepared dataset layout, checkpoints, Docker or a
matching Conda environment, and very long evaluation windows.

## Dataset and checkpoints

The source material expects:

- a dataset tarball unpacked into the subproject's `src/dataset` directory
- trained checkpoints under `src/saved_checkpoints`
- optional Docker image use for a prebuilt environment

## Single datapoint sampling

The maintained workflow samples multiple conformations for a chosen PDB ID and
then converts coordinates to PDB format.

Operational notes:

- the selection step reads the list of available PDB IDs
- the sampling step is GPU-heavy
- the output is written under the subproject output directory
- cleanup of intermediate positions is part of the source workflow

## Full evaluation

The full evaluation workflow is intentionally long-running and documented as an
approximately 10-hour job on a single A100/A40 GPU.

Operational notes:

- this is not a smoke test
- the workflow is a good candidate for command rendering and review, but not
  for routine execution during skill construction

## Docker path

The source material also documents a Docker-based route:

- load the provided image
- bind-mount the subproject working directory
- activate the prebuilt environment inside the container
- run the same sampling or evaluation logic there

## What to check before a real run

- the dataset and checkpoints are unpacked where the workflow expects them
- the GPU runtime is available if you use the container or a CUDA host
- the PDB ID exists in the dataset manifest when sampling one system
- you have time budget for the long evaluation job

## How this sub-skill treats the workflow

This workflow is primarily reference-only in the generated skill. The command
renderer can explain the sequence and preflight conditions, but the real run
should be treated as a later Researcher task with explicit data and GPU budget.
