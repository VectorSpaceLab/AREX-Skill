# Motif Pruning and Regulon API Reference

## Core Imports

Use these imports for Python work in this sub-skill:

```python
from ctxcore.rnkdb import FeatherRankingDatabase as RankingDatabase
from pyscenic.prune import prune2df, find_features, df2regulons
from pyscenic.utils import load_motif_annotations, load_motifs, load_from_yaml, save_to_yaml
from pyscenic.cli.utils import load_modules, load_signatures, save_enriched_motifs
from pyscenic.featureseq import Feature, FeatureSeq
```

`df2regulons` is re-exported from `pyscenic.prune`; the implementation lives in `pyscenic.transform`.

## `prune2df`

Installed signature verified for this checkout:

```python
prune2df(
    rnkdbs,
    modules,
    motif_annotations_fname,
    rank_threshold=1500,
    auc_threshold=0.05,
    nes_threshold=3.0,
    motif_similarity_fdr=0.001,
    orthologuous_identity_threshold=0.0,
    weighted_recovery=False,
    client_or_address="dask_multiprocessing",
    num_workers=None,
    module_chunksize=100,
    filter_for_annotation=True,
)
```

Use `prune2df` after upstream module construction. It enriches features from each ranking database, filters to motif annotations by default, computes leading-edge target genes, and returns an enriched motif `pandas.DataFrame` indexed by `(TF, MotifID)`.

Important parameters:

- `rnkdbs`: sequence of `ctxcore.rnkdb.RankingDatabase` objects, usually `FeatherRankingDatabase(fname=..., name=...)`.
- `modules`: sequence of `ctxcore.genesig.Regulon` or `GeneSignature` objects; pySCENIC normally adds the TF to each module upstream.
- `motif_annotations_fname`: motif-to-TF annotation TSV path.
- `rank_threshold`: number of ranked genes used while deriving leading-edge target genes; CLI default is `5000`, API default is `1500`.
- `auc_threshold`: fraction of the ranked genome used for AUC; default `0.05`.
- `nes_threshold`: normalized enrichment score cutoff; default `3.0`.
- `motif_similarity_fdr`: maximum motif similarity q-value used by `load_motif_annotations`; default `0.001`.
- `orthologuous_identity_threshold`: minimum orthologous identity; default `0.0`; note the parameter spelling is `orthologuous` in `prune2df`.
- `weighted_recovery`: use module gene weights in recovery curves.
- `client_or_address`: `custom_multiprocessing`, `dask_multiprocessing`, `local`, a Dask scheduler address, or a `distributed.Client` for API calls.
- `num_workers`: local worker count; for `custom_multiprocessing`, it must be at least the number of ranking databases.
- `module_chunksize`: Dask chunk size for module batches; cluster mode effectively uses one module per task.
- `filter_for_annotation`: keep only annotated enriched features; use `False` only for no-pruning/enriched-feature discovery.

## `find_features`

Installed signature verified for this checkout:

```python
find_features(
    rnkdbs,
    signatures,
    motif_annotations_fname,
    motif_base_url="http://motifcollections.aertslab.org/v9/logos/",
    **kwargs,
)
```

Use `find_features` for `ctx --no_pruning`. It calls `prune2df(..., filter_for_annotation=False, **kwargs)` and appends an `("Enrichment", "MotifURL")` column. It is still a cisTarget enrichment workflow and still requires ranking databases and motif annotations, but it does not require an annotation match to retain a feature.

## Motif Annotation Loading

`load_motif_annotations(fname, column_names=("#motif_id", "gene_name", "motif_similarity_qvalue", "orthologous_identity", "description"), motif_similarity_fdr=0.001, orthologous_identity_threshold=0.0)` reads a TSV and creates a `(TF, MotifID)` index with these renamed columns:

- `MotifSimilarityQvalue`
- `OrthologousIdentity`
- `Annotation`

The loader filters rows where `motif_similarity_qvalue <= motif_similarity_fdr` and `orthologous_identity >= orthologous_identity_threshold`. Schema mismatches usually surface as `pandas.read_csv` errors or empty joins later.

## Enriched Motif DataFrame

`prune2df` and `find_features` return a DataFrame with a two-level index named `TF` and `MotifID`. The important columns are under the `Enrichment` top-level column:

- `AUC`: feature AUC.
- `NES`: normalized enrichment score.
- `MotifSimilarityQvalue`: motif annotation confidence.
- `OrthologousIdentity`: orthology support.
- `Annotation`: motif-to-TF annotation description.
- `Context`: a `frozenset` containing module context and database name.
- `TargetGenes`: list of `(gene, weight)` tuples selected from the leading edge.
- `RankAtMax`: rank position at maximum leading-edge separation.
- `MotifURL`: present when using `find_features` or calling `add_motif_url`.

`module2df` skips a module when at least 20% of its genes are missing from a ranking database, when no genes map to the database, or when no enriched annotated feature remains.

## `df2regulons`

`df2regulons(df, save_columns=[])` converts an enriched motif DataFrame into `ctxcore.genesig.Regulon` objects.

- `df` must not be empty; empty input raises `AssertionError: Signatures dataframe is empty!`.
- If the DataFrame has two-level columns, `df2regulons` drops the top level internally.
- Rows are grouped by TF and inferred interaction type; contexts containing `repressing` become `TF(-)`, otherwise the regulon is treated as activating and named `TF(+)`.
- Target genes and weights come directly from the `TargetGenes` column.
- The final regulon context includes the selected motif logo filename, based on the row with the highest NES.
- `save_columns` can include `NES`, `OrthologousIdentity`, `MotifSimilarityQvalue`, and `Annotation` to copy those values onto the regulon object.

## File Loading and Saving Helpers

`pyscenic.cli.utils.save_enriched_motifs(df, fname)` chooses behavior by suffix:

- `.csv` and `.tsv`: save the enriched motif table with `DataFrame.to_csv`; these are reloadable with `load_motifs` and `load_signatures`.
- `.gmt`: convert `df2regulons(df)` to GSEA GMT using `GeneSignature.to_gmt`.
- `.dat`: pickle the `Regulon` list; validate this in the active environment because some `ctxcore.openfile` versions fail on binary modes with `binary mode doesn't take an encoding argument`.
- `.yaml` and `.yml`: write regulons through `save_to_yaml`.
- `.json`: write a mapping from regulon name to target gene list; this is useful for external export but is not accepted by `load_signatures` in this checkout.

`load_signatures(fname)` accepts CSV/TSV motif tables, YAML/YML, GMT, and DAT. `load_modules(fname)` accepts YAML/YML, DAT, and GMT for module input; CSV/TSV adjacencies are handled by the `ctx` command when an expression matrix is also supplied.

`load_motifs(fname, sep=",")` reads pySCENIC motif CSV/TSV files with two-level headers and `(TF, MotifID)` index. It reconstructs `Context` and `TargetGenes` by evaluating serialized Python literals; only use it for trusted files.

## CLI `ctx` Surface

`pyscenic ctx` accepts:

```text
pyscenic ctx MODULE_FNAME DATABASE_FNAME [DATABASE_FNAME ...] \
  --annotations_fname MOTIF_ANNOTATIONS.tsv \
  --output REGULONS_OR_MOTIFS \
  --mode custom_multiprocessing \
  --num_workers 6
```

Key options:

- `MODULE_FNAME`: CSV/TSV adjacencies, YAML, GMT, or DAT modules.
- `DATABASE_FNAME`: one or more ranking database files; help text mentions Feather or legacy DB, but current pySCENIC releases require modern ctxcore-compatible database formats.
- `--annotations_fname`: required motif annotation TSV.
- `--no_pruning`: call `find_features` instead of `prune2df`.
- `--chunk_size`: Dask module chunk size, default `100`.
- `--mode`: `custom_multiprocessing`, `dask_multiprocessing`, or `dask_cluster`; CLI default is `custom_multiprocessing`.
- `--client_or_address`: Dask scheduler address; required with `--mode dask_cluster`.
- `--all_modules`: keep positive and negative modules when modules are generated from adjacencies.
- `--expression_mtx_fname`: required when `MODULE_FNAME` is an adjacency CSV/TSV and modules must be generated inside `ctx`.
- `--mask_dropouts`, `--thresholds`, `--top_n_targets`, `--top_n_regulators`, and `--min_genes`: used only when building modules from adjacencies inside `ctx`.

## Genomic Interval Helpers

`pyscenic.featureseq.Feature` and `FeatureSeq` support BED-like evidence handling for regulatory features:

- `Feature.from_string("chr1 12 50 feature1 10.0 +")` parses at least chromosome, start, and end; optional columns are name, score, and strand.
- Coordinates are zero-based, half-open intervals.
- `Feature.has_overlap_with(other)`, `other in feature`, and `Feature.get_overlap_in_bp_with(other)` implement overlap checks.
- `FeatureSeq.from_bed_file(path_or_file)` builds an interval index.
- `FeatureSeq.find(feature, fraction=None)` returns overlapping features, optionally requiring overlap fraction.
- `FeatureSeq.intersection(other, fraction=None)` returns a new `FeatureSeq` containing overlaps.

For a bounded validation, parse two tiny BED-like strings with `Feature.from_string(...)` and assert the expected overlap or non-overlap before scaling to larger files.
