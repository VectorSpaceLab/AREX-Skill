# Gene annotation troubleshooting

Keep `verbose=True` for the first failing request. The functions use several
independent public services, so identify the failing operation before changing
IDs or flags. Do not replace an unavailable record with a different species,
release, or transcript without recording that decision.

## Invalid species, release, or database

### `ref` says the species is unavailable

`ref` requires a species with both the requested GTF and DNA/FASTA listing for
the chosen release. Check spelling and normalized form first:

```python
import gget
species = gget.ref(None, list_species=True, release=110, verbose=False)
assert "homo_sapiens" in species
```

For Ensembl Genomes species, use `list_iv_species=True`; the species is routed
to a plants, protists, metazoa, or fungi kingdom. `human`, `mouse`, and
`human_grch37` are the only documented shortcuts. `human_grch37` selects the
GRCh37 assembly and is not the same as current human GRCh38 reference files.

If the requested release is older or newer than the listing supports, ask for
an available release rather than silently falling back to latest. A release
higher than the observed latest generates a warning and may fail while
retrieving directories. Some species/resource combinations legitimately have
no ncRNA file; `ref` can return an empty FTP field for that resource.

### `search` says species not found or selects an unexpected database

Use a full species name or an explicit core database. `human` and `mouse` are
shortcuts. A string containing `core` is treated as an explicit database and
overrides `release`; for invertebrates, the database name is the supported way
to pin a release. If a plain species matches multiple databases, gget may
choose a standard human/mouse database or the first match and warn. Make the
core database explicit when assembly or strain matters.

`search` uses public Ensembl MySQL and its database listing. A valid species
name is not proof that the requested historical database is still hosted.
Retry with a current supported database after recording the failed release.

### `which` validation fails

Use exactly one of `all`, `gtf`, `cdna`, `dna`, `cds`, `ncrna`, or `pep`, or a
list of individual values. Do not pass `which=["all", "dna"]`. The command
line uses a comma-separated value such as `-w dna,gtf`; the Python API accepts
a list. `cdrna` appears as a documentation typo in some descriptions; the
implementation accepts `ncrna`.

## Identifier normalization and object type

- A string or list is accepted by `info` and `seq`; `search` accepts one or
  many search words. Preserve input order when collecting results.
- IDs beginning with `ENS` have `.version` removed before `info` and `seq`
  queries. The returned Ensembl ID may have a newer version. This is a lookup
  normalization, not a release pin.
- WormBase IDs such as `WBGene...` or `T...`, and FlyBase IDs such as `FBgn...`
  or `FBtr...`, are supported by `info` and `seq` but are not stripped using
  the Ensembl version rule. Keep their punctuation intact.
- `info` can return `object_type` values such as `Gene`, `Transcript`, or
  `Exon`. `seq(..., isoforms=True)` enumerates transcripts only for a `Gene`;
  a transcript request remains a single sequence and emits a warning.
- For a mixed `info` request, unknown IDs are warned about and omitted. If no
  requested ID is found, the return is `None`. Check keys/indexes instead of
  assuming one output row per input token.

A quick type probe is:

```python
meta = gget.info(ids, ncbi=False, uniprot=False, verbose=True)
if meta is None:
    raise LookupError("No ID resolved")
# DataFrame index, or JSON keys, carry the current reported ID.
```

## API failures, throttling, and partial results

`ref` and `search` first inspect remote directory/database listings. `search`
then connects anonymously to Ensembl MySQL and tries several public ports.
`info` can call Ensembl REST, NCBI, UniProt, and optional PDBe; `seq` calls
Ensembl REST or UniProt. A 4xx/5xx, connection failure, timeout, or temporary
rate limit may therefore affect one provider but not another.

Recovery sequence:

1. Stop a loop and retry once after a delay with one ID and `verbose=True`.
2. Reduce `info` provider calls (`ncbi=False`, `uniprot=False`, `pdb=False`) to
   isolate the failing provider.
3. Reduce a `search` term set and set a small `limit`; for `info`, split lists
   into chunks no larger than 1,000 IDs.
4. Use an explicit supported release/core database if the server reports an
   old or ambiguous database.
5. Preserve the error and upstream service in the handoff if a second bounded
   retry fails. Do not turn a network failure into “no gene.”

Public endpoints can change records, enforce fair-use limits, or be
temporarily unavailable. This skill contains no credentials, service tokens,
or offline mirror. Large `ref` files are only links until downloaded; do not
request or download all resources merely to resolve one gene.

## No UniProt record or incomplete protein metadata

A valid Ensembl gene/transcript can have no UniProt cross-reference. `info`
tries reviewed UniProt entries first and falls back to unreviewed entries only
when no reviewed result exists. `seq(translate=True)` follows the same
cross-reference path and appends no FASTA record when the sequence table is
empty. Multiple UniProt hits can also be reduced to the first result by the
metadata helper.

Diagnose without changing the biological question:

```python
meta = gget.info(
    transcript_id,
    ncbi=False,
    uniprot=True,
    verbose=True,
)
protein = gget.seq(transcript_id, translate=True, verbose=True)
nucleotide = gget.seq(transcript_id, translate=False, verbose=True)
```

If metadata resolves but `protein` is empty, report “Ensembl resolved; no
UniProt sequence returned for the normalized current transcript.” A nucleotide
sequence is a labeled fallback, not an amino-acid answer. For a gene, inspect
`canonical_transcript`; with `isoforms=True`, expect only transcript mappings
that UniProt can resolve. Do not infer that every Ensembl CDS has a UniProt
entry.

## Translation, canonical, and isoform semantics

- Default `translate=False` returns nucleotide FASTA from Ensembl REST.
- `translate=True` returns amino-acid FASTA from UniProt; it is not an
  in-process translation of the nucleotide sequence and has no release flag.
- A gene with `translate=True, isoforms=False` is resolved through its
  canonical transcript. A transcript input is used directly.
- A gene with `isoforms=True` enumerates all known transcript IDs. In protein
  mode, only UniProt-resolvable transcript records produce FASTA entries.
- A transcript with `isoforms=True` does not expand to sibling isoforms; the
  flag is ignored for non-gene objects.
- `transcribe` and `seqtype` are deprecated. `seqtype` causes a logged error
  and an early return; use the boolean `translate` flag.

When a versioned transcript is “missing,” first compare the normalized current
ID in `info` with the supplied version. `gget.seq` strips the Ensembl version,
so it cannot guarantee the historical transcript sequence. Use `gget.ref` to
record a release-aware reference resource if the analysis truly requires a
historical release, and state that a separate extraction step is needed.

## Deprecated `info` arguments

`expand=True` is deprecated because gget now expands all available metadata by
default. `ensembl_only=True` is also deprecated; prefer
`ncbi=False, uniprot=False` and leave `pdb=False`. The old flags may warn but
should not be used in new workflows. If a legacy caller passes both current
and deprecated flags, remove the deprecated ones before diagnosing provider
behavior.

## JSON, DataFrame, FASTA, and save behavior

### `search`

- Default Python return: pandas DataFrame.
- `json=True`: list of dictionaries with `ensembl_id`, `gene_name`,
  descriptions, `biotype`, list-valued `synonym`, and `url`.
- `wrap_text=True`: display-only wrapping of long DataFrame cells.
- `save=True`: fixed current-directory CSV or JSON filename.

### `info`

- Default Python return: pandas DataFrame with one row per resolved current
  ID; columns vary with object type and provider flags.
- `json=True`: dictionary keyed by current reported ID, with nested transcript,
  exon, and translation records.
- `wrap_text=True`: display-only wrapping.
- `save=True`: fixed current-directory CSV or JSON filename.

### `ref`

- Default Python return: nested dictionary of URL and release metadata.
- `ftp=True`: list of URLs.
- `save=True`: fixed current-directory JSON or text filename.

### `seq`

- Default and translated Python return: alternating FASTA header and sequence
  strings in a list.
- There is no `json`, `wrap_text`, or DataFrame mode.
- `save=True`: additionally writes a fixed current-directory FASTA file and
  still returns the list.

The Python `save` flag does not accept a path. In the CLI, use `--out FILE` for
search/info/ref output or `seq --out FILE` for FASTA; use `ref --out_dir DIR
--download` only when a full FTP download is intended. Verify the file exists,
its extension/content mode matches the flags, and its headers/IDs match the
returned value. Avoid overwriting a previous fixed-name result by running in a
fresh output directory.

## Routing boundaries

Use **sequence-tools** for pairwise/multiple alignment, identity, similarity,
or sequence comparison after `gget.seq` has returned FASTA. Use
**expression-omics** for expression matrices, tissue/cell expression, or
correlation. Use **disease-structure** for target, disease, cancer, drug, or
structure-oriented queries. This sub-skill only resolves annotation IDs,
reference files, metadata, and raw nucleotide/protein sequence records.
