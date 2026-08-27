---
name: prediction
description: "Use Boltz prediction workflows: CLI runs, YAML/FASTA inputs, MSA
  handling, constraints/templates, affinity prediction, cache/backend options,
  and output interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Boltz Prediction

Use this sub-skill when a user asks to run `boltz predict`, draft or validate Boltz input files, configure MSA generation/authentication, predict affinity, inspect prediction outputs, or debug prediction-time failures.

## Start Here

1. Confirm the requested task is prediction, not data preprocessing, training, or benchmark aggregation. For MSA/data-pipeline background route to `../data-preparation/SKILL.md`; for metrics or benchmark analysis route to `../evaluation/SKILL.md`; for top-level routing see `../../SKILL.md`.
2. Prefer YAML inputs for new work. FASTA is still accepted by Boltz but is deprecated and lacks modifications, covalent bonds, pocket conditioning, and affinity.
3. Validate inputs before launching model downloads or GPU work:
   `python sub-skills/prediction/scripts/boltz_input_validator.py INPUT --use-msa-server --check-auth`
4. Build the smallest safe `boltz predict` command first, then add model/runtime flags only when required.

## Common Workflows

- **Single YAML or FASTA:** `boltz predict input.yaml --out_dir predictions --use_msa_server`
- **Directory batch:** `boltz predict inputs/ --out_dir predictions --use_msa_server --override` where the directory contains only `.yaml`, `.yml`, `.fasta`, `.fa`, or `.fas` files and no nested directories.
- **Custom MSA:** set each protein `msa` to `empty`, a `.a3m`, or a paired `.csv`; do not mix omitted/auto MSA proteins with custom MSA proteins in one target.
- **Affinity:** use Boltz-2 YAML with `properties: [{affinity: {binder: L}}]` where `L` is a single-copy small-molecule ligand.
- **Older CUDA/cuEquivariance:** retry with `--no_kernels` when kernel import/compatibility errors appear.

## Reference Map

- `references/prediction-workflows.md` — command recipes, MSA/auth choices, affinity and runtime options.
- `references/input-formats.md` — YAML, FASTA, MSA A3M/CSV, constraints, templates, and validation rules.
- `references/output-formats.md` — prediction directory layout, structure/confidence/affinity files, and interpretation.
- `references/cli-reference.md` — `boltz predict` option groups and safe defaults.
- `references/troubleshooting.md` — common failure signals and fixes.
- `scripts/boltz_input_validator.py` — self-contained preflight validator that avoids model downloads.
