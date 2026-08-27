# cBioPortal reference

The cBioPortal wrapper has two public Python operations. The live signatures
are:

```python
gget.cbio_search(key_words: str | list[str]) -> list[str]
gget.cbio_plot(
    study_ids: list[str], genes: list[str], stratification: str = "tissue",
    variation_type: str = "mutation_occurrences",
    filter: tuple[str, Any] | None = None, merge_type: str = "Symbol",
    remove_non_ensembl_genes: bool = False,
    data_dir: str = "gget_cbio_cache",
    figure_dir: str = "gget_cbio_figures",
    figure_filename: str | None = None, verbose: bool = True,
    confirm_download: bool = False, dpi: int = 100, show: bool = False,
    figure_title: str | None = None,
) -> bool
```

The module uses cBioPortal metadata to search studies and cBioPortal datahub
Git LFS files to build a local heatmap. It has no credential argument, but it
needs network access, temporary/download storage, and a working `bravado`
dependency for `cbio_search`. Run `gget.setup("cbio")` once if the optional
client is absent.

## Discover and verify study IDs

```python
import gget

study_ids = gget.cbio_search(["esophag", "ovary", "ovarian"])
# Inspect, deduplicate, and select a manageable subset.
selected = [sid for sid in study_ids if sid in {"ov_tcga", "ov_tcga_pub"}]
```

A string keyword becomes a one-element list. Matching is a substring test
against the lowercased study cancer-type name or cancer-type acronym; pass
lowercase keywords for reliable case-insensitive behavior. The function
excludes cancer type `mixed` and returns sorted study IDs, not names or data.
The cBio fixture demonstrates that the query above returns study IDs including
`ov_tcga` and esophageal/ovarian cohorts. Study catalogs evolve, so save the
returned IDs with the analysis.

If `bravado` cannot be imported, `cbio_search` logs a setup message and returns
`[]`. An HTTP/specification failure can still raise from the client. Distinguish
“no matching study” from “search dependency/service failed” in a run log.

## Plot a heatmap

```python
gget.cbio_plot(
    ["msk_impact_2017"],
    ["AKT1", "ALK", "NOTCH3"],
    stratification="tissue",
    variation_type="mutation_occurrences",
    data_dir="cache/cbio",
    figure_dir="figures/cbio",
    figure_filename="lung_mutations.png",
    figure_title="Mutation occurrences by tissue",
    dpi=200,
)
```

On the first call, gget creates `data_dir/<study_id>/` and attempts these
files: `mutations.txt` and `clinical_sample.txt` are required for processing;
`cna.txt` and `sv.txt` are optional, as are `clinical_patient.txt` for the
heatmap. Existing files are reused. Raw cBioPortal data is downloaded through
Git LFS, so a cache can be large and stale; keep the study ID and cache date.
With `confirm_download=True`, gget plans the downloads and asks for a `y/n`
confirmation including the estimated size. With `False`, it downloads without
that confirmation.

The function writes a PNG under `figure_dir` and returns `True` after the plot
path is processed. The default filename is `Heatmap_<stratification>.png`,
with the filter value appended when relevant. `figure_filename` is relative to
`figure_dir`; `show=True` opens the matplotlib window. It does not return the
pivot table. If no requested gene has data, the code prints “No data to plot”
and the artifact is not useful even though the outer return value can remain
`True`.

## Stratification and variation matrix

| `variation_type` | Meaning | Required stratification/filter |
|---|---|---|
| `mutation_occurrences` | Number of mutations per gene/sample grouping | Any supported stratification |
| `cna_occurrences` | Binary CNA occurrence, when CNA data exists | Any supported stratification |
| `sv_occurrences` | Structural-variant occurrence, when SV data exists | Any supported stratification |
| `cna_nonbinary` | Original non-binary CNA values | `stratification="sample"` and `filter=("study_id", study_id)` |
| `Consequence` | Mutation consequence categories | `stratification="sample"` |

Supported `stratification` values are `tissue`, `cancer_type`,
`cancer_type_detailed`, `study_id`, and `sample`. `filter` is one exact
`(column, value)` pair such as `("tissue", "intestine")`; it is applied before
grouping. For `Consequence` and `cna_nonbinary`, the source asserts that
stratification is `sample`; for non-binary CNA it also asserts that the filter
column is `study_id`.

Default `merge_type="Symbol"` groups on `Hugo_Symbol`. `merge_type="Ensembl"`
tries to use Ensembl gene IDs, resolving ENST transcript IDs and ENSG IDs
through the Ensembl lookup service when the downloaded data requires it. If a
study has no usable Ensembl IDs, the implementation falls back to symbols.
`remove_non_ensembl_genes=True` drops rows that cannot be assigned an ENSG ID;
use it only when losing non-Ensembl records is intentional.

The heatmap preserves requested genes with missing rows as NaN and uses a gray
missing-value cell. It groups duplicate mutation records and joins multiple
consequences as `Multiple_consequences`. More than 100 columns suppress x-axis
labels; more than 372 columns are truncated for rendering. Treat those messages
as an analysis limitation and split studies or change stratification rather
than assuming all samples are visible.

## Download/cache recovery

The native downloader checks for each existing file and skips it. A missing
required file, malformed Git LFS pointer, invalid study ID, or interrupted
file can lead to `False` from the downloader or an error while `_GeneAnalysis`
loads the cache. Recover as follows:

1. Stop plotting and inspect `data_dir/<study_id>/` for non-empty tab-separated
   files. Do not use a zero-byte file as a successful cache hit.
2. Remove only the incomplete study directory, rerun with the same study ID,
   and keep `confirm_download=True` if the download size matters.
3. If cBioPortal returns a missing optional `cna`/`sv` file, choose
   `mutation_occurrences` or another variation that the study actually has.
4. If the mutation or sample file is missing, search again for a valid study ID
   and retry; do not invent filenames or manually substitute another cohort.
5. Validate the PNG exists and is non-empty, and record the exact gene list,
   study IDs, stratification, variation type, filter, cache, and figure path.

A cBioPortal result is cohort-specific and the tissue mapping in gget is an
internal convenience. Preserve the raw study IDs and do not interpret an
unclassified tissue label as a biological tissue diagnosis.
