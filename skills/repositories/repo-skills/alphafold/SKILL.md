---
name: alphafold
description: "Route AlphaFold protein structure prediction setup, data
  preparation, local prediction, model configuration, output interpretation, and
  relaxation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold Repo Skill

Use this skill for AlphaFold 2.3.2 repository/package tasks involving protein structure prediction setup, input validation, local inference command planning, model configuration, output confidence interpretation, AlphaFold DB or Server JSON formats, and Amber relaxation.

## Start Here

- Read [`references/package-overview.md`](references/package-overview.md) for the capability map, public prerequisites, and safe/unsafe operation boundaries.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install, import, backend, data, Docker, and hardware failures.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill matches a current AlphaFold checkout or should be refreshed.
- Use [`scripts/check_install.py`](scripts/check_install.py) to inspect an installed AlphaFold environment without running predictions, downloading data, or starting Docker.

## Route by Task

| User task | Go to |
| --- | --- |
| Build Docker/image commands, plan GPU/container requirements, or plan database/model-parameter downloads and updates | [`sub-skills/docker-and-data-setup/SKILL.md`](sub-skills/docker-and-data-setup/SKILL.md) |
| Construct or diagnose direct `run_alphafold` commands, presets, database flags, MSA reuse, relaxation flags, random seeds, and output locations | [`sub-skills/prediction-cli/SKILL.md`](sub-skills/prediction-cli/SKILL.md) |
| Validate FASTA/MSA/template inputs, adapt notebook input validation, or reason about monomer/multimer data-pipeline APIs | [`sub-skills/input-data-and-formats/SKILL.md`](sub-skills/input-data-and-formats/SKILL.md) |
| Inspect model presets/configs, parameter-loading APIs, feature processing, JAX/Haiku/TensorFlow dependency constraints, or backend import errors | [`sub-skills/model-config-and-api/SKILL.md`](sub-skills/model-config-and-api/SKILL.md) |
| Interpret prediction folders, ranked structures, confidence JSON, PAE/pTM/ipTM, AFDB formats, or AlphaFold Server JSON | [`sub-skills/outputs-and-confidence/SKILL.md`](sub-skills/outputs-and-confidence/SKILL.md) |
| Decide whether/how to run Amber relaxation, switch GPU/CPU relax, inspect PDB relaxability, or debug OpenMM/PDBFixer failures | [`sub-skills/relaxation/SKILL.md`](sub-skills/relaxation/SKILL.md) |

## Safe Defaults

- Treat full AlphaFold prediction, Docker builds/runs, database downloads, model-parameter downloads, and AFDB/GCS/BigQuery operations as user-supervised external operations.
- Prefer bundled dry-run helpers first: validate paths, FASTA files, database layout, model presets, confidence files, and relaxation inputs before proposing expensive commands.
- Use `--db_preset=reduced_dbs` only with the small BFD database path; use `--db_preset=full_dbs` only with BFD and UniRef30 paths.
- Use `--model_preset=multimer` only with multimer FASTA inputs and the UniProt plus PDB SeqRes database paths.
- Keep the AlphaFold data directory outside the project/build context to avoid huge Docker builds.

## Minimal Environment Check

Run the bundled diagnostic in the environment where AlphaFold is installed:

```bash
python scripts/check_install.py --check run_alphafold --check docker --check openmm --json
```

A passing import check does not prove that prediction is runnable. Full runs also need model parameters, genetic/template databases, external alignment binaries, writable output storage, and suitable CPU/GPU resources.

## Common Decisions

- Choose `docker-and-data-setup` when the user asks how to install, download, update, mount, or run the documented Docker path.
- Choose `prediction-cli` when the user already has an installed package/environment and wants direct `run_alphafold` command construction or flag diagnosis.
- Choose `input-data-and-formats` when the failure or task is about FASTA contents, multimer chain count, MSA formats, templates, or notebook-style sequence validation.
- Choose `outputs-and-confidence` when the task starts after a prediction folder exists or involves AFDB/Server JSON files.
- Choose `relaxation` when the task mentions Amber, OpenMM, PDBFixer, `models_to_relax`, `use_gpu_relax`, or structural violations.

## Do Not Do Automatically

- Do not start terabyte database downloads or model-weight downloads without explicit user approval.
- Do not run full prediction, benchmark, Docker build, Docker run, or relaxation minimization as a routine verification step.
- Do not assume cached MSAs are valid after the sequence, database, template cutoff, or model preset changes.
- Do not treat AlphaFold Server JSON as input to the local `run_alphafold` CLI; route Server JSON tasks to `outputs-and-confidence`.
