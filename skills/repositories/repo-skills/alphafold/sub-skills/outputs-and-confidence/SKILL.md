---
name: outputs-and-confidence
description: "Inspect AlphaFold output folders, confidence JSON, ranked
  structures, AFDB files, and AlphaFold Server JSON schemas."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold Outputs and Confidence

Use this sub-skill when a task is about interpreting AlphaFold prediction artifacts after a run, checking confidence files, converting or parsing PDB/mmCIF structures, understanding AlphaFold DB files, or preparing AlphaFold Server JSON job requests.

## Start Here

- Read [`references/output-formats.md`](references/output-formats.md) to identify `run_alphafold` target-folder artifacts, ranked models, confidence files, PAE files, mmCIF/PDB outputs, timing files, and missing-output clues.
- Read [`references/api-reference.md`](references/api-reference.md) for `alphafold.common.confidence` and `alphafold.common.protein` API contracts, shapes, JSON dialects, and structure conversion limits.
- Read [`references/afdb-reference.md`](references/afdb-reference.md) for AlphaFold DB file naming, confidence formats, metadata files, GCS/BigQuery access patterns, licensing, and cost warnings.
- Read [`references/server-json.md`](references/server-json.md) and the bundled fixture [`references/server-example.json`](references/server-example.json) when creating or validating AlphaFold Server job JSON.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for pLDDT/PAE shape errors, PDB chain limits, mmCIF conversion surprises, missing output artifacts, AFDB costs, and Server JSON dialect mistakes.
- Run [`scripts/inspect_confidence_json.py`](scripts/inspect_confidence_json.py) to summarize local `confidence_*.json` and `pae_*.json` files without importing AlphaFold.

## Routing Boundaries

- Use this sub-skill for output directory inspection, ranked model interpretation, PDB/mmCIF conversion facts, pLDDT/PAE/pTM/ipTM explanation, AFDB formats, and AlphaFold Server JSON schemas.
- Route command construction, model/database preset choices, random seeds, MSA reuse decisions, and prediction execution to `../prediction-cli/`.
- Route FASTA, MSA, template, sequence validation, and AlphaFold Server protein input sequence rules to `../input-data-and-formats/`.
- Route Amber/OpenMM relaxation internals, relaxation backend failures, and structural violation metrics to `../relaxation/`.
- Route Docker, database downloads, data directory layout, and cloud/network operations to `../docker-and-data-setup/`.

## Safe Workflow

1. Identify the target output directory as one directory per FASTA basename inside the user-selected `--output_dir`.
2. Inspect `ranking_debug.json` first to map `ranked_0.pdb`, `ranked_1.pdb`, and later ranked structures back to model names and ranking scores.
3. Use `confidence_<model>.json` for per-residue pLDDT categories and `pae_<model>.json` for inter-residue or inter-domain placement confidence.
4. Treat PDB/mmCIF files as outputs to inspect or convert, not as proof that inference completed successfully; confirm that timing, ranking, result, and confidence files are present.
5. Use the bundled Server JSON reference for syntax and entity schemas, but do not submit jobs, call cloud services, query BigQuery, or download AFDB data unless the user explicitly asks.

## Bundled Helper

```bash
python sub-skills/outputs-and-confidence/scripts/inspect_confidence_json.py path/to/output_dir --json
```

The helper is standalone, uses only the Python standard library, accepts individual JSON files or directories, and never imports AlphaFold or reads original repository files.
