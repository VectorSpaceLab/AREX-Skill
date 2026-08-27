# Enrichr reference

`gget.enrichr` submits a gene list to the Enrichr/modEnrichr service. It is a
network operation with no gget credential, but the service and gene libraries
can change. The Python signature observed in the live signature report is:

```python
gget.enrichr(
    genes: str | list[str], database: str, species: str = "human",
    background_list: list[str] | None = None, background: bool = False,
    ensembl: bool = False, ensembl_bkg: bool = False, plot: bool = False,
    figsize: tuple[float, float] = (10, 10), ax=None,
    kegg_out: str | None = None, kegg_rank: int = 1,
    json: bool = False, save: bool = False, verbose: bool = True,
) -> pandas.DataFrame | list[dict] | None
```

## Namespaces and database selection

- `genes` may be a symbol string or list. A single string is converted to a
  one-element list. `None`, floating NaN values, and the string `"nan"` are
  removed before submission.
- Set `ensembl=True` for Ensembl gene IDs. gget strips a trailing version at
  the first dot, calls its Ensembl `info` lookup, and uses the first returned
  `ensembl_gene_name`. Unknown IDs are warned and skipped. If no symbol remains,
  the function logs an error and returns `None`.
- `background_list` is a symbol list unless `ensembl_bkg=True`; the latter
  performs the same conversion. A background list supplied by the user takes
  precedence over `background=True`.
- `background=True` submits gget's bundled default list of more than 20,000
  genes. It is supported only for human/mouse. A user background is also only
  supported for human/mouse. Do not silently use a whole-genome background when
  the experimental sampling frame is known; pass that frame explicitly.

Accepted species are `human`, `mouse`, `fly`, `yeast`, `worm`, and `fish`.
`mouse` is sent to the human Enrichr endpoint by the implementation. Species
other than human/mouse use the species endpoint and require a full
species-specific library name; the six shortcuts below are rejected there.

| Shortcut | Actual library |
|---|---|
| `pathway` | `KEGG_2021_Human` |
| `transcription` | `ChEA_2016` |
| `ontology` | `GO_Biological_Process_2021` |
| `diseases_drugs` | `GWAS_Catalog_2019` |
| `celltypes` | `PanglaoDB_Augmented_2021` |
| `kinase_interactions` | `KEA_2015` |

For human/mouse, use a shortcut or an exact library name such as
`ChEA_2022`. For fly, yeast, worm, or fish, consult the corresponding current
library catalog and pass its exact name. A shortcut is not automatically
translated to a model-organism equivalent.

## Standard calls and output

```python
import gget

# Human shortcut; returns a DataFrame.
df = gget.enrichr(["ACE2", "AGT", "AGTR1"], database="ontology")

# Versioned Ensembl IDs and a matching Ensembl background.
df = gget.enrichr(
    ["ENSG00000130234.12", "ENSG00000100170"],
    database="pathway", ensembl=True,
    background_list=["ENSG00000130234", "ENSG00000100170", "ENSG00000141510"],
    ensembl_bkg=True,
)

# JSON-compatible records; select top N locally after checking the response.
records = gget.enrichr("ACE2", database="KEGG_2021_Human", json=True)
top5 = records[:5] if records is not None else []
```

The DataFrame columns are, in this order:

```text
rank, path_name, p_val, z_score, combined_score,
overlapping_genes, adj_p_val, database
```

`overlapping_genes` is a list per row. Results are already in Enrichr rank
order; there is no `limit` parameter. For a reproducible top-N artifact, save
the input list, species, exact resolved database, conversion behavior, and
`df.head(N)` (or the first N JSON records), and record the date/service version.
A live library can change even when the call is unchanged.

`json=True` returns a list of dictionaries. `save=True` writes
`gget_enrichr_results.csv` for DataFrame mode or `gget_enrichr_results.json` for
JSON mode in the current directory. These fixed names make an explicit working
directory important. A plot with `plot=True` displays the first 15 rows; with
`save=True` it also writes `gget_enrichr_results.png` at 300 dpi. The first
plot axis counts overlapping genes and the secondary axis shows
`-log10(adj_p_val)` with a 0.05 guide.

## Background, plotting, and KEGG

Use a background when the tested genes are a subset of a defined assay or
universe. The API first submits the query list, then submits the background and
uses the background-analysis endpoint. It is not equivalent to merely adding
background genes to `genes`.

```python
# Plot a standard overview; do not infer significance from bar length alone.
df = gget.enrichr(
    ["ZBP1", "IRF3", "RIPK1"], database="pathway",
    plot=True, figsize=(8, 6), save=True,
)

# Requires a KEGG-named database and the optional pykegg dependency.
gget.enrichr(
    ["ZBP1", "IRF3", "RIPK1"], database="pathway",
    kegg_out="results/kegg_rank1.png", kegg_rank=1,
)
```

`kegg_out` is rejected by returning `None` if the resolved library does not
start with `KEGG`, or if `pykegg` is unavailable; install `pykegg` separately
only when pathway rendering is needed. `kegg_rank` is looked up in the result
and can fail if the requested rank does not exist. `ax` lets a caller supply a
matplotlib axis; the function still creates a secondary x-axis.

## CLI equivalents

The CLI uses the same long option names and writes JSON by default. Examples:

```bash
gget enrichr --database ontology ACE2 AGT AGTR1
gget enrichr --database KEGG_2021_Human --ensembl ENSG00000130234
gget enrichr --database pathway --kegg_out results/pathway.png --kegg_rank 1 ZBP1 IRF3 RIPK1
```

For CLI output use `--out`; `--csv` requests CSV, `--quiet` suppresses progress,
`--background` selects the bundled background, and `--background_list` plus
`--ensembl_background` supplies an explicit background. Verify the actual
installed CLI help if a wrapper version differs from the Python names.

## Validation and recovery

Before submission, assert `species` is one of the six values, choose a library
valid for that species, and inspect the converted symbols when the input is
Ensembl. A failed POST/GET raises `RuntimeError`; a missing library or no hits
may instead log an error and return `None` or an empty DataFrame. Check the
HTTP/service error and retry with a small known symbol list before changing the
biology. If Ensembl conversion fails, call the general gget `info` workflow
separately with the same IDs, remove invalid IDs, and retry; do not pass
Ensembl IDs as symbols. If background conversion is intended, confirm
`ensembl_bkg=True` independently of `ensembl`.

Do not claim a pathway plot proves a pathway: it is a visualization of the
ranked Enrichr response. Do not compare p-values across different library
versions without recording the exact library name and retrieval context.
