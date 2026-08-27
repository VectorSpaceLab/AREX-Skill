---
name: colabfold
description: "Use ColabFold for protein structure prediction workflows: validate
  FASTA/CSV/A3M inputs, generate MSAs, plan batch predictions, inspect outputs,
  and troubleshoot optional AlphaFold, MMseqs2, JAX, GPU, and OpenMM
  dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ColabFold

Use this skill when a task involves ColabFold local or notebook-derived workflows: preparing sequence inputs, generating MSAs, planning or running `colabfold_batch`, exporting AlphaFold3 JSON, inspecting prediction outputs, or diagnosing ColabFold dependency and backend failures.

## Start Here

1. Check whether the task is about the current source checkout or general ColabFold usage. If freshness matters, read [`references/repo-provenance.md`](references/repo-provenance.md).
2. Choose the narrowest install route from [`references/installation-and-backends.md`](references/installation-and-backends.md).
3. Use the sub-skill that owns the user-facing workflow; do not send future agents to original repository notebooks, tests, scripts, or docs.
4. Run a bundled dry-run or read-only diagnostic before expensive network, database, GPU, prediction, or relaxation work.

## Install Routes

- **Search/input inspection only**: install base ColabFold, which provides input helpers plus `colabfold_search` and `colabfold_split_msas`.
- **Structure prediction**: install prediction extras such as `colabfold[alphafold]` and a JAX build compatible with the target CPU/GPU.
- **Amber relaxation**: install OpenMM/PDBFixer support such as `colabfold[openmm]` and verify the CPU/GPU OpenMM platform before using `--use-gpu`.
- **Local database search**: install MMseqs2 separately and prepare the ColabFold databases; database setup is large and should be explicitly approved.

Minimal import check:

```bash
python - <<'PY'
import importlib.metadata as md
print(md.version("colabfold"))
PY
```

Optional environment diagnostic:

```bash
python scripts/check_colabfold_environment.py --check-entry-points --json
```

## Route by Task

- **Inputs and formats**: use [`sub-skills/inputs-and-formats/SKILL.md`](sub-skills/inputs-and-formats/SKILL.md) for FASTA, CSV, A3M, AF3 molecule syntax, parser behavior, PDB/mmCIF input extraction, and validation with `validate_colabfold_input.py`.
- **MSA search**: use [`sub-skills/msa-search/SKILL.md`](sub-skills/msa-search/SKILL.md) for public MSA server use, `colabfold_search`, local MMseqs2 databases, GPU/gpuserver search, split/merge helpers, AF3 JSON from MSAs, and local MSA server planning.
- **Batch prediction**: use [`sub-skills/batch-prediction/SKILL.md`](sub-skills/batch-prediction/SKILL.md) for `colabfold_batch`, MSA-only then prediction staging, templates, model flags, parameter downloads, GPU/JAX planning, and AF3 JSON-only export.
- **Relaxation and outputs**: use [`sub-skills/relaxation-and-outputs/SKILL.md`](sub-skills/relaxation-and-outputs/SKILL.md) for `colabfold_relax`, OpenMM/PDBFixer choices, output directory inspection, score/PAE/pLDDT interpretation, plots, citations, and extra pTM/interface metrics.

## Shared References and Scripts

- [`references/installation-and-backends.md`](references/installation-and-backends.md) explains package extras, external binaries, database storage, GPU/JAX/OpenMM choices, and safe verification.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting install/import, network/server, database, GPU, and optional dependency failures; sub-skills add workflow-specific details.
- [`scripts/check_colabfold_environment.py`](scripts/check_colabfold_environment.py) is a read-only diagnostic for package metadata, imports, console entry points, optional dependencies, MMseqs2, and GPU signals.

## Safety and Resource Rules

- Do not run public MSA server queries, large local database setup, model parameter downloads, GPU predictions, or relaxation unless the user has approved the resource use.
- Treat original notebooks and tests as evidence only. Runtime instructions in this skill rely on bundled references and scripts.
- Prefer dry-run command planning and read-only validators before mutating output directories or launching long computations.
- If a requested workflow requires credentials, private sequences, large databases, or unavailable hardware, explain the missing prerequisite and provide a safe fallback or skip decision.
