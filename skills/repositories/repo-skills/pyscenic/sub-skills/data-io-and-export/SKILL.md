---
name: data-io-and-export
description: "Load, save, convert, and export pySCENIC expression matrices,
  signatures, AUCell metadata, SCope loom files, AnnData annotations, and
  regulon GraphML."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Data I/O And Export

Use this sub-skill when a task needs pySCENIC file loading, matrix orientation checks, CSV/TSV-to-loom conversion, AUCell metadata append/export, SCope-ready loom preparation, AnnData metadata insertion, or regulon GraphML export.

## Route Here

- Load or save expression, AUC, adjacency, module, signature, enriched-motif, loom, or h5ad-compatible data with pySCENIC utilities.
- Decide whether CSV/TSV inputs are cells x genes or genes x cells, when to use transpose flags, and how extension-based separators behave.
- Convert a tiny or production expression matrix to loom with `csv2loom` or the Python loader/writer APIs.
- Append AUCell/regulon metadata into an existing loom file, or export SCope-compatible loom content with embeddings, thresholds, tree metadata, and regulon membership.
- Add SCENIC metadata to an AnnData object or export regulons as GraphML.

## Route Elsewhere

- Interpret AUCell values, tune AUCell thresholds, or binarize activity matrices with `../aucell-and-binarization/SKILL.md`.
- Explain motif pruning, regulon creation semantics, enriched motif table meaning, or module pruning with `../motif-pruning-and-regulons/SKILL.md`.
- Build full CLI/container execution recipes, scheduler commands, or container mount plans with `../cli-and-containers/SKILL.md`.
- Infer GRN adjacencies, add TF-target correlations, or create unpruned modules with `../network-inference/SKILL.md`.

## Read First

- [API reference](references/api-reference.md) lists the loader, writer, converter, loom/AnnData export, and GraphML contracts.
- [Data formats](references/data-formats.md) explains supported extensions, orientation, loom attributes, SCope metadata, AnnData placement, and output schemas.
- [Troubleshooting](references/troubleshooting.md) covers separator mistakes, transpose errors, optional dependencies, loom metadata, h5ad caveats, SCope constraints, extension errors, and legacy entry-point discrepancies.
- [I/O format probe](scripts/io_format_probe.py) creates tiny CSV/TSV fixtures, checks load/save orientation, and optionally checks loom support when installed dependencies allow it.

## Safe Starting Point

```bash
python scripts/io_format_probe.py --help
python scripts/io_format_probe.py
```

For real data, keep Python API expression matrices as cells x genes. Use transpose options only when a text file is stored genes x cells. Loom files are stored rows=genes and columns=cells but are loaded back as cells x genes by pySCENIC.