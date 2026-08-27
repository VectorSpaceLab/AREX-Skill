# Expression-omics troubleshooting and recovery

## Fast triage

1. Confirm the function and input mode (`symbol` versus Ensembl ID).
2. Validate species and exact enum values before spending network time.
3. Bound the request with metadata filters, a short gene list, or a named
   partition.
4. Record the remote status code/body or exception, output type, and query
   parameters.
5. Retry only after correcting the cause; do not convert an empty table into
   a biological negative without checking identifiers and filters.

## Identifier and species failures

### ARCHS4 returns `None` or says a gene is absent

- A symbol is case-normalized to uppercase by the wrapper. Check spelling and
  whether the supplied value is actually an Ensembl ID.
- For an Ensembl input set `ensembl=True`; the wrapper strips a version suffix
  for its ID-to-symbol lookup. A versioned ID without this flag is treated as a
  symbol and commonly returns no result.
- `which` must be `correlation` or `tissue`; `species` must be `human` or
  `mouse`. Invalid values raise `ValueError` locally.
- Tissue responses with only a header or fewer than two rows are treated as no
  result. The optional `color` column is not a required output column.

### Bgee rejects an ID or type

- `type` must be exactly `orthologs` or `expression`.
- Ortholog mode accepts one ID, not a list. Use expression mode for a list.
- Expression mode does a species lookup for every ID and raises if IDs map to
  more than one species. Split the list into homogeneous batches.
- Use an Ensembl ID supported by Bgee for the target animal. Some Bgee species
  expose NCBI identifiers, but a numeric ID should not be assumed valid without
  Bgee confirmation.
- A changed Bgee response shape can surface as a missing nested field or an
  assertion during species lookup. Preserve the response/error and inspect
  the current Bgee API before adapting code; do not silently guess columns.

### CELLxGENE says species is unsupported

Use exactly one of:

```text
homo_sapiens
mus_musculus
macaca_mulatta
callithrix_jacchus
pan_troglodytes
```

The allowlist is checked before optional dependency import and network access.
A typo such as `macaca_mulata` is a local `ValueError`. For a non-human
primate, select Census `2025-11-08` LTS or newer. If an older snapshot does
not contain the organism key, change the snapshot rather than changing the
organism spelling.

### Symbols produce an empty CELLxGENE matrix

- Gene symbols are case-sensitive. Use canonical species casing, for example
  `PAX7` for human and `Pax7` for mouse.
- Use `ensembl=True` only with Ensembl feature IDs; it changes the filter key
  from `feature_name` to `feature_id`.
- `gene` is applied in matrix mode only. In the current metadata-only branch,
  the wrapper reads `obs` with observation filters and does not use `gene`.
  A metadata-only query can therefore be nonempty even when the supplied gene
  is invalid, and it cannot be used to prove gene expression.
- Check the selected Census version and returned `var` columns in matrix mode.
  A dated snapshot may contain different features or metadata than `stable`.

## Dependency, network, and resource failures

### Missing `cellxgene_census` extra

The wrapper catches `ImportError`, logs setup guidance, and returns `None`.
Install the optional dependency through the supported setup path:

```python
import gget
gget.setup("cellxgene")
```

Then retry in the prepared environment. Do not treat the `None` as an empty
Census result. If installation is unavailable, use `meta_only` only after the
extra is installed; metadata-only still imports and uses `cellxgene_census`.

### Census runs out of RAM or stalls

The source recommends more than 16 GB RAM and a network faster than 5 Mbps for
practical Census use. An unfiltered query can require hundreds of GB. Recover
by using `meta_only=True`, a small explicit `column_names` list, and multiple
observation filters (`tissue`, `cell_type`, `disease`, `sex`, `dataset_id`, or
ontology terms). Then use a small gene list in matrix mode. Do not increase
scope until row counts and dataset IDs are understood. A timeout or cancelled
read may be caused by the remote service, network, or local resources; record
which one was observed.

### Public service failure or changed schema

ARCHS4, Bgee, CELLxGENE Census, and 8cube all require remote access. Check
connectivity, service status, Census availability, and the exact request
before retrying. For a non-2xx 8cube response, the wrapper raises
`RuntimeError` with status and body. For a non-CSV 8cube response, it raises
`RuntimeError` with the response text. ARCHS4 HTTP failures likewise raise
`RuntimeError`.

If a response is nonempty but columns changed, stop downstream analysis and
compare the current columns with the documented schema. Keep the raw response
or DataFrame and report the API/version; never force renamed columns without
verifying their semantics. Bgee nested-schema changes may appear as missing
keys or assertion failures rather than a clean status error.

## 8cube input and partition errors

### Scalar-vs-list `ValueError`

All 8cube methods require a list or tuple, even for one gene:

```python
from gget.gget_8cube import psi_block

# Wrong: raises ValueError before network access.
psi_block("GJB4", "Across_tissues", "Sex:Strain")

# Right:
psi_block(["GJB4"], "Across_tissues", "Sex:Strain")
```

A comma-separated string is still a scalar. Use `['GJB4', 'GJB5']` or a tuple.
The wrapper strips surrounding whitespace but preserves Ensembl version
suffixes.

### Incorrect `analysis_level` or `analysis_type`

`psi_block` and `gene_expression` require both strings. Common evidence-backed
examples are:

```text
analysis_level: Across_tissues, Kidney
analysis_type:  Sex:Strain, Sex:Celltype, Strain
```

These are examples, not a complete service enumeration. Preserve exact case,
underscores, and colon punctuation. If an invalid combination returns a
non-2xx response, inspect the body. If it returns an empty CSV or unexpected
columns, check the service's current partition names and whether the gene is
present in that partition before retrying. Do not replace `Sex:Celltype` with a
space or a slash.

### Empty 8cube result

Check gene spelling, symbol versus Ensembl ID, version suffix, and whether the
chosen analysis level/type contains that gene. Start with `specificity([gene])`
(which does not require partition parameters), then retry a documented
partition. An empty or header-only response is not evidence that the gene is
not expressed; it may be a partition mismatch or service data update.

## Difficult synthetic checks

1. **CELLxGENE metadata-only multi-filter:** call `cellxgene` with
   `meta_only=True`, `tissue=['lung', 'blood']`, two `cell_type` values,
   `disease='normal'`, explicit `column_names`, and `census_version='stable'`.
   Verify a DataFrame and the combined `and` filters. Explain that the
   optional `cellxgene-census` extra is still required, `gene` is ignored in
   this branch, and a non-human-primate requires `2025-11-08` LTS or newer.
   Use a patched/local Census double for a test; do not fetch the whole Census.
2. **8cube invalid scalar and partition:** call `psi_block('GJB4',
   'Across_tissues', 'Sex:Strain')` and verify local `ValueError` with no
   request. Then call with `['GJB4']` but a deliberately incorrect level or
   type and verify the service error/empty-schema recovery path. This checks
   both the scalar contract and exact partition-name handling without relying
   on a large dataset.
