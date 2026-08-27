# pySCENIC Overview

## Purpose

Read this when choosing a pySCENIC workflow route or explaining the required data and resources before writing commands or Python code.

## Pipeline Phases

| Phase | Main entry points | Inputs | Outputs | Owning sub-skill |
| --- | --- | --- | --- | --- |
| Network inference | `pyscenic grn`, `arboreto_with_multiprocessing.py`, Arboreto APIs | Expression matrix, TF list | TF-target adjacencies | `sub-skills/network-inference/SKILL.md` |
| Correlation and modules | `pyscenic add_cor`, `modules_from_adjacencies()` | Adjacencies, expression matrix | Activating/repressing modules | `sub-skills/network-inference/SKILL.md` |
| Motif pruning | `pyscenic ctx`, `prune2df()`, `find_features()` | Modules, cisTarget databases, motif annotations | Enriched motif table or regulons | `sub-skills/motif-pruning-and-regulons/SKILL.md` |
| Activity scoring | `pyscenic aucell`, `aucell()` | Expression matrix, regulons/signatures | AUC matrix | `sub-skills/aucell-and-binarization/SKILL.md` |
| Thresholding/export | `binarize()`, `export2loom()`, `add_scenic_metadata()` | AUC matrix, regulons, optional metadata | Binary activity, loom/h5ad/GraphML outputs | `sub-skills/aucell-and-binarization/SKILL.md`, `sub-skills/data-io-and-export/SKILL.md` |
| CLI/container operation | `pyscenic`, container image commands, `@args.txt` | All phase resources and paths | Reproducible command plan | `sub-skills/cli-and-containers/SKILL.md` |

## Data And Resource Checklist

- **Expression matrix**: CSV, TSV, loom, and selected h5ad paths are supported in pySCENIC utilities. Python APIs expect cells x genes dataframes.
- **TF list**: plain text list of transcription factors; a low overlap with expression genes is a strong warning signal.
- **Ranking databases**: current ctxcore-compatible Feather v2 cisTarget ranking databases are expected for modern pySCENIC releases.
- **Motif annotations**: TSV table mapping motif IDs to TF names with similarity and orthology columns.
- **Regulons/signatures**: motif CSV/TSV, GMT, DAT, YAML, or in-memory `ctxcore.genesig` objects depending on the step.
- **Compute mode**: local multiprocessing is simpler; Dask or cluster mode requires consistent package versions and shared access to databases/resources.

## Output Conventions

- Adjacency outputs normally contain `TF`, `target`, and `importance` columns.
- Correlation-enriched adjacencies add `rho` and `regulation` columns.
- Enriched motif tables preserve motif evidence, contexts, target genes, and enrichment statistics.
- AUCell matrices are cells x regulons/signatures.
- Loom exports store genes as rows and cells as columns internally but pySCENIC loaders return cells x genes dataframes.

## Routing Notes

- Start with `cli-and-containers` when the user asks for a complete runnable command plan.
- Start with `network-inference`, `motif-pruning-and-regulons`, or `aucell-and-binarization` when the user asks for a specific pipeline phase or Python API.
- Start with `data-io-and-export` when the task is mostly about orientation, file extension support, loom/h5ad metadata, or SCope export.
