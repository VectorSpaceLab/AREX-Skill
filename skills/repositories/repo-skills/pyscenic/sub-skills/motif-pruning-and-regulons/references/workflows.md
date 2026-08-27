# Motif Pruning and Regulon Workflows

## Decide the Output First

Choose the output suffix before running `ctx` because pySCENIC switches between motif-table and regulon-collection behavior by extension:

- Use `.csv` or `.tsv` when a future agent must inspect NES, AUC, motif annotations, target genes, and contexts.
- Use `.dat` when staying inside Python and preserving `Regulon` objects with pickle is acceptable.
- Use `.gmt` when a broad gene-signature ecosystem needs target sets and not detailed motif evidence.
- Use `.yaml` or `.yml` when human-readable regulon serialization is needed, accepting slower YAML load/save behavior.
- Use `.json` only for external export of `{regulon_name: [target_gene, ...]}`; this checkout does not reload JSON via `load_signatures`.

## CLI Motif Pruning from Existing Modules

When upstream modules already exist as YAML, GMT, or DAT:

```bash
pyscenic ctx modules.dat \
  hg38-tss-centered-10kb.genes_vs_motifs.rankings.feather \
  hg38-500bp-upstream.genes_vs_motifs.rankings.feather \
  --annotations_fname motifs-v9-nr.hgnc-m0.001-o0.0.tbl \
  --mode custom_multiprocessing \
  --num_workers 6 \
  --output regulons.csv
```

Use this pattern when the upstream GRN step already produced module/signature files. The result above is a motif evidence table because the suffix is `.csv`.

## CLI Motif Pruning from Adjacencies

When the input is a GRN adjacency table, provide the expression matrix so `ctx` can build modules before pruning:

```bash
pyscenic ctx adjacencies.tsv \
  hg38-tss-centered-10kb.genes_vs_motifs.rankings.feather \
  --annotations_fname motifs-v9-nr.hgnc-m0.001-o0.0.tbl \
  --expression_mtx_fname expression.csv \
  --mode custom_multiprocessing \
  --num_workers 6 \
  --min_genes 20 \
  --output regulons.gmt
```

Module-building options in this path include `--thresholds`, `--top_n_targets`, `--top_n_regulators`, `--all_modules`, `--mask_dropouts`, and `--transpose`. These belong to module generation inside `ctx`; upstream GRN modeling itself is outside this sub-skill.

## No-Pruning Enrichment Mode

Use no-pruning mode when the task is to find enriched motifs/features without requiring annotation-backed target pruning:

```bash
pyscenic ctx signatures.gmt \
  hg38-tss-centered-10kb.genes_vs_motifs.rankings.feather \
  --annotations_fname motifs-v9-nr.hgnc-m0.001-o0.0.tbl \
  --no_pruning \
  --mode custom_multiprocessing \
  --num_workers 4 \
  --output enriched_motifs.tsv
```

Internally this calls `find_features`, which wraps `prune2df` with `filter_for_annotation=False` and adds motif logo URLs. It still requires ranking databases and motif annotation resources.

## Python Pruning Workflow

Use the API when the agent needs programmatic control over modules, database names, and conversion:

```python
import glob
import os

from ctxcore.rnkdb import FeatherRankingDatabase as RankingDatabase
from pyscenic.prune import prune2df, df2regulons
from pyscenic.cli.utils import load_modules, save_enriched_motifs

modules = load_modules("modules.dat")

def db_name(path):
    return os.path.splitext(os.path.basename(path))[0]

db_paths = glob.glob("databases/*.genes_vs_motifs.rankings.feather")
dbs = [RankingDatabase(fname=path, name=db_name(path)) for path in db_paths]

motifs = prune2df(
    dbs,
    modules,
    "motifs-v9-nr.hgnc-m0.001-o0.0.tbl",
    rank_threshold=5000,
    auc_threshold=0.05,
    nes_threshold=3.0,
    motif_similarity_fdr=0.001,
    orthologuous_identity_threshold=0.0,
    client_or_address="custom_multiprocessing",
    num_workers=6,
)

regulons = df2regulons(motifs)
save_enriched_motifs(motifs, "regulons.csv")
save_enriched_motifs(motifs, "regulons.gmt")
```

Use `rank_threshold=5000` when matching the CLI default; the raw API default is `1500`.

## Python Enriched Feature Workflow

Use `find_features` to retain enriched features without annotation filtering:

```python
from pyscenic.prune import find_features

enriched = find_features(
    dbs,
    modules,
    "motifs-v9-nr.hgnc-m0.001-o0.0.tbl",
    motif_base_url="http://motifcollections.aertslab.org/v9/logos/",
    client_or_address="custom_multiprocessing",
    num_workers=4,
)
```

The returned DataFrame includes `MotifURL` and can be saved with `save_enriched_motifs`.

## Loading Results for Downstream Use

Reload motif tables and regulon files with pySCENIC helpers:

```python
from pyscenic.utils import load_motifs
from pyscenic.cli.utils import load_signatures

motif_table = load_motifs("regulons.csv")
regulons_from_csv = load_signatures("regulons.csv")
regulons_from_gmt = load_signatures("regulons.gmt")
regulons_from_yaml = load_signatures("regulons.yaml")
regulons_from_dat = load_signatures("regulons.dat")
```

Only load motif CSV/TSV files from trusted sources because `load_motifs` evaluates serialized `Context` and `TargetGenes` cells.

## Compute Mode Selection

- `custom_multiprocessing`: current CLI default and usually the first local choice; each worker loads a ranking database and motif annotation table into memory. Ensure `num_workers >= number_of_databases`.
- `dask_multiprocessing`: uses Dask with local process scheduler; progress bar appears in CLI; `module_chunksize` controls module batches.
- `dask_cluster`: use only when workers can see the same ranking database and annotation paths; pass a scheduler through `--client_or_address`.
- `local`: supported by the internal `_prepare_client` API path, not a CLI `--mode` choice in this checkout.
- Direct scheduler address or `distributed.Client`: pass to API `client_or_address` for externally managed Dask.

## Resource Planning Checklist

Before starting a large `ctx` run:

1. Confirm every ranking database is current and readable by `ctxcore`.
2. Confirm the motif annotation file species and motif collection match the ranking database family.
3. Count ranking database files and set `num_workers` at least that high for `custom_multiprocessing`.
4. Start with `.csv` or `.tsv` output on unfamiliar data so the enriched motif table is inspectable.
5. Keep `rank_threshold`, `auc_threshold`, `nes_threshold`, motif FDR, and orthology thresholds in the run log for reproducibility.
6. On clusters, verify shared storage and avoid node-local paths for databases or motif annotations.

## Source Script Adaptation Notes

The upstream pySCENIC project includes an HPC pruning example that parameterizes `prune2df` with mode, chunk size, thresholds, database globbing, annotations, modules, and worker count. Treat that pattern as reference evidence only: cluster scheduler and storage paths are environment-specific, and this runtime skill does not copy or require the example script or configuration.

The safe bundled script in this sub-skill validates pySCENIC regulon and motif I/O surfaces only. It intentionally does not run pruning, open ranking databases, perform downloads, submit scheduler jobs, or train models.
