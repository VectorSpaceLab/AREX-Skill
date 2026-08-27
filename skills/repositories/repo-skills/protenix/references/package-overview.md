# Protenix Package Overview

## What Protenix Provides

Protenix is a PyTorch-based biomolecular structure prediction package for AlphaFold 3-style modeling of proteins, DNA, RNA, ligands, ions, covalent bonds, and soft structural constraints. Its public workflows cover prediction, input conversion, protein MSA generation, template search, RNA MSA search, training-data preparation, model training/fine-tuning, and advanced model/backend configuration.

## Package And CLI Surface

- Distribution name: `protenix`
- Package version verified during skill generation: `2.0.0`
- Common import roots: `protenix`, `runner`, `configs`, and selected helper modules under the installed package.
- Console entry point: `protenix`
- Registered commands:
  - `protenix pred`: run structure prediction from Protenix input JSON.
  - `protenix json`: convert PDB/mmCIF/CIF structures into Protenix-compatible JSON.
  - `protenix msa`: run protein MSA search from JSON or FASTA.
  - `protenix mt`: run protein MSA plus template search.
  - `protenix prep`: run protein MSA, template search, and RNA MSA search.

## Dependency And Hardware Profile

Protenix is a heavyweight ML package. The declared runtime stack includes PyTorch, CUDA-oriented packages, cuEquivariance, DeepSpeed, Triton, RDKit, Biopython, Biotite, modelcif, gemmi, fair-esm, ml-collections, and scientific Python dependencies. Package metadata requires Python 3.11 or newer.

Full prediction and training commonly require NVIDIA GPU resources, checkpoints, common chemistry/cache data, and enough memory for the selected model and input size. Many support tasks are safe without GPU access: CLI help, command construction, static JSON validation, layout checks, package metadata inspection, and no-run training/preprocessing planning.

## Workflow Boundaries

- Input authoring and static validation are usually safe and can be done without model downloads or GPU access.
- CLI help, no-run command construction, environment checks, and layout checks are safe read-only operations.
- MSA/template/RNA searches may require HMMER, kalign, MMseqs/ColabFold, large databases, network access, and storage.
- Training data downloads and preprocessing can require large disk capacity and long runtimes.
- Full prediction may download or read checkpoints/cache files and can consume significant GPU memory.
- Kernel/backend debugging can trigger import-time or JIT behavior; use read-only doctors and safe fallbacks before deeper probes.

## Common Entry Decisions

- If the user has not authored input JSON yet, start with `sub-skills/input-data-and-features/SKILL.md`.
- If the user has valid JSON and wants predictions, start with `sub-skills/cli-and-inference/SKILL.md`.
- If JSON refers to missing MSA/template/RNA path fields, start with `sub-skills/msa-template-and-prep/SKILL.md`.
- If the task is about data roots, index CSVs, custom CIF training data, downloads, or launch commands, start with `sub-skills/training-and-data-pipeline/SKILL.md`.
- If the task names kernels, configs, TFG, confidence, metrics, CUDA extension failures, or model internals, start with `sub-skills/advanced-model-configuration/SKILL.md`.
