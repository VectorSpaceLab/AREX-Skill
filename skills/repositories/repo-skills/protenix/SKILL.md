---
name: protenix
description: "Use Protenix for biomolecular structure prediction, input JSON
  authoring, MSA/template/RNA preprocessing, training data pipelines, and
  model/kernel configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Protenix

Use this repo skill when a task mentions Protenix, biomolecular or protein structure prediction, AlphaFold 3-style inputs, protein/RNA/DNA/ligand complexes, MSA/template preprocessing, Protenix training data, or Protenix model/kernel internals.

## Start Here

1. Verify the user's environment before running package-backed commands:
   ```bash
   pip install --upgrade protenix --index-url https://pypi.org/simple
   python -c "import protenix, runner.batch_inference; import importlib.metadata as md; print(md.version('protenix'))"
   protenix --help
   ```
2. Run `python scripts/check_protenix_environment.py --json` when import, CLI, CUDA, optional backend, or external-tool status is unclear.
3. Route to a focused sub-skill before giving detailed commands; this root file is only the router and shared safety policy.
4. Treat full prediction, MSA/template/RNA search, data downloads, preprocessing, training, CCD refresh, and checkpoint downloads as side-effecting or expensive unless the user confirms resources and runtime budget.
5. Keep commands self-contained in the user's current environment; do not assume the original Protenix repository checkout exists.

## Route By Task

| User task | Read |
| --- | --- |
| Run `protenix pred`, choose a model, build a no-run prediction command, inspect output layout, or debug CLI/cache/checkpoint failures | `sub-skills/cli-and-inference/SKILL.md` |
| Author or validate input JSON, entities, ligands, ions, covalent bonds, constraints, MSA/template paths, or `protenix json` conversion | `sub-skills/input-data-and-features/SKILL.md` |
| Generate or validate protein MSA, template hits, RNA MSA, ColabFold-compatible MSA, or `protenix msa`/`mt`/`prep` workflows | `sub-skills/msa-template-and-prep/SKILL.md` |
| Prepare training data roots, custom CIF preprocessing, index CSVs, training/fine-tuning commands, DDP, W&B, or checkpoint launch planning | `sub-skills/training-and-data-pipeline/SKILL.md` |
| Inspect configs, kernels, CUDA/Triton/cuEquivariance/DeepSpeed fallbacks, TFG, confidence outputs, metrics, or model internals | `sub-skills/advanced-model-configuration/SKILL.md` |

## Shared References

- `references/package-overview.md` summarizes the package purpose, CLI surface, dependency profile, hardware assumptions, and workflow boundaries.
- `references/troubleshooting.md` covers cross-cutting install/import, CLI visibility, package version, checkpoint/cache, CUDA/backend, external-tool, JSON, and data-root issues.
- `references/repo-provenance.md` records the source snapshot and evidence paths used to generate this skill; read it before deciding whether a refresh is needed.
- `references/repo-routing-metadata.json` is structured metadata consumed by DisCo's `repo-skills-router` import flow.

## Shared Tool

- `scripts/check_protenix_environment.py` performs safe read-only checks for package metadata, imports, CLI help, PyTorch/CUDA, optional backend packages, relevant environment variables, and external tools such as HMMER and kalign.

## Safety Rules

- Do not present full inference, MSA search, template search, RNA search, CCD cache refresh, data downloads, preprocessing, or training as a quick smoke test.
- Prefer no-run command builders and read-only layout validators before launching expensive work.
- Set `PROTENIX_ROOT_DIR` intentionally when checkpoints, cache files, common chemistry data, search databases, or training datasets need a stable location.
- For debugging kernel failures, first try safe fallbacks such as `LAYERNORM_TYPE=torch`, `--trimul_kernel torch`, and `--triatt_kernel torch`; use the advanced sub-skill for deeper backend work.
- For input JSON issues, validate statically before running model inference; for MSA/template issues, validate paths and layouts before rerunning searches.
