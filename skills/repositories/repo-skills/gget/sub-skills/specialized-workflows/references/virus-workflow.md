# `gget.virus` operating contract

Evidence: `gget_virus.py`, `docs/src/en/virus.md`, `tests/test_virus.py` and
`tests/fixtures/test_virus.json`, plus the live signature report. This reference
records behavior needed to operate the public function; it is not a promise
that NCBI service responses remain unchanged.

## Signature and input forms

The live public signature is:

```text
virus(virus: str, is_accession: bool = False, outfolder: str | None = None,
host: str | None = None, min_seq_length: int | None = None,
max_seq_length: int | None = None, min_gene_count: int | None = None,
max_gene_count: int | None = None, nuc_completeness: str | None = None,
has_proteins: Any = None, proteins_complete: bool = False,
lab_passaged: bool | None = None, geographic_location: str | None = None,
submitter_country: str | None = None, min_collection_date: str | None = None,
max_collection_date: str | None = None, source_database: str | None = None,
annotated: bool | None = None, keep_temp: bool = False,
min_release_date: str | None = None, max_release_date: str | None = None,
min_mature_peptide_count: int | None = None,
max_mature_peptide_count: int | None = None, min_protein_count: int | None = None,
max_protein_count: int | None = None, max_ambiguous_chars: int | None = None,
is_sars_cov2: bool = False, is_alphainfluenza: bool = False, segment: Any = None,
vaccine_strain: bool | None = None, lineage: str | None = None,
genbank_metadata: bool = False, genbank_batch_size: int = 200,
download_all_accessions: bool = False, _skip_cache: bool = False,
provirus: bool | None = None, isolate: str | None = None, genotype: Any = None,
isolation_source: str | None = None, env_source: Any = None,
submitter_name: str | None = None, submitter_institution: str | None = None,
gen_mol_type: str | None = None, api_key: str | None = None,
baseline_metadata: str | None = None, merge_results: bool = True,
verbose: bool = True) -> None
```

The CLI exposes corresponding long options. The positional `virus` can be a
name (for example `Zika virus`), NCBI taxon ID, one accession, a
space-separated accession string, or a text file with one accession per line.
Use `is_accession=True` for accession input. For an accession-based SARS-CoV-2
or Alphainfluenza request, set `is_sars_cov2=True` or
`is_alphainfluenza=True`; name queries can be auto-detected. `download_all_accessions=True`
replaces the query with the all-viruses taxon (10239), so it is unsafe without
additional restrictive filters.

## Filter semantics and order

The implementation's effective pipeline is:

1. Validate the query and arguments, create `outfolder` and a temporary
   directory, and resolve `api_key` from the argument first and
   `NCBI_API_KEY` second. Without a key, the code logs the lower E-utilities
   rate limit; it does not require a key.
2. For SARS-CoV-2/Alphainfluenza, try NCBI datasets cached packages. Cached
   packages may apply host, complete-only, annotated, or lineage filters. The
   code records which strategy filters were applied, then applies any missing
   filters locally. If cache processing fails, it retries the normal API path.
3. Otherwise fetch NCBI Virus metadata. Server-side filters include the
   applicable host, geographic location, annotation, complete-only,
   minimum-release-date, and RefSeq constraints. Multi-accession requests are
   parsed and fetched in batches. Large responses may be streamed or chunked.
4. Deduplicate against `baseline_metadata` by accession before sequence
   download. Missing or invalid baseline files are warned about and the run
   continues without deduplication; do not assume the baseline was honored
   unless the summary reports it.
5. Apply metadata-only filters locally, including length, partial completeness,
   lab passaging, submitter country/name/institution, collection/release date,
   source database, protein count, segment, vaccine strain, isolate,
   isolation source, geographic location, and deferred host filters. These
   filters are conjunctive: a record is rejected as soon as one active filter
   fails. Matching is generally case-insensitive; location and host support
   normalized/substring matching, while several submitter/isolate fields use
   exact normalized values.
6. If any GenBank-dependent filter is active, fetch GenBank metadata before
   sequence download where possible and apply `provirus`, `genotype`,
   `has_proteins`, `gen_mol_type`, `env_source`, gene-count, or mature-peptide
   filters. This can substantially reduce the sequence download. If the early
   fetch fails, the code may download first and apply those filters afterward.
   Those filters automatically enable `genbank_metadata`.
7. Download only surviving accessions as FASTA, or stream surviving records from
   a cached FASTA. Apply sequence-dependent checks such as
   `max_ambiguous_chars` (count of `N`/`n`) and `proteins_complete`, then stream
   passing records to the final FASTA. Do not infer that a metadata length
   filter replaced sequence validation.
8. Write final metadata and, when requested, fetch detailed GenBank metadata.
   A GenBank failure normally leaves standard FASTA/metadata outputs and is
   recorded as a warning. Temporary files are removed unless `keep_temp=True`.

Important constraints: `host` and `env_source` are mutually exclusive. Valid
`nuc_completeness` values are `complete` and `partial`; `source_database` is
`genbank` or `refseq`; min/max pairs must be logically ordered. A GenBank batch
size above 500 is warned as timeout-prone. Date values may be full dates or
partial values in metadata; use ISO `YYYY-MM-DD` for predictable requests.

## Filter-to-stage map

| Need | Preferred argument | Stage / consequence |
|---|---|---|
| Complete or partial genome | `nuc_completeness` | `complete` can be server/cache-side; `partial` is local metadata filtering |
| Host | `host` | Server/cache when supported, otherwise local metadata; `human` normalizes to `Homo sapiens` |
| Length | `min_seq_length`, `max_seq_length` | Metadata length before download |
| N count | `max_ambiguous_chars` | FASTA sequence stage |
| Protein text / genes | `has_proteins` | GenBank-dependent; fetches GenBank metadata and may inspect headers |
| All proteins complete | `proteins_complete` | FASTA/header and metadata stage |
| `genotype`, `provirus`, molecule type | corresponding argument | GenBank-dependent |
| Environment | `env_source` | GenBank-dependent; cannot combine with `host` |
| Dates | collection/release min/max | API where supported plus local date checks |
| Segment, submitter, isolate, source DB | corresponding argument | Local metadata (some server-side deferral possible) |
| SARS-CoV-2 lineage | `lineage` | Cache/server when available, then local cached filtering |

List-like filters are accepted in Python for several fields (`has_proteins`,
`segment`, `genotype`, submitter/isolate/location fields); CLI examples use
comma-separated values. Verify the CLI parser's conversion for unusual values.

## Output contract

With virus name `X` normalized by replacing spaces, `/`, and `-` with `_`, the
standard output folder contains:

- `X_sequences.fasta`: final nucleotide sequences.
- `X_metadata.csv`: final tabular metadata, including sequence/header fields
  when available.
- `X_metadata.jsonl`: one final metadata object per line.
- `X_api_metadata.jsonl`: server/cached metadata snapshot can remain when
  temporary retention or a failure path needs it.
- `command_summary.txt`: command, versions, status, counts, filter exclusion
  statistics, output file names/sizes, runtime/memory when available, and
  failed-operation/recovery information.

When `genbank_metadata=True` (or auto-enabled), also expect
`X_genbank_metadata.csv`, `X_genbank_metadata_full.xml`, and
`X_genbank_metadata_full.csv` when each conversion succeeds. When a baseline is
used, merge mode creates `X_merged.csv`; no-merge mode creates `X_new.csv` and
`X_baseline_provided.csv`. Existing source files are copied, not edited.

A successful non-empty run should have matching record counts across final
FASTA, JSONL, and CSV. A zero-result run may write only the summary. A partial
API failure can save `X_partial_metadata_api_failure.jsonl` and print a
baseline recovery command; preserve it and use it as the next run's baseline.
