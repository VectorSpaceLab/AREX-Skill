# CLI reference

This reference describes the version-0.3.4 `ncbi-genome-download` parser. The
`ngd` console entry point invokes the same `ncbi_genome_download.__main__:main`
function, so the commands are interchangeable.

## Command shape

```text
ncbi-genome-download [options] groups
ngd [options] groups
```

The positional `groups` argument is syntactically required. It is a single
comma-separated string; use `all` to expand to all groups allowed by the
selected section. The installed package reports version `0.3.4`:

```bash
ncbi-genome-download --version
ncbi-genome-download --help
```

The help output is the runtime authority for the cache-directory text and
version string. The parser's choices are:

- `--section`: `refseq`, `genbank` (default `refseq`).
- `groups`: `all`, `archaea`, `bacteria`, `fungi`, `invertebrate`,
  `metagenomes`, `plant`, `protozoa`, `vertebrate_mammalian`,
  `vertebrate_other`, `viral`.
- `--formats`: `genbank`, `fasta`, `rm`, `features`, `gff`, `protein-fasta`,
  `genpept`, `wgs`, `cds-fasta`, `rna-fna`, `rna-fasta`, `assembly-report`,
  `assembly-stats`, `translated-cds`, `all`.
- `--assembly-levels`: `all`, `complete`, `chromosome`, `scaffold`, `contig`.
- `--refseq-categories`: `all`, `reference`, `representative`, `na`.
- `--type-materials`: `any`, `all`, `type`, `reference`, `synonym`,
  `proxytype`, `neotype`.

### Section and group combinations

`metagenomes` is GenBank-only. These are valid:

```bash
ngd --section refseq bacteria
ngd --section genbank fungi
ngd --section genbank metagenomes
ngd --section refseq bacteria,viral
```

This is invalid during configuration and is rejected before candidate
selection:

```bash
ngd --section refseq metagenomes
```

With `--section refseq`, `all` expands to every supported RefSeq group except
`metagenomes`. With `--section genbank`, `all` includes `metagenomes`.

## Options

| Option | Destination / default | Effect |
|---|---|---|
| `-s`, `--section {refseq,genbank}` | `section`, `refseq` | Choose the NCBI section. |
| `-F`, `--formats VALUE` | `file_formats`, `genbank` | Select one or comma-separated file formats, or `all`. |
| `-l`, `--assembly-levels VALUE` | `assembly_levels`, `all` | Select `complete`, `chromosome`, `scaffold`, or `contig`; comma-separate values. |
| `-g`, `--genera VALUE` | `genera`, empty | Filter NCBI `organism_name`; a file path is also accepted. |
| `--genus VALUE` | `genera` | Deprecated alias for `--genera`; emits a stderr warning. |
| `--fuzzy-genus` | `fuzzy_genus`, false | Make genus matching a case-insensitive substring search. |
| `-S`, `--strains VALUE` | `strains`, empty | Exact match against the extracted strain; comma list or one-per-line file. |
| `-T`, `--species-taxids VALUE` | `species_taxids`, empty | Exact species TaxID filter; comma list or one-per-line file. |
| `-t`, `--taxids VALUE` | `taxids`, empty | Exact organism TaxID filter; comma list or one-per-line file. |
| `-A`, `--assembly-accessions VALUE` | `assembly_accessions`, empty | Exact assembly accession filter; comma list or one-per-line file. |
| `--fuzzy-accessions` | `fuzzy_accessions`, false | Match an assembly accession by configured prefix instead of exact equality. |
| `-R`, `--refseq-categories VALUE` | `refseq_categories`, `all` | Select `reference`, `representative`, `na`, or `all`. |
| `--refseq-category VALUE` | `refseq_categories` | Deprecated alias for `--refseq-categories`; emits a stderr warning. |
| `-o`, `--output-folder PATH` | `output`, current directory | Set the output root. Tree, resume, checksums, and links belong to [output-and-integrity](../../output-and-integrity/SKILL.md). |
| `--flat-output` | `flat_output`, false | Put files directly under the output root; see output-and-integrity. |
| `-H`, `--human-readable` | `human_readable`, false | Create human-readable links; see output-and-integrity. |
| `-P`, `--progress-bar` | `progress_bar`, false | Show progress bars while examining entries and downloading files. |
| `-u`, `--uri URI` | `uri`, `https://ftp.ncbi.nlm.nih.gov/genomes` | Replace the NCBI base URI, useful for a compatible mirror/test service. |
| `-p`, `--parallel N` | `parallel`, `1` | Use one worker for `1`; any other integer selects the multiprocessing path. Use a positive value appropriate for the host. |
| `-r`, `--retries N` | CLI-only, `0` | Retry a call after return status `75` for connection/chunk errors. `N` is the number of retries after the first attempt. |
| `-m`, `--metadata-table PATH` | `metadata_table`, unset | Write a tab-delimited metadata table after download; column/serialization questions belong to output-and-integrity. |
| `-n`, `--dry-run` | `dry_run`, false | Fetch and filter summaries, print matching assemblies, and skip genome-file jobs. |
| `-N`, `--no-cache` | `use_cache`, CLI default `true` | Disable the one-day assembly-summary cache. Without this flag the CLI uses cached summaries when fresh. |
| `-v`, `--verbose` | CLI-only, false | Set logging to INFO. |
| `-d`, `--debug` | CLI-only, false | Set logging to DEBUG. |
| `-V`, `--version` | parser action | Print the supplied package version and exit. |
| `-M`, `--type-materials VALUE` | `type_materials`, `any` | Filter relation-to-type-material values; use `any`, `all`, or named relations. |
| `--md5-cache-days N` | `md5_cache_days`, `1` | Set the age of per-assembly `MD5SUMS` files before refresh; output-and-integrity owns this behavior. |

A comma-separated argument is parsed literally by splitting on `,`. Do not
write `bacteria, viral`, `fasta, assembly-report`, or
`complete, chromosome`: the leading spaces become part of values and can cause
validation errors or no matches. Quote a value when the value itself contains
spaces, as in `--genera "Streptomyces coelicolor"`.

## Safe request patterns

Preview a narrow selection before fetching payloads:

```bash
ngd --section refseq \
    --formats fasta,assembly-report \
    --assembly-levels complete,chromosome \
    --refseq-categories reference,representative \
    --genera Streptomyces \
    --dry-run bacteria
```

Filter by IDs from a file and use a local output root:

```bash
ngd --section refseq --taxids taxids.txt \
    --species-taxids species-taxids.txt \
    --output-folder ./ncbi-out --dry-run bacteria
```

After inspecting the dry-run list, remove `--dry-run` and optionally use
parallel workers:

```bash
ngd --section refseq --formats fasta --parallel 4 \
    --output-folder ./ncbi-out bacteria
```

All candidate filters are combined with logical AND. `--formats` controls the
files created for each surviving assembly; it does not broaden the candidate
set. `--dry-run` still needs an assembly summary, so it may make summary HTTP
requests when the cache is disabled or stale, but it does not request genome
payloads or checksums through download jobs.

## Expected status and validation

The CLI implementation catches configuration `ValueError`s, prints the error,
and returns `-2`. Candidate selection returns `1` when no assembly survives.
A dry run or completed download returns `0`. Connection and chunked-encoding
failures are represented as `75`; the CLI wrapper repeats the complete API call
up to the requested retry count.

Use these checks before a real request:

```bash
command -v ncbi-genome-download
ngd --version
ngd --help >./ngd-help.txt
ngd --formats fasta --assembly-levels complete --dry-run bacteria
```

The last command should either print a `Considering the following ...`
section (with zero or more matching rows) or clearly report a summary/network
failure; it must not create genome payload jobs while `--dry-run` is present.
