---
name: pyscenic
description: "Use pySCENIC for single-cell SCENIC regulatory network inference,
  motif pruning, AUCell scoring, data export, and CLI or container workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# pySCENIC

Use this repo skill when a task involves pySCENIC, the Python implementation of the SCENIC pipeline for single-cell transcription factor and regulon analysis.

## Start Here

- Read `references/overview.md` for the SCENIC pipeline phases, required inputs, and expected outputs.
- Run `python scripts/check_pyscenic_environment.py --check-cli` when a user environment may be missing pySCENIC, CLI entry points, or compatible dependencies.
- Read `references/troubleshooting.md` for cross-cutting install, dependency, resource, and file-format failures.
- Read `references/repo-provenance.md` before deciding whether this skill is current for a repository checkout.

## Route By Task

- **Infer co-expression networks**: use `sub-skills/network-inference/SKILL.md` for `pyscenic grn`, `pyscenic add_cor`, `arboreto_with_multiprocessing.py`, `add_correlation()`, and `modules_from_adjacencies()`.
- **Prune modules into regulons**: use `sub-skills/motif-pruning-and-regulons/SKILL.md` for `pyscenic ctx`, `prune2df()`, `find_features()`, enriched motif tables, cisTarget databases, and regulon output formats.
- **Score cells with AUCell**: use `sub-skills/aucell-and-binarization/SKILL.md` for `pyscenic aucell`, `aucell()`, thresholds, binarization, activity plots, and regulon specificity scores.
- **Handle files and exports**: use `sub-skills/data-io-and-export/SKILL.md` for CSV/TSV/loom/h5ad loading, `csv2loom`, `export2loom()`, AnnData metadata, SCope loom output, and GraphML regulon export.
- **Plan CLI/container runs**: use `sub-skills/cli-and-containers/SKILL.md` for end-to-end `grn -> ctx -> aucell` command plans, `@args.txt`, Docker/Podman/Singularity/Apptainer, and HPC cautions.
- **Combine Python API phases**: for notebooks or scripts that span precomputed adjacencies, matrix orientation, motif pruning, AUCell scoring, and GraphML/SCope export, route through data I/O checks first, then network module construction, motif pruning/regulon conversion, AUCell scoring, and final export.

## Install And Smoke Check

For a normal user environment, prefer a fresh Python environment compatible with scientific Python wheels, then install pySCENIC:

```bash
pip install pyscenic
python -c "import pyscenic; print('pyscenic import ok')"
pyscenic --help
```

If a source checkout is being inspected or developed, install that checkout into an isolated environment and run the same import and CLI checks. Avoid installing broad notebook, Scanpy, or documentation extras unless the task specifically requires them.

## Required External Resources

- An expression matrix in a supported text, loom, or h5ad format.
- A transcription-factor list for the GRN step.
- cisTarget ranking databases and motif-to-TF annotations for the `ctx` step.
- Regulon or signature files for standalone AUCell scoring.
- Enough CPU cores and memory for the selected matrix, database, and multiprocessing mode.

pySCENIC does not download large ranking databases or motif annotation resources automatically. Treat those files as explicit user-provided inputs and validate their format before launching expensive runs.

## Common Decisions

- Use cells x genes matrices for Python APIs and most CSV/TSV CLI inputs; use transpose flags only when text files are genes x cells.
- Choose CSV/TSV outputs when motif evidence must remain inspectable; choose GMT/DAT/YAML when a compact regulon collection is enough.
- Use local multiprocessing for one machine, Dask cluster mode only when workers can access the same database/resource paths, and container mounts only when every command path is inside the mounted volume.
- Keep full notebooks, large examples, and native test scripts as evidence or verification candidates, not runtime dependencies for this skill.
