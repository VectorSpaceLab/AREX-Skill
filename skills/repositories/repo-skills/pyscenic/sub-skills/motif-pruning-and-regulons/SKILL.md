---
name: motif-pruning-and-regulons
description: "Prune pySCENIC co-expression modules against cisTarget ranking
  databases and convert enriched motif tables into regulons."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Motif Pruning and Regulons

Use this sub-skill when the task is to run or explain the pySCENIC `ctx` step, call `prune2df` or `find_features`, inspect enriched motif tables, convert motif evidence with `df2regulons`, or choose regulon output formats for downstream scoring.

Do not use this sub-skill for upstream GRN/module inference or downstream AUCell scoring; route those tasks to the pySCENIC sub-skills that own those phases.

## Route

- For exact API signatures, motif table schema, output suffix behavior, and interval helpers, read [API reference](references/api-reference.md).
- For command-line and Python pruning workflows, no-pruning enrichment mode, resource planning, and cluster modes, read [workflows](references/workflows.md).
- For Feather v2 database, annotation TSV, multiprocessing, empty-output, and extension failures, read [troubleshooting](references/troubleshooting.md).
- To verify local pySCENIC motif/regulon I/O without ranking databases or downloads, run [regulon_io_smoke.py](scripts/regulon_io_smoke.py) with `python scripts/regulon_io_smoke.py --help` first.

## Inputs Owned Here

- Co-expression modules as `ctxcore.genesig.GeneSignature` or `Regulon` objects, or CLI module files in CSV, TSV, YAML, GMT, or DAT form.
- cisTarget ranking databases already available on disk, normally current Feather v2 files ending in `*.genes_vs_motifs.rankings.feather` or `*.genes_vs_tracks.rankings.feather`.
- Motif-to-TF annotation TSV files with motif id, gene name, motif similarity q-value, orthologous identity, and description columns.

## Outputs Owned Here

- Enriched motif tables in CSV or TSV form that preserve NES, AUC, annotation, context, target genes, and rank metadata.
- Regulon/signature collections in GMT, DAT, YAML, or JSON form, with JSON treated as an export mapping rather than the normal pySCENIC reload format.
- `ctxcore.genesig.Regulon` objects produced by `df2regulons` for downstream AUCell or custom analysis.

## Operating Rules

- Prefer current Feather v2 ranking databases and avoid initiating downloads from this sub-skill.
- Keep ranking databases, motif annotations, and expression/module inputs accessible to every local worker or cluster worker before starting `ctx`.
- Choose output suffix before running: CSV/TSV when motif evidence must remain inspectable, GMT/YAML/DAT when a compact regulon collection is enough.
- Treat loaded motif CSV/TSV files as trusted inputs because pySCENIC reconstructs Python objects from serialized `Context` and `TargetGenes` cells.
