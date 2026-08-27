# Alignment I/O workflows

These recipes are safe starting points for SAM/BAM/CRAM tasks with pysam. They avoid source fixtures and use only public pysam APIs.

## Open and scan alignments

```python
import pysam

with pysam.AlignmentFile("reads.bam", "rb") as bam:
    print(bam.references, bam.lengths)
    for read in bam.fetch("chr1", 100, 200):
        print(read.query_name, read.reference_start, read.cigarstring)
```

Checklist:

- Use `"r"` for SAM, `"rb"` for BAM, and `"rc"` for CRAM.
- Use `with` blocks unless a long-lived handle is intentional.
- Use `fetch(contig, start, stop)` for indexed random access.
- Use `fetch(until_eof=True)` for a sequential scan, unindexed files, or reads in file order.

## Convert user coordinates safely

When users provide Python-style coordinates, pass integers directly:

```python
start0 = 99
stop0 = 120
reads = list(bam.fetch("chr1", start0, stop0))
```

When users provide SAM/browser-style one-based coordinates, normalize explicitly:

```python
# User means chr1:100-120 inclusive in SAM/browser coordinates.
start0 = 100 - 1
stop0 = 120
reads = list(bam.fetch("chr1", start0, stop0))
```

If the user already supplied a samtools-style region string, pass it as `region=` and do not subtract one again:

```python
reads = list(bam.fetch(region="chr1:100-120"))
```

## Create a tiny BAM from scratch

```python
import pysam

header = {
    "HD": {"VN": "1.6", "SO": "coordinate"},
    "SQ": [{"SN": "chr1", "LN": 1000}],
}

read = pysam.AlignedSegment()
read.query_name = "read1"
read.query_sequence = "ACGTACGTAA"
read.flag = 0
read.reference_id = 0
read.reference_start = 100
read.mapping_quality = 60
read.cigarstring = "10M"
read.next_reference_id = -1
read.next_reference_start = -1
read.template_length = 0
read.query_qualities = pysam.qualitystring_to_array("FFFFFFFFFF")
read.set_tag("NM", 0)

with pysam.AlignmentFile("tiny.bam", "wb", header=header) as out_bam:
    out_bam.write(read)
```

Then index if command wrappers are available in the environment:

```python
pysam.index("tiny.bam")
with pysam.AlignmentFile("tiny.bam", "rb") as bam:
    indexed_reads = list(bam.fetch("chr1", 100, 110))
```

If indexing is unavailable or unsafe, read sequentially:

```python
with pysam.AlignmentFile("tiny.bam", "rb") as bam:
    reads = list(bam.fetch(until_eof=True))
```

## Edit a read without losing qualities

Assigning `query_sequence` invalidates `query_qualities`, so take a copy before editing.

```python
qualities = read.query_qualities
read.query_sequence = read.query_sequence[2:8]
read.query_qualities = qualities[2:8] if qualities is not None else None
read.cigarstring = "6M"
```

Also keep qualities the same length as the sequence:

```python
if read.query_qualities is not None:
    assert len(read.query_qualities) == len(read.query_sequence)
```

## Inspect flags, tags, and CIGAR

```python
for read in bam.fetch("chr1", 100, 200):
    if read.is_unmapped or read.is_secondary or read.is_supplementary:
        continue

    nm = read.get_tag("NM") if read.has_tag("NM") else None
    aligned_pairs = read.get_aligned_pairs(matches_only=False, with_cigar=True)
    blocks = read.get_blocks()
    overlap = read.get_overlap(100, 120)
    cigar_counts, cigar_blocks = read.get_cigar_stats()

    print(read.query_name, nm, blocks, overlap, cigar_counts[0])
```

Tips:

- Use boolean flag attributes rather than hand-decoding bit masks when readability matters.
- Use `cigartuples` when modifying CIGAR programmatically; use `cigarstring` for concise display or simple assignment.
- `get_aligned_pairs(with_seq=True)` may require MD-tag/reference context for reference bases.

## Count reads and coverage

```python
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    n = bam.count("chr1", 100, 200)
    a, c, g, t = bam.count_coverage("chr1", 100, 200, quality_threshold=20)
    depth_by_base = [sum(values) for values in zip(a, c, g, t)]
```

Rules:

- `count()` and `count_coverage()` use the same coordinate conventions as `fetch()`.
- `count_coverage(contig)` can count the whole contig, but `count_coverage()` without coordinates is an error.
- Use `read_callback="all"` to include reads that default filters would skip; use a callable for custom filters.
- Check contig names against `bam.references` before calling if user input may be invalid.

## Pileup columns over a region

```python
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    for column in bam.pileup("chr1", 100, 120, truncate=True, min_base_quality=20):
        bases = []
        for pileup_read in column.pileups:
            if pileup_read.is_del or pileup_read.is_refskip:
                continue
            read = pileup_read.alignment
            bases.append(read.query_sequence[pileup_read.query_position])
        print(column.reference_name, column.reference_pos, column.nsegments, bases)
```

For samtools-like pileup filtering with a reference:

```python
with pysam.FastaFile("reference.fa") as fasta, pysam.AlignmentFile("reads.bam", "rb") as bam:
    for column in bam.pileup("chr1", 100, 120, truncate=True, stepper="samtools", fastafile=fasta):
        print(column.reference_pos, column.get_query_sequences())
```

When a task only needs text mpileup output, route to command wrappers rather than reimplementing samtools output formatting.

## Keep pileup proxies alive only inside iteration

Correct:

```python
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    pileup_iter = bam.pileup("chr1", 100, 120, truncate=True)
    for column in pileup_iter:
        names = column.get_query_names()
        print(column.reference_pos, names)
```

Avoid storing `PileupColumn` or `PileupRead` objects for later use. Store plain values such as names, positions, and bases instead.

## Use multiple active iterators

One `AlignmentFile` has one underlying file position. If two active iterators must be interleaved, isolate one of them:

```python
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    iter_chr1 = bam.fetch("chr1", multiple_iterators=True)
    iter_chr2 = bam.fetch("chr2")
    first_chr1 = next(iter_chr1, None)
    first_chr2 = next(iter_chr2, None)
```

Prefer materializing small result lists or opening separate `AlignmentFile` handles for clearer ownership in complex code.

## Include unmapped reads

Default `fetch()` returns placed alignments. To include unmapped records in file order:

```python
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    for read in bam.fetch(until_eof=True):
        if read.is_unmapped:
            print(read.query_name)
```

To iterate only unplaced unmapped reads at the end of an indexed BAM:

```python
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    unplaced = list(bam.fetch(contig="*"))
```

## Stream SAM/BAM through stdin/stdout

pysam supports `-` for stdin/stdout, not arbitrary Python file objects for all alignment I/O.

```python
import sys
import pysam

with pysam.AlignmentFile("-", "rb") as in_bam, pysam.AlignmentFile("-", "w", template=in_bam) as out_sam:
    for read in in_bam:
        out_sam.write(read)
```

Rules:

- Use binary mode for BAM streams (`"rb"` or `"wb"`).
- Avoid random-access APIs on streams; there is no usable index-backed seek.
- If wrapping file descriptors, understand `duplicate_filehandle`; leaving the default usually protects the caller's descriptor lifetime.

## Read and write CRAM

```python
with pysam.AlignmentFile("reads.cram", "rc", reference_filename="reference.fa") as cram:
    for read in cram.fetch("chr1", 100, 120):
        print(read.query_name)
```

For writing CRAM:

```python
with pysam.AlignmentFile("template.bam", "rb") as template:
    with pysam.AlignmentFile("out.cram", "wc", template=template, reference_filename="reference.fa") as out_cram:
        for read in template.fetch(until_eof=True):
            out_cram.write(read)
```

CRAM guidance:

- Provide `reference_filename` when CRAM open/write errors mention reference lookup, MD5 mismatch, or missing reference sequence.
- Keep the reference FASTA stable between writing, indexing, and reading CRAM.
- Use the tabix/FASTA sub-skill for FASTA indexing details if the reference needs preparation.

## Query reads by name with `IndexedReads`

```python
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    index = pysam.IndexedReads(bam, multiple_iterators=True)
    index.build()
    for read in index.find("read42"):
        print(read.reference_name, read.reference_start)
```

Use this for query-name lookup, not coordinate lookup. It builds an in-memory index and can be expensive for very large files.

## Validate a local install with the bundled helper

From the generated skill root, run:

```bash
python sub-skills/alignment-io/scripts/alignment_smoke.py --outdir smoke-output
```

The helper writes a tiny BAM, attempts to index it, falls back to `fetch(until_eof=True)` if indexing is unavailable, and prints JSON with observed reads, coverage, pileup, tags, and quality conversions.
