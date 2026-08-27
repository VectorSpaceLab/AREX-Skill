---
name: expression-omics
description: "Query bulk, comparative, single-cell, and partitioned expression
  resources with gget: ARCHS4 correlation/tissue atlases, Bgee
  orthologs/expression, CZ CELLxGENE Census, and 8cube specificity, ψ-block, and
  normalized expression."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Expression and omics queries

Use this sub-skill when the task needs expression patterns, orthology, tissue
correlation, single-cell Census data, or 8cube partition statistics. These
wrappers query public remote services; they do not replace local differential
expression or statistical modeling. Select the narrowest source first and
scope large requests with filters.

## Route before calling

- Use `archs4` for human/mouse bulk RNA-seq co-expression or a tissue atlas.
- Use `bgee` for Ensembl-centered comparative orthologs or anatomical
  expression across many animals. Expression lists must be one species.
- Use `cellxgene` for filtered CZ CELLxGENE Discover Census single-cell count
  matrices or cell metadata. It requires the optional `cellxgene-census`
  dependency and substantial RAM/network capacity.
- Use `specificity`, `psi_block`, or `gene_expression` from `gget.gget_8cube`
  for 8cube mouse partition metrics and normalized expression.
- Route cancer/target associations to `disease-structure`; route generic
  Ensembl ID lookup, conversion, and annotation to `gene-annotation`.

Read [API signatures and outputs](references/api-signatures.md) for exact
parameters, return schemas, and save names. The source-to-claim map is in
[evidence](references/evidence.md). Read [workflows](references/workflows.md)
before a multi-filter or partitioned query, and keep
[troubleshooting](references/troubleshooting.md) open for service,
identifier, dependency, and resource failures.

## Common output and safety rules

Python defaults are pandas DataFrames for the HTTP-table wrappers. Set
`json=True` on ARCHS4, Bgee, or 8cube to receive JSON-compatible
`list[dict]` records. `save=True` writes the wrapper's documented default file
in the current directory for ARCHS4/8cube. Bgee has no Python `save` parameter;
write its returned DataFrame yourself. CELLxGENE uses `out=...`: AnnData is
written for matrix mode and a CSV for `meta_only=True`.

Use versioned Ensembl IDs where the API accepts them unless the target service
requires a specific form. Do not silently convert symbols to Ensembl IDs:
`ensembl=True` is an explicit input-mode flag in ARCHS4 and CELLxGENE.
Preserve query parameters and Census/partition versions in the experiment log.
Treat an empty result as a result to investigate, not evidence of no biology.

## Minimal Python recipes

```python
import gget

# Bulk co-expression (100 correlated genes by default)
corr = gget.archs4("STAT4", which="correlation", gene_count=25)

# Human or mouse ARCHS4 tissue atlas
atlas = gget.archs4("STAT4", which="tissue", species="human")

# Comparative orthologs, one Ensembl gene for ortholog mode
orth = gget.bgee("ENSSSCG00000014725", type="orthologs")

# Anatomical expression; multiple IDs must resolve to one Bgee species
expr = gget.bgee(["ENSBTAG00000047356", "ENSBTAG00000018317"], type="expression")
```

For single-cell and 8cube recipes, use the constrained examples in
[workflows](references/workflows.md); do not begin with an unfiltered Census
matrix. Inspect columns, row counts, and identifier casing before downstream
analysis.

## ARCHS4 procedure

Pass a gene symbol such as `STAT4`, or remove an Ensembl version suffix and
set `ensembl=True`. `which` is exactly `correlation` or `tissue`; `species`
is exactly `human` or `mouse` and applies to tissue mode. Correlation returns
Pearson co-expression over ARCHS4 samples and drops the queried gene itself;
tissue mode returns tissue summary statistics sorted by decreasing `median`.
An invalid `which` or `species` fails before the request. A missing gene
returns `None` after an error log. See the output schema and save filenames in
the reference.

## Bgee procedure

Use an Ensembl gene ID (Bgee can expose non-Ensembl/NCBI identifiers for some
species, but the wrapper contract and examples are Ensembl-centered). Choose
`type="orthologs"` for homolog rows; this mode accepts only one ID. Choose
`type="expression"` for anatomical/cell-type expression; a string is treated
as one ID and a list is allowed only when all IDs map to one species. Bgee
performs a species lookup before the data request, so invalid IDs and mixed
species commonly fail before a table is returned.

## CELLxGENE Census procedure

Install the optional extra once with `gget.setup("cellxgene")` (or the
corresponding CLI setup command), then use canonical species keys and
case-sensitive gene symbols. Supported species are `homo_sapiens`,
`mus_musculus`, `macaca_mulatta`, `callithrix_jacchus`, and
`pan_troglodytes`. For Ensembl feature IDs set `ensembl=True`; for symbols
leave it false. Choose a dated `census_version`, `stable`, or `latest` and
record it. Non-human primates require the Census LTS `2025-11-08` or newer.

In matrix mode (`meta_only=False`), `gene` builds a feature filter and the
return is AnnData. In metadata-only mode the return is a pandas DataFrame of
`obs`; the current implementation reads only `obs` filters, so `gene` does
not build a feature filter in this branch. Scope with `tissue`, `cell_type`,
`disease`, `sex`, `dataset_id`, ontology-term columns, donor, ethnicity, or
suspension filters. Scalar strings and lists are both accepted. By default
`is_primary_data=True` is included in the observation filter. The defaults
for `column_names` are documented in the API reference.

## 8cube procedure

Import `specificity`, `psi_block`, and `gene_expression` from
`gget.gget_8cube` (also exported at `gget` top level). Every `gene_list` must
be a list or tuple, even for one gene; scalar strings raise `ValueError`.
Symbols and Ensembl IDs are accepted, and Ensembl version suffixes are
preserved. `specificity` needs no partition selection and returns ψ/ζ summary
statistics over available partitions. `psi_block` returns block-level ψ for a
specific `analysis_level` and `analysis_type`; `gene_expression` returns
normalized mean/variance for that same partition selection. Use exact API
partition names, such as `Across_tissues`, `Kidney`, `Sex:Strain`, and
`Sex:Celltype`, rather than inventing labels.

```python
from gget.gget_8cube import specificity, psi_block, gene_expression

summary = specificity(["Akr1c21"], json=True)
blocks = psi_block(["GJB4"], "Across_tissues", "Sex:Strain")
values = gene_expression(["ENSMUSG00000030945.18"], "Kidney", "Sex:Celltype")
```

## Validate and recover

For every call, verify the return type, nonzero row count when expected,
identifier/partition columns, and output path. Use `verbose=False` only after
the query is understood. For HTTP failures, preserve the status/body and
retry only after checking filters, service availability, and request size.
For schema or empty-result changes, inspect current returned columns and stop
before treating them as interchangeable. Apply the targeted recovery matrix in
[troubleshooting](references/troubleshooting.md). No bundled script is
provided: these operations are thin network wrappers, and a local duplicate
would add no safe value.
