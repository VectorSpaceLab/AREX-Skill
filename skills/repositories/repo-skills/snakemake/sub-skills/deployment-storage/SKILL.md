---
name: deployment-storage
description: "Plan and diagnose Snakemake 9.23.1 software deployment,
  containers, storage providers, caches, archives, and executor jobscript
  deployment surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deployment and Storage

Use this sub-skill when a Snakemake workflow needs reproducible software stacks, external storage, cluster/cloud deployment surfaces, source deployment, caches, or archives.

## Route here for

- Choosing `--software-deployment-method` / `--sdm`, `--use-conda`, `--use-apptainer`, or `--use-envmodules` for a workflow run.
- Writing or diagnosing `conda:`, global `conda:`, `.pin.txt`, `.post-deploy.sh`, `container:`, `containerized:`, and `envmodules:` directives.
- Planning storage provider usage with `--default-storage-provider`, `--default-storage-prefix`, `storage:` blocks, `storage.<tag>(...)`, `local(...)`, access flags, credentials, or local-copy behavior.
- Handling `--shared-fs-usage`, non-shared executor storage/cache/source deployment, `--jobscript`, `--jobname`, or job properties embedded in jobscripts.
- Creating or reviewing workflow archives with `--archive`, container specs with `--containerize`, and between-workflow output caching with `SNAKEMAKE_OUTPUT_CACHE` / `--cache`.

## Start with

- Deployment commands and directive patterns: [references/deployment-reference.md](references/deployment-reference.md).
- Storage provider and filesystem behavior: [references/storage-reference.md](references/storage-reference.md).
- Failure diagnosis and recovery checklists: [references/troubleshooting.md](references/troubleshooting.md).
- Jobscript property inspection: run `python scripts/inspect_job_properties.py --help`.

## Boundaries

- General CLI construction, target selection, profiles, and core execution planning belong to the root skill or command/execution sub-skills.
- Python API and plugin authoring details belong to `../python-api-plugins/SKILL.md`.
- Reports, linting, benchmark interpretation, and test debugging belong to `../debugging-reporting/SKILL.md`.
- Language syntax for ordinary rules, wildcards, inputs, and outputs belongs outside this sub-skill unless it directly affects deployment or storage behavior.

## Snakemake 9.23.1 cautions

- Prefer `--software-deployment-method conda apptainer` (or `--sdm conda apptainer`) over older mental models that treat deployment flags as unrelated toggles.
- `--use-conda`, `--use-apptainer` / `--use-singularity`, and `--use-envmodules` remain accepted convenience flags for the corresponding deployment methods.
- Do not suggest `--reason`; it is not a valid Snakemake 9.23.1 flag, although dry-run output still reports reasons for jobs.
- External tools and plugins are not bundled by Snakemake itself: conda, Apptainer/Singularity, storage plugins, executor plugins, credentials, and cluster/cloud commands must be present in the target runtime.
