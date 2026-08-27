# Tabix, FASTA, and FASTQ API Reference

## Coordinate model

- pysam integer coordinates are 0-based and half-open: `start` is included and `end` is excluded.
- Tabix and FASTA region strings such as `region="chr1:101-200"` follow samtools/tabix convention and are 1-based inclusive.
- Do not mix `region=` with explicit `reference`, `start`, and `end` in the same fetch call.
- BED rows are conventionally 0-based half-open on disk; GTF/GFF/VCF/SAM textual positions are conventionally 1-based. Parser proxies expose Python-oriented start values where documented below.

## Compression and indexing

Primary entry points:

```python
pysam.tabix_compress(filename_in, filename_out, force=False)
pysam.tabix_index(
    filename,
    force=False,
    seq_col=None,
    start_col=None,
    end_col=None,
    preset=None,
    meta_char="#",
    line_skip=0,
    zerobased=False,
    min_shift=-1,
    index=None,
    keep_original=False,
    csi=False,
)
```

Operational notes:

- `tabix_compress()` writes BGZF-compressed output. Use `force=True` only when overwriting is intentional.
- `tabix_index()` returns the compressed filename. If `filename` is not compressed, pysam compresses it and, unless `keep_original=True`, removes the original text file.
- `preset` may be one of `"gff"`, `"bed"`, `"sam"`, `"vcf"`, `"psltbl"`, or `"pileup"`.
- For non-standard tabular files, pass `seq_col`, `start_col`, and usually `end_col`. These column numbers are 0-based Python indexes.
- `zerobased=True` tells tabix the on-disk start column is 0-based. This is needed for BED-style explicit columns; standard presets already encode their conventions.
- `meta_char` marks header/comment lines, usually `#`. `line_skip` skips a fixed number of leading lines before parsing data rows.
- `index=...` writes the `.tbi` or `.csi` to a custom path. Use the same path later via `TabixFile(..., index=...)`.
- `csi=True` creates a CSI index. `min_shift` controls CSI binning and is normally left at the default.

## `TabixFile`

Open indexed BGZF tabular files with:

```python
pysam.TabixFile(
    filename,
    mode="r",
    parser=None,
    index=None,
    encoding="ascii",
    threads=1,
)
```

Common members:

- `tabix.fetch(reference=None, start=None, end=None, region=None, parser=None, multiple_iterators=False)` returns raw strings or parser proxy rows.
- `tabix.contigs` is a read-only list of indexed reference names.
- `tabix.header` is a list-like collection of header lines without trailing newlines.
- `tabix.filename_index` exposes the loaded index filename as bytes.
- `tabix.close()`, `tabix.closed`, and context-manager methods manage the underlying C handle.

Fetch behavior:

- `fetch()` with no interval iterates all data rows.
- `fetch("chr1")`, `fetch("chr1", 1000)`, `fetch("chr1", end=2000)`, and `fetch("chr1", 1000, 2000)` are all valid interval forms.
- Unknown contigs and invalid intervals such as negative coordinates or `start > end` raise `ValueError`.
- Empty intervals such as `start == end` are allowed and yield no rows.
- Use `multiple_iterators=True` when two active iterators over the same file must be independent. Without it, a new iterator advances the shared file state.
- `threads=N` can speed decompression for some workloads; verify results when changing concurrency.

## Sequential `tabix_iterator`

`pysam.tabix_iterator(infile, parser)` iterates over a file-like object using a parser without requiring a tabix index. It is useful for sequential reads from compressed or uncompressed streams:

```python
with open("rows.tsv") as infile:
    for row in pysam.tabix_iterator(infile, pysam.asTuple()):
        print(row[0], row[1:])
```

The `infile` object should yield text lines or bytes compatible with the parser encoding. Use `TabixFile.fetch()` instead when random access through `.tbi` or `.csi` is required.

## Parser objects

All parser constructors accept an optional `encoding` and produce mutable proxy rows:

```python
pysam.asTuple(encoding="ascii")
pysam.asBed(encoding="ascii")
pysam.asGTF(encoding="ascii")
pysam.asGFF3(encoding="ascii")
pysam.asVCF(encoding="ascii")
```

Parser proxy behavior:

- Proxies support `len(row)`, integer indexing, slicing, iteration, string conversion with tab-separated fields, and assignment for writable fields.
- `asTuple()` returns generic fields only; it is best for custom tabular formats.
- `asBed()` exposes at least `contig`, `start`, and `end`; optional BED fields such as `name` or `score` raise `KeyError` or `IndexError` if the row lacks those columns.
- `asGTF()` and `asGFF3()` expose core feature fields plus parsed attributes. They provide `to_dict()`, `from_dict()`, `keys()`, and `setAttribute()` helpers for attributes.
- `asVCF()` is a tabix row parser for VCF-like text rows. It is not a replacement for `VariantFile` when users need header-aware INFO/FORMAT/sample object semantics.

## `FastaFile`

Open indexed FASTA files with:

```python
pysam.FastaFile(
    filename,
    filepath_index=None,
    filepath_index_compressed=None,
)
```

Common members:

- `fasta.fetch(reference=None, start=None, end=None, region=None)` returns a sequence string.
- `fasta.references`, `fasta.lengths`, `fasta.nreferences`, and `len(fasta)` expose reference metadata.
- `fasta.get_reference_length(reference)` returns one contig length.
- `fasta[reference]` fetches the full reference; `reference in fasta` tests presence.
- `filepath_index` points at a `.fai` file. `filepath_index_compressed` points at a `.gzi` for compressed FASTA.

Behavior notes:

- Opening a FASTA can succeed with a discoverable adjacent `.fai`; if no explicit index is provided, htslib may create or use an adjacent index depending on file state and permissions.
- Passing a bad explicit `filepath_index` raises an `IOError`/`OSError` at open time.
- `fetch()` without a reference raises `ValueError`.
- Unknown references raise `KeyError`; negative starts and `start > end` raise `ValueError`.
- Out-of-range intervals beyond the end of a known reference return an empty string rather than raising.
- `pysam.Fastafile` is a backwards-compatibility alias spelling; prefer `pysam.FastaFile` in new code.

## `FastxFile`, `FastxRecord`, and `FastqProxy`

Open FASTA or FASTQ streams with:

```python
pysam.FastxFile(filename, persist=False)
```

Common members:

- `FastxFile` is an iterator of `FastxRecord` objects with `name`, `comment`, `sequence`, and `quality` attributes.
- `persist=True` makes returned records independent of the iterator buffer. With `persist=False`, earlier records can be overwritten as iteration advances.
- `FastxRecord.get_quality_array(offset=33)` returns an array of integer quality scores for FASTQ records; it returns `None` for FASTA records without qualities.
- `FastxRecord.set_name()`, `set_comment()`, and `set_sequence(sequence, quality=None)` edit copied or newly created records. Quality length must match sequence length.
- `str(record)` renders FASTA when quality is absent and FASTQ when quality is present.
- `FastqProxy` exists in the public API for FASTQ proxy behavior but is not intended to be directly instantiated.
- `pysam.FastqFile` is a backwards-compatibility alias for `FastxFile`; prefer `FastxFile`.
