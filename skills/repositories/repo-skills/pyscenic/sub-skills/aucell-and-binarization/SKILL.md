---
name: aucell-and-binarization
description: "Score pySCENIC regulon or gene-signature activity with AUCell,
  derive thresholds, binarize AUC matrices, inspect activity plots, and compute
  regulon specificity scores."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# AUCell And Binarization

Use this sub-skill when the task starts from an expression matrix plus already-created regulons or gene signatures and needs cell-level activity scoring, activity thresholding, binary regulon calls, activity inspection, or RSS summaries.

## Route Here

- Run `pyscenic aucell` or `pyscenic.aucell.aucell` on CSV/TSV, loom, h5ad, GMT, YAML, DAT, or motif-table-derived signatures.
- Check whether expression input is cells-by-genes, whether text input needs `--transpose`, and whether AUCell output is cells-by-regulons.
- Choose `auc_threshold`, `seed`, `num_workers`, `--weights`, `noweights`, or `normalize` settings for scoring.
- Use `derive_auc_threshold`, `create_rankings`, `aucell4r`, `derive_threshold`, `binarize`, `plot_binarization`, `plot_rss`, or `regulon_specificity_scores`.
- Diagnose empty signatures, non-overlapping gene names, multiprocessing memory behavior, optional loom/h5ad dependency issues, and unimodal threshold results.

## Route Elsewhere

- Create modules, motif-prune them, or convert enriched motifs into regulons with `../motif-pruning-and-regulons/SKILL.md`.
- Export SCope loom or AnnData metadata beyond AUCell output append behavior with `../data-io-and-export/SKILL.md`.
- Build end-to-end `grn -> ctx -> aucell` CLI/container recipes with `../cli-and-containers/SKILL.md`.

## Bundled References

- `references/api-reference.md` lists the AUCell, binarization, plotting, RSS, CLI, and signature-format contracts.
- `references/workflows.md` gives safe API and CLI recipes for scoring, thresholding, binarization, plotting, RSS, and orientation checks.
- `references/troubleshooting.md` covers common failures and ambiguous outputs for AUCell and binarization.
- `scripts/aucell_smoke.py` runs a tiny deterministic AUCell API smoke test and can print equivalent CLI guidance.

## Quick Start

```bash
python scripts/aucell_smoke.py --show-cli
```

For real data, keep expression matrices as cells x genes for the Python API and CSV/TSV CLI input unless using `pyscenic aucell --transpose` for genes x cells text files. Treat returned AUC and binary matrices as cells x regulons.
