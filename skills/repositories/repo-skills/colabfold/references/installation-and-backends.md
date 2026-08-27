# Installation and Backends

Read this when choosing a ColabFold install variant, preparing a machine for prediction, or diagnosing missing optional dependencies.

## Package Layers

| Need | Install scope | What it enables | What it does not prove |
| --- | --- | --- | --- |
| Input parsing and local MSA CLI planning | `pip install colabfold` | `colabfold`, input helpers, `colabfold_search`, `colabfold_split_msas` | full `colabfold_batch` prediction |
| Structure prediction | `pip install colabfold[alphafold]` plus compatible JAX | `colabfold_batch`, AlphaFold model code, prediction orchestration | local MMseqs2 databases, GPU driver compatibility, model parameter presence |
| Relaxation | `pip install colabfold[openmm]` | `colabfold_relax` and Amber/OpenMM paths | GPU OpenMM support unless separately verified |
| Local database search | MMseqs2 binary plus ColabFold DB files | `colabfold_search` against local databases | database download/storage safety or service deployment |

ColabFold's package metadata exposes console scripts: `colabfold_batch`, `colabfold_search`, `colabfold_split_msas`, and `colabfold_relax`. Some scripts import optional dependencies at startup.

## Safe Verification

Use the root checker first:

```bash
python scripts/check_colabfold_environment.py --check-entry-points
```

For prediction environments, add explicit checks for:

- `alphafold` import success.
- JAX import success and backend/device visibility.
- model parameter directory availability before large downloads.
- enough GPU memory for the sequence length and model count.

For relaxation environments, add explicit checks for:

- `openmm` and `pdbfixer` import success.
- whether the requested OpenMM platform is available.
- whether CPU relaxation is acceptable if GPU OpenMM fails.

For local MSA environments, add explicit checks for:

- `mmseqs` on `PATH` or a user-provided `--mmseqs` path.
- database marker files such as `.dbtype`, optional `.idx`, and GPU index expectations.
- available storage and RAM before starting database setup.

## Backend Decisions

- Do not require CUDA just because a GPU exists. CPU/base inspection is enough for parser and command-planning tasks.
- Require GPU/JAX verification when the user asks to run prediction locally or tune GPU execution.
- For `colabfold_search --gpu 1`, keep `CUDA_VISIBLE_DEVICES` consistent between `gpuserver` and search commands.
- `--db-load-mode 2` is useful when databases are already resident/preloaded; it is not a substitute for a correct database layout.
- Amber relaxation can be long-running. Use CPU unless OpenMM GPU support is known to work and the user wants it.

## Resource Approvals

Ask or explicitly confirm before:

- downloading ColabFold databases or model parameters;
- querying a public MSA server with private or high-throughput sequences;
- launching long GPU prediction or relaxation jobs;
- starting or modifying a local MSA server or systemd service;
- installing broad extras or changing an existing user-managed environment.
