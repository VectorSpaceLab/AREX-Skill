# Expression-omics API signatures and outputs

This reference is distilled from the four module implementations, their
English module documentation, native tests/fixtures, and the live API
signature report. It is intentionally self-contained; remote response values
and schemas can change.

## `gget.archs4`

```python
archs4(
    gene: str,
    ensembl: bool = False,
    which: str = "correlation",
    gene_count: int = 100,
    species: str = "human",
    json: bool = False,
    save: bool = False,
    verbose: bool = True,
) -> pandas.DataFrame | list[dict] | None
```

- `gene` is one symbol or one Ensembl ID. With `ensembl=True`, the wrapper
  removes a trailing version suffix, asks gget's Ensembl information service
  for the symbol, and then queries ARCHS4 by symbol.
- `which="correlation"` accepts `gene_count` and ignores the tissue species
  distinction. The response has `gene_symbol` and
  `pearson_correlation`; the queried gene is removed from the result.
- `which="tissue"` accepts `species="human"` or `"mouse"`. The tissue
  response normally has `id`, `min`, `q1`, `median`, `q3`, and `max`; an
  intermittent `color` column is discarded. Rows are sorted by descending
  `median`, then ascending `id` as a deterministic tie-breaker.
- Invalid `which` or `species` raises `ValueError`. HTTP failure raises
  `RuntimeError`. A not-found gene is logged and returns `None`.
- `json=True` converts the table to a list of record dictionaries. `save=True`
  writes `gget_archs4_gene-correlation_<GENE>.csv/.json` or
  `gget_archs4_tissue-expression_<GENE>.csv/.json` in the current directory.
- ARCHS4 uses lightweight legacy HTTP endpoints at Ma'ayan Lab. It is not a
  local database and requires network access; the current wrapper supports
  human and mouse only.

Example:

```python
import gget
corr = gget.archs4("ENSG00000106443.4", ensembl=True, gene_count=5, json=True)
atlas = gget.archs4("FUNDC1", which="tissue", species="mouse")
```

## `gget.bgee`

```python
bgee(
    gene_id: str | list[str],
    type: str = "orthologs",
    json: bool = False,
    verbose: bool = True,
) -> pandas.DataFrame | list[dict]
```

- `type` is exactly `"orthologs"` or `"expression"`; any other value raises
  `ValueError`.
- Ortholog mode permits one ID only. It performs a species lookup and returns
  columns `gene_id`, `gene_name`, `species_id`, `genus`, and `species`.
  Passing a list raises `ValueError` before the homolog request.
- Expression mode accepts a string or list. It performs a species lookup for
  every ID and raises `RuntimeError` if the IDs map to different species. The
  returned columns are `anat_entity_id`, `anat_entity_name`, `score`,
  `score_confidence`, and `expression_state`; `score` is converted to float.
- The public docs describe Ensembl IDs (for example `ENSG...`, `ENSSSCG...`,
  `ENSBTAG...`). Bgee itself includes some species not represented in Ensembl
  or Ensembl Metazoa where an NCBI gene ID may be available; validate that
  identifier against Bgee rather than assuming every numeric ID is accepted.
- `json=True` returns a list of record dictionaries. There is no Python
  `save` argument; save a DataFrame with `to_csv` or serialize the JSON list
  explicitly. The CLI can write JSON/CSV with its output options.
- Calls use the public Bgee API and require network access. Invalid/nonexistent
  IDs can fail while resolving the species or while traversing the response.

Examples:

```python
import gget
orth = gget.bgee("ENSOARG00000019163", type="orthologs")
expr = gget.bgee(["ENSBTAG00000047356", "ENSBTAG00000018317"], type="expression")
```

## `gget.cellxgene`

```python
cellxgene(
    species="homo_sapiens", gene=None, ensembl=False, column_names=None,
    meta_only=False, tissue=None, cell_type=None,
    development_stage=None, disease=None, sex=None,
    is_primary_data=True, dataset_id=None,
    tissue_general_ontology_term_id=None, tissue_general=None,
    assay_ontology_term_id=None, assay=None,
    cell_type_ontology_term_id=None,
    development_stage_ontology_term_id=None,
    disease_ontology_term_id=None, donor_id=None,
    self_reported_ethnicity_ontology_term_id=None,
    self_reported_ethnicity=None, sex_ontology_term_id=None,
    suspension_type=None, tissue_ontology_term_id=None,
    census_version="stable", verbose=True, out=None,
) -> AnnData | pandas.DataFrame | Any
```

- Supported `species` keys are `homo_sapiens`, `mus_musculus`,
  `macaca_mulatta`, `callithrix_jacchus`, and `pan_troglodytes`. A different
  key raises `ValueError` before importing the optional dependency or making a
  network request.
- `gene` accepts a string or list. With `ensembl=False`, the wrapper filters
  `feature_name`; with `ensembl=True`, it filters `feature_id`. Symbols are
  case-sensitive (for example `PAX7` for human and `Pax7` for mouse).
- `census_version` accepts service-supported labels such as `stable`,
  `latest`, or a dated snapshot such as `2023-05-15`. The current source
  documents `2025-11-08` LTS or newer for the three non-human primates.
- `meta_only=False` calls `cellxgene_census.get_anndata` and returns AnnData.
  `gene` is used only in this matrix branch. `meta_only=True` reads the
  organism's `obs` table and returns a pandas DataFrame; it applies the
  observation filters but does not use `gene` to filter features.
- Every metadata argument is a scalar or list and is translated to an `in`
  predicate. The filter includes `is_primary_data == True` by default. Set
  `is_primary_data=False` to remove that primary-only predicate; it does not
  mean “secondary data only”.
- If `column_names` is omitted, current source defaults to
  `dataset_id`, `assay`, `suspension_type`, `sex`, `tissue_general`, `tissue`,
  `cell_type`, and `disease`. Explicit names control the metadata columns
  returned in `obs`/the metadata DataFrame.
- `out` writes AnnData using its `write` method in matrix mode and CSV in
  metadata-only mode. In CLI usage, an output path is required by the module
  documentation.
- If `cellxgene_census` is unavailable, the wrapper logs setup guidance and
  returns `None`; install via `gget.setup("cellxgene")` or the package's
  documented optional dependency. The Census recommends more than 16 GB RAM
  and a network faster than 5 Mbps for practical queries; an unfiltered query
  warns that it can require hundreds of GB.

## `gget.gget_8cube`

All three functions use the following return convention:

```python
json=False -> pandas.DataFrame
json=True  -> list[dict]
save=True  -> default CSV or JSON file in the current directory
```

`gene_list` must be a `list[str]` or `tuple[str, ...]`, including for one gene.
Whitespace is stripped and Ensembl version suffixes are preserved.

### Specificity

```python
specificity(
    gene_list, json=False, save=False, verbose=True
) -> pandas.DataFrame | list[dict]
```

Queries `https://eightcubedb.onrender.com/specificity` across available
partitions. The documented table fields are `gene_name`, `ensembl_id`,
`Analysis_level`, `Analysis_type`, `Psi_mean`, `Psi_std`, `Zeta_mean`, and
`Zeta_std` (exact service casing is retained). `save=True` uses
`gget_8cube_specificity.csv` or `.json`.

### ψ-block

```python
psi_block(
    gene_list, analysis_level: str, analysis_type: str,
    json=False, save=False, verbose=True
) -> pandas.DataFrame | list[dict]
```

Queries `/psi_block` for block-level ψ scores. Examples of biological levels
are `Across_tissues` and `Kidney`; examples of partition designs are
`Sex:Strain` and `Sex:Celltype`. The returned columns depend on the partition
and contain block labels such as `Male:NZOJ` and `Female:B6J`. `save=True`
uses `gget_8cube_psiblock.csv` or `.json`.

### Normalized expression

```python
gene_expression(
    gene_list, analysis_level: str, analysis_type: str,
    json=False, save=False, verbose=True
) -> pandas.DataFrame | list[dict]
```

Queries `/gene_expression` for normalized expression mean and variance over
the requested partition. Columns vary with `analysis_type` and include the
partition metadata/block fields. `save=True` uses
`gget_8cube_expression.csv` or `.json`.

For all three endpoints, a scalar gene input raises `ValueError`; non-2xx
responses raise `RuntimeError`; non-CSV content also raises `RuntimeError`.
The 8cube service is remote and may be cold, unavailable, or change its CSV
schema.
