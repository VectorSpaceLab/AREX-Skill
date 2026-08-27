# COSMIC reference

`gget.cosmic` has two distinct modes: download an archive, or query a local
TSV. The live Python signature is:

```python
gget.cosmic(
    searchterm: str | None, cosmic_tsv_path: str | None = None,
    limit: int = 100, json: bool = False, download_cosmic: bool = False,
    cosmic_project: str | None = None, cosmic_version: int | None = None,
    grch_version: int = 37, email: str | None = None,
    password: str | None = None, gget_mutate: bool = False,
    keep_genome_info: bool = False, remove_duplicates: bool = False,
    seq_id_column: str = "seq_ID", mutation_column: str = "mutation",
    mut_id_column: str = "mutation_id", out: str | None = None,
    verbose: bool = True,
) -> pandas.DataFrame | list[dict] | None
```

COSMIC is licensed cancer mutation data. Commercial use may require fees and
permission. Full database downloads require a COSMIC account; do not guess,
share, or put a password in a command or committed script. Download size is a
major constraint: the documentation describes the CMC `cancer` archive as
about 2 GB, census about 630 MB, and some cell-line archives about 2.7 GB.
Sizes and latest versions can change.

## Query an existing local TSV

```python
import gget

rows = gget.cosmic(
    "EGFR",
    cosmic_tsv_path="data/CancerMutationCensus_AllData_v101_GRCh37.tsv",
    cosmic_project="cancer",
    limit=20,
)
```

`cosmic_tsv_path` is required in query mode and is read with pandas as a
full local tab-separated table. The query is exact and case-insensitive, not a
substring search. It examines these fields for `cancer` and `cancer_example`:

```text
GENE_NAME, ACCESSION_NUMBER, LEGACY_MUTATION_ID,
Mutation CDS, Mutation AA, GENOMIC_MUTATION_ID
```

For `census`, `resistance`, `cell_line`, `genome_screen`, `targeted_screen`,
and the query-only `other` class, it examines:

```text
GENE_SYMBOL, TRANSCRIPT_ACCESSION, COSMIC_GENE_ID, COSMIC_SAMPLE_ID,
COSMIC_PHENOTYPE_ID, GENOMIC_MUTATION_ID, LEGACY_MUTATION_ID,
SAMPLE_NAME, MUTATION_CDS, MUTATION_AA, MUTATION_ID, COSMIC_STUDY_ID
```

Accession fields match both the full accession and its version-stripped form,
so `ENST00000275493` can match `ENST00000275493.2`. `limit` takes the first
matching rows in file order. Returned DataFrame column names are the source
TSV names with spaces retained; `json=True` returns JSON-compatible records.
No result raises `ValueError`; it is not silently converted into an empty
result.

If `cosmic_project` is omitted, a path containing
`CancerMutationCensus_AllData` is inferred as `cancer`; other paths are
inferred as `other`. For a custom TSV, pass the project explicitly so gget
selects the correct schema. A missing path raises `FileNotFoundError` and
prints the appropriate download command in its error text.

Query output uses `out` as a directory, not a final filename. gget writes:

```text
<out>/gget_cosmic_<cosmic_project>_<searchterm>.csv
<out>/gget_cosmic_<cosmic_project>_<searchterm>.json   # json=True
```

Without `out`, return the DataFrame/list to the caller. Prefer a path without
spaces or shell metacharacters in automated runs and check the file exists and
has rows before consuming it.

## Download mode and projects

Use `searchterm=None` and `download_cosmic=True`:

```python
gget.cosmic(
    searchterm=None, download_cosmic=True,
    cosmic_project="cancer_example", grch_version=37,
    out="data/cosmic-example",
)
```

Allowed download projects are:

| Project | Content and constraint |
|---|---|
| `cancer` | Cancer Mutation Census; feature-rich; documented as GRCh37-only |
| `cancer_example` | Small example CMC subset; no account required; latest version only |
| `census` | Curated cancer-gene mutation census |
| `resistance` | Drug-resistance mutations |
| `cell_line` | Cell Lines Project mutations; large |
| `genome_screen` | Genome-screen mutations |
| `targeted_screen` | Targeted-panel mutations |

`cosmic_version=None` resolves the latest version. `grch_version` must be 37
or 38, but choose 37 for `cancer`; the source warns that CMC is unavailable
for GRCh38. `out` is a destination folder and defaults to the current working
directory. Existing archives prompt for overwrite unless the internal call is
restarted with an explicit decision; never overwrite an irreplaceable local
archive without checking its version.

`cancer_example` is downloaded anonymously. Other projects require an account
and the source asks for consent before downloading unless both `email` and
`password` are supplied. Passing `password=` causes it to be held in the
running Python process and is discouraged; use an interactive prompt or a
secret manager outside the gget call. The full download uses curl and extracts
a tar archive, so curl, network, disk, and archive permissions are required.

## Mutation-workflow handoff

`gget_mutate=True` creates a derived `*_mutation_workflow.csv` with configurable
`seq_id_column`, `mutation_column`, and `mut_id_column`; optional
`keep_genome_info` and `remove_duplicates` change that derived schema. This
sub-skill does not teach mutation transformation. Route interpretation of that
file, nucleotide/protein mutation application, and sequence validation to the
specialized mutation-workflow sub-skill. If a user requests this export, record
that the output is a handoff artifact and validate its columns before routing.

## Failure recovery

- **Account/license:** stop on an authentication or license error. Use
  `cancer_example` for a small public fixture or obtain permission; do not
  retry with guessed credentials.
- **Wrong project/schema:** inspect the TSV header and pass the corresponding
  `cosmic_project`; `other` is query-only and is not a download project.
- **No hits:** confirm exact spelling/case-insensitive identifier and the
  project-specific column set. COSMIC does not do substring search; a gene
  symbol may be stored under `GENE_SYMBOL` rather than `GENE_NAME`.
- **Wrong GRCh/version:** use the archive's filename/header and match the
  analysis assembly. Do not mix GRCh37 and GRCh38 mutation coordinates.
- **Large or partial archive:** verify the tar extraction and TSV size, remove
  only incomplete extracted output, and resume with the same version. Avoid
  loading a multi-gigabyte TSV repeatedly during exploratory loops; make a
  licensed, reproducible local subset for development.
- **Output confusion:** query `out` is a directory, while `cosmic_tsv_path` is
  the file. Check the generated basename rather than expecting `out` itself to
  be a CSV.
