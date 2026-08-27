# Expression-omics workflows

These recipes use only the public gget interfaces and intentionally keep
large remote reads bounded. Replace example IDs with identifiers validated for
the selected service.

## 1. Bulk correlation and tissue atlas

```python
import gget

# Symbol input: output is a DataFrame with gene_symbol and correlation.
corr = gget.archs4("STAT4", which="correlation", gene_count=25, verbose=False)
assert {"gene_symbol", "pearson_correlation"} <= set(corr.columns)

# Tissue mode: species is human or mouse and output is sorted by median.
atlas = gget.archs4("Stat4", which="tissue", species="mouse", verbose=False)
assert {"id", "median"} <= set(atlas.columns)
```

For an Ensembl input, pass `ensembl=True` and keep in mind that ARCHS4 then
resolves the ID to a symbol before the query. A version suffix is removed for
that lookup. If the result is `None`, check symbol/ID mode and spelling before
retrying. Use `json=True` for records and `save=True` for the module's default
filename; do not assume a remote result is stable across database updates.

## 2. Bgee orthology and expression

```python
import gget

# Ortholog mode: one ID only.
orthologs = gget.bgee("ENSSSCG00000014725", type="orthologs", verbose=False)
assert {"gene_id", "species_id", "genus", "species"} <= set(orthologs.columns)

# Expression mode: all IDs must map to the same Bgee species.
expression = gget.bgee(
    ["ENSBTAG00000047356", "ENSBTAG00000018317"],
    type="expression",
    verbose=False,
)
assert {"anat_entity_id", "score", "expression_state"} <= set(expression.columns)
```

Use `json=True` when handing records to a JSON-oriented caller. If a list
contains mixed species, split it into species-homogeneous calls. If Bgee says
an ID is unknown, do not substitute a guessed symbol: resolve it with the
annotation workflow or use a Bgee-supported identifier documented for that
species. The wrapper performs a network species lookup per ID.

## 3. CELLxGENE metadata-only, safely scoped

Metadata-only is useful for discovering dataset/cell annotations without
materializing a count matrix. Use several observation filters and explicit
columns:

```python
import gget

meta = gget.cellxgene(
    species="homo_sapiens",
    meta_only=True,
    tissue=["lung", "blood"],
    cell_type=["macrophage", "dendritic cell"],
    disease="normal",
    sex=["female", "male"],
    column_names=["dataset_id", "tissue", "cell_type", "disease", "sex"],
    census_version="stable",
    verbose=False,
    out="lung_blood_metadata.csv",
)
```

Strings and lists are normalized to lists for the Census `in [...]` filter;
separate metadata arguments are combined with `and`. The default
`is_primary_data=True` predicate remains active unless explicitly changed.
Check `len(meta)`, `meta.columns`, and dataset IDs before choosing a matrix
query. `meta_only=True` reads `obs` only; in the current implementation the
`gene` argument does not narrow this metadata table. If gene-level scoping is
required, use matrix mode with a small gene list and the same observation
filters, or filter the returned metadata by available dataset/observation
fields.

### Matrix query after discovery

```python
adata = gget.cellxgene(
    species="homo_sapiens",
    gene=["ACE2", "ABCA1", "SLC5A1"],
    tissue="lung",
    cell_type=["mucus secreting cell", "neuroendocrine cell"],
    column_names=["dataset_id", "tissue", "cell_type", "disease"],
    census_version="2023-05-15",
    out="lung_genes.h5ad",
)
print(adata.n_obs, adata.n_vars, list(adata.obs.columns))
```

Use canonical, case-sensitive symbols or set `ensembl=True` for Ensembl
feature IDs. Install the optional extra before the call. Do not omit all obs
filters unless the available machine can support a potentially hundreds-of-GB
read; the source explicitly warns about this case.

### Non-human primate snapshot

For `macaca_mulatta`, `callithrix_jacchus`, or `pan_troglodytes`, select
`census_version="2025-11-08"` or a newer LTS-supported snapshot, and use
filters such as `tissue` and `cell_type`. A pre-LTS snapshot may not contain
these organism keys. Record the snapshot because Census content and schema
are versioned.

## 4. 8cube partition comparison

Run a summary first, then request a named partition:

```python
from gget.gget_8cube import specificity, psi_block, gene_expression

genes = ["Gjb4", "ENSMUSG00000030945.18"]
summary = specificity(genes, verbose=False)
blocks = psi_block(
    ["Gjb4"],
    analysis_level="Across_tissues",
    analysis_type="Sex:Strain",
    verbose=False,
)
expr = gene_expression(
    ["ENSMUSG00000030945.18"],
    analysis_level="Kidney",
    analysis_type="Sex:Celltype",
    json=True,
    verbose=False,
)
```

Before interpreting the result, confirm the response still has the expected
`Analysis_level`/`Analysis_type` or partition block columns. The service takes
repeated `gene_list` query parameters; do not pass a comma-separated scalar.
`gene_list` may be a tuple, but a string raises `ValueError`. Ensembl version
suffixes are preserved, and surrounding whitespace is stripped.

`analysis_level` identifies the biological scope and `analysis_type` identifies
the partition design. Examples in the source evidence are `Across_tissues`,
`Kidney`, `Sex:Strain`, `Sex:Celltype`, and `Strain`; the service, not this
skill, owns the complete list. If an apparently valid label returns a service
error or empty CSV, retry only after checking exact case, underscores, and
colon punctuation against the current 8cube API.

## 5. Save and hand off reproducibly

For every remote call, log: function, identifier form, all filters, Census
version or 8cube partition strings, gget version, output type, row/observation
counts, and the output path. For DataFrames, use `df.to_csv(path,
index=False)` when a custom Bgee destination is needed. For JSON lists, use
`json.dump` with UTF-8. Keep raw output when response schema or biological
interpretation matters; a rerun may see updated public data.
