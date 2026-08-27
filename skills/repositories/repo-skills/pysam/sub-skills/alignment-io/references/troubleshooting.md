# Alignment I/O troubleshooting

Use this guide when pysam alignment code fails or returns surprising reads, coordinates, coverage, pileup, or qualities.

## Coordinates are off by one

Symptoms:

- User expected SAM/browser position `100`, but `reference_start` reports `99`.
- `fetch("chr1", 100, 200)` misses a read shown at `chr1:100` in SAM text.
- `fetch(region="chr1:100-200")` and `fetch("chr1", 100, 200)` disagree.

Cause:

- pysam integer coordinates are 0-based, half-open.
- SAM text and samtools-style region strings are 1-based.

Repair:

```python
# Browser/SAM chr1:100-200 inclusive -> pysam integer interval
start0 = 100 - 1
stop0 = 200
reads = list(bam.fetch("chr1", start0, stop0))

# Already a samtools-style region string: do not adjust it.
reads = list(bam.fetch(region="chr1:100-200"))
```

Prefer explicit integers in new code and document whether user inputs are 0-based or 1-based.

## `fetch()` fails without an index

Symptoms:

- `ValueError: fetch called on bamfile without index` or similar.
- `has_index()` is false.
- Region fetch works on one file but not another.

Cause:

- Random-access `fetch(contig, start, stop)` needs a BAM/CRAM index.

Repair options:

```python
# Sequential scan without an index.
for read in bam.fetch(until_eof=True):
    ...
```

```python
# If command wrappers are allowed in the workflow, create an index first.
pysam.index("reads.bam")
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    reads = list(bam.fetch("chr1", 100, 200))
```

For command-wrapper details, route to `../command-wrappers/SKILL.md`.

## Unmapped reads are missing

Symptoms:

- `fetch()` returns only reads with `reference_name` set.
- Expected unmapped records do not appear in a loop.

Cause:

- Default `fetch()` iterates placed alignments.

Repair:

```python
# Include mapped and unmapped records in file order.
for read in bam.fetch(until_eof=True):
    if read.is_unmapped:
        ...

# Only unplaced unmapped reads at the end of an indexed file.
for read in bam.fetch(contig="*"):
    ...
```

Distinguish unmapped reads with positions from unplaced reads with no coordinates when reporting counts.

## Existing iterators get confused

Symptoms:

- An iterator stops early after another `fetch()` call.
- Interleaved iteration over two regions produces missing or repeated records.

Cause:

- One open `AlignmentFile` tracks one file position.

Repair:

```python
iter1 = bam.fetch("chr1", multiple_iterators=True)
iter2 = bam.fetch("chr2")
```

Alternatives:

- Materialize small iterators with `list()` before starting another iterator.
- Open separate `AlignmentFile` handles for independent scans.
- Avoid `multiple_iterators=True` in tight loops unless needed because it reopens the file.

## Pileup proxy accessed after iterator finished

Symptoms:

- `ValueError` mentioning `PileupProxy accessed after iterator finished`.
- `column.get_query_names()` or `column.pileups` fails after the loop.

Cause:

- `PileupColumn` and `PileupRead` are proxy objects backed by the active htslib pileup iterator.

Repair:

```python
plain_rows = []
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    for column in bam.pileup("chr1", 100, 120, truncate=True):
        plain_rows.append({
            "pos": column.reference_pos,
            "names": column.get_query_names(),
            "depth": column.nsegments,
        })
```

Do not return/store live `PileupColumn` or `PileupRead` objects outside the active iteration. Store plain values instead.

## Pileup depth or bases differ from expectations

Symptoms:

- Pileup emits columns outside the requested interval.
- Depth differs from samtools or from `count_coverage()`.
- Deletions/refskips cause `TypeError` or wrong base extraction.

Causes and repairs:

- Missing `truncate=True`: add it when exact interval columns are required.
- Different filters: align `stepper`, `min_base_quality`, `min_mapping_quality`, `ignore_overlaps`, `flag_filter`, `flag_require`, `compute_baq`, and `redo_baq` with the intended semantics.
- Deletions/refskips: guard `query_position` before indexing `query_sequence`.

```python
for pileup_read in column.pileups:
    if pileup_read.is_del or pileup_read.is_refskip:
        continue
    base = pileup_read.alignment.query_sequence[pileup_read.query_position]
```

For exact samtools mpileup text output, use command wrappers rather than approximating formatting with `pileup()`.

## `query_sequence` edits erase qualities

Symptoms:

- `read.query_qualities` becomes `None` after sequence edits.
- Writing fails or downstream code sees missing quality strings.

Cause:

- pysam stores sequence and qualities together; assigning `query_sequence` invalidates existing qualities.

Repair:

```python
qualities = read.query_qualities
read.query_sequence = new_sequence
read.query_qualities = new_qualities
```

For trims:

```python
qualities = read.query_qualities
read.query_sequence = read.query_sequence[5:10]
read.query_qualities = qualities[5:10] if qualities is not None else None
```

Set sequence first, then qualities, when constructing new reads.

## Writing fails because the header is missing references

Symptoms:

- Errors mention no targets, no `SQ`, invalid tid, unknown reference, or missing header.
- Mapped reads write but cannot be read back with names.

Cause:

- Mapped reads need reference metadata in the output header.

Repair:

```python
header = {
    "HD": {"VN": "1.6", "SO": "coordinate"},
    "SQ": [{"SN": "chr1", "LN": 1000}],
}
with pysam.AlignmentFile("out.bam", "wb", header=header) as out_bam:
    out_bam.write(read)
```

Or copy a known-good template:

```python
with pysam.AlignmentFile("in.bam", "rb") as source:
    with pysam.AlignmentFile("out.bam", "wb", template=source) as out_bam:
        ...
```

If opening nonstandard SAM without `SQ` records for sequential inspection, `check_sq=False` can help, but do not rely on random access.

## CRAM reference errors

Symptoms:

- CRAM open/write fails with reference lookup, MD5, `M5`, `UR`, or external reference messages.
- CRAM reads produce unexpected sequence reconstruction failures.

Cause:

- CRAM often requires the exact reference FASTA used for encoding unless enough reference data is embedded.

Repair:

```python
with pysam.AlignmentFile("reads.cram", "rc", reference_filename="reference.fa") as cram:
    reads = list(cram.fetch("chr1", 100, 120))
```

For writing:

```python
with pysam.AlignmentFile("out.cram", "wc", header=header, reference_filename="reference.fa") as out_cram:
    out_cram.write(read)
```

If FASTA indexing or reference preparation is the task, route to `../tabix-fasta/SKILL.md`.

## Streams and `duplicate_filehandle` behave unexpectedly

Symptoms:

- Random-access calls fail on stdin/stdout.
- File descriptors close earlier or later than expected.
- Code passes Python file-like objects that do not behave like paths or real descriptors.

Causes:

- pysam alignment I/O supports `-` for stdin/stdout, but not all arbitrary Python file objects as true random-access alignment files.
- `duplicate_filehandle=True` duplicates a supplied file handle by default; changing it affects ownership and lifetime.

Repair:

- Use path strings for normal files.
- Use `pysam.AlignmentFile("-", "rb")` or `pysam.AlignmentFile("-", "w")` for standard streams.
- Avoid `fetch(contig, start, stop)` and indexing assumptions on streams.
- Change `duplicate_filehandle` only when you control the descriptor lifecycle and have a reason.

## Invalid contig or interval errors

Symptoms:

- `ValueError` for unknown contig, start greater than stop, negative intervals, or out-of-range coordinates.
- `KeyError` from coverage calls on unknown references.

Repair:

```python
if contig not in bam.references:
    raise ValueError(f"Unknown contig {contig!r}; valid contigs include {bam.references[:5]!r}")
length = bam.get_reference_length(contig)
start = max(0, start)
stop = min(stop, length)
if stop < start:
    raise ValueError("stop must be >= start")
```

For zero-length intervals, expect no fetched reads for exact interval operations unless the caller intentionally asks for an empty result.

## `count_coverage()` errors or returns unexpected lengths

Symptoms:

- `TypeError` from `count_coverage()` without a contig/region.
- Arrays are longer or shorter than expected.
- Filtered coverage differs from manual pileup.

Repair:

```python
a, c, g, t = bam.count_coverage("chr1", 100, 200, quality_threshold=20, read_callback="all")
assert len(a) == 100
```

Remember:

- With `count_coverage("chr1")`, arrays cover the whole contig.
- With `start=None`, coverage begins at zero.
- `quality_threshold` and `read_callback` change which bases are counted.

## Tags or CIGAR edits produce invalid reads

Symptoms:

- `get_tag()` raises `KeyError`.
- Written reads fail validation or have inconsistent lengths.
- CIGAR-derived positions disagree with sequence length.

Repair:

```python
if read.has_tag("NM"):
    nm = read.get_tag("NM")
read.set_tag("NM", 0)
```

When editing CIGAR:

- Ensure query-consuming operations (`M`, `I`, `S`, `=`, `X`) match query sequence length.
- Ensure reference-consuming operations (`M`, `D`, `N`, `=`, `X`) fit the reference interval.
- Prefer `cigarstring` for simple edits and `cigartuples` for generated edits.

## Opening mode is wrong

Symptoms:

- BAM opened with `"r"` or SAM opened with `"rb"` fails.
- CRAM is not detected or cannot be decoded.

Repair:

- SAM: `pysam.AlignmentFile(path, "r")` for read, `"w"` for write.
- BAM: `pysam.AlignmentFile(path, "rb")` for read, `"wb"` for write.
- CRAM: `pysam.AlignmentFile(path, "rc")` for read, `"wc"` for write, often with `reference_filename=`.

If the file extension and content disagree, prefer an explicit mode and inspect upstream file creation.
