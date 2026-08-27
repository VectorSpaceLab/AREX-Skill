---
name: network-inference
description: "Use pySCENIC and Arboreto to infer co-expression adjacencies, add
  TF-target correlations, and build TF-target modules before motif pruning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Network Inference

Use this sub-skill when a task asks for pySCENIC Phase I work: GRNBoost2 or GENIE3 adjacency inference, Dask-free Arboreto multiprocessing, adding Pearson correlations, or converting adjacencies into TF-target modules.

## Read First

- [API reference](references/api-reference.md): verified `add_correlation()` and `modules_from_adjacencies()` signatures, dataframe schemas, correlation behavior, and module-construction defaults.
- [Workflows](references/workflows.md): CLI recipes for `pyscenic grn`, `pyscenic add_cor`, `arboreto_with_multiprocessing.py`, and Python recipes for module construction.
- [Troubleshooting](references/troubleshooting.md): TF/gene overlap, orientation, duplicate genes, sparse/loom handling, Dask client mode, multiprocessing fallback, missing genes, dropout masking, and `min_genes` filtering.
- [GRN multiprocessing smoke helper](scripts/grn_multiprocessing_smoke.py): safe import check, tiny fixture writer, API smoke check, and command-template printer.

## Route By Task

- **Infer adjacencies**: use `pyscenic grn` for Dask-backed GRNBoost2/GENIE3, or the bundled workflows for `arboreto_with_multiprocessing.py` when Dask is the failure point.
- **Add correlations**: use `pyscenic add_cor` or `pyscenic.utils.add_correlation()` to add `rho` and `regulation` columns before module construction or diagnostics.
- **Build modules**: use `pyscenic.utils.modules_from_adjacencies()` when a task needs unpruned activating or repressing modules from weighted adjacencies.
- **Stay in bounds**: route motif database pruning and final regulon creation to the motif-pruning workflow, AUCell scoring/binarization to the AUCell workflow, file conversion/export to the data I/O workflow, and container orchestration to the CLI/container workflow.

## Safe Starting Point

Run the bundled helper before writing commands for a user environment:

```bash
python scripts/grn_multiprocessing_smoke.py --help
python scripts/grn_multiprocessing_smoke.py --make-fixtures ./pyscenic-grn-smoke --run-api-smoke
```

The helper checks imports and prints command templates. It creates only tiny local fixtures when requested and does not download data, run GRNBoost2/GENIE3, train models, or mutate existing files.
