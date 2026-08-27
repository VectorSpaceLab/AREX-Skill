---
name: relaxation-and-outputs
description: "Post-process ColabFold results with Amber/OpenMM relaxation,
  confidence/output validation, plotting utilities, citations, and extra
  pTM/interface metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Relaxation and Outputs

Use this sub-skill when the task starts after ColabFold input preparation, MSA generation, or structure prediction and asks you to inspect, validate, relax, visualize, or interpret prediction outputs.

## Route here for

- Running standalone Amber/OpenMM relaxation with `colabfold_relax` on existing PDB outputs.
- Choosing CPU vs GPU relaxation and tuning `--max-iterations`, `--tolerance`, `--stiffness`, or `--max-outer-iterations`.
- Explaining output files such as ranked/unrelaxed/relaxed PDBs, score JSON files, PAE JSON, pLDDT/PAE/coverage PNGs, `config.json`, and `cite.bibtex`.
- Validating an output directory without re-running prediction by using `scripts/inspect_colabfold_outputs.py`.
- Interpreting pLDDT, pTM, ipTM, PAE, ranking metrics, and optional extra interface metrics.
- Using plotting or display APIs such as `plot_predicted_alignment_error(...)`, `plot_msa_v2(...)`, and `show_pdb(...)` when optional visualization dependencies are available.
- Deciding citation coverage for AlphaFold, multimer, MMseqs/MSA, templates, environment database, DeepFold, and Amber relaxation.

## Route elsewhere

- For FASTA, CSV, A3M, PDB/mmCIF input preparation, use `../inputs-and-formats/SKILL.md`.
- For MSA server, local MMseqs2 database, GPU search, or AF3 JSON-only MSA export workflows, use `../msa-search/SKILL.md`.
- For running `colabfold_batch`, model selection, templates during prediction, or prediction GPU/JAX setup, use `../batch-prediction/SKILL.md`.

## Quick workflow

1. Inspect the result directory before changing anything:
   ```bash
   python scripts/inspect_colabfold_outputs.py results_dir
   ```
2. If outputs are complete enough, interpret scores and plots with `references/output-reference.md`.
3. If relaxation is requested, choose CPU first unless OpenMM GPU/CUDA is known to work; see `references/cli-reference.md`.
4. If files or metrics are missing, diagnose owned failures with `references/troubleshooting.md` before re-running prediction.

## Bundled references

- `references/cli-reference.md` covers `colabfold_relax`, `relax_me(...)`, plotting/display APIs, extra pTM APIs, and citation writing.
- `references/output-reference.md` explains expected files, score keys, confidence semantics, validation checks, and safe interpretation.
- `references/troubleshooting.md` covers optional dependency, backend, data/config, CLI/API, plotting, citation, and workflow failures.
- `scripts/inspect_colabfold_outputs.py` summarizes PDB/mmCIF/JSON/PNG/BibTeX outputs, detects common missing artifacts, and never downloads, deletes, or rewrites files.
