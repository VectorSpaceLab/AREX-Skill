# Alignment I/O API reference

This reference covers pysam's SAM/BAM/CRAM alignment model. It intentionally excludes VCF/BCF, tabix/FASTA, command wrapper, and build topics.

## Core coordinate model

- pysam object attributes and integer arguments use Python coordinates: 0-based starts and half-open `[start, stop)` intervals.
- SAM text fields are 1-based on disk, but pysam converts them when reading and writing `AlignedSegment.reference_start`, `reference_end`, and pileup positions.
- `fetch(region="chr:100-200")` and `pileup(region="chr:100-200")` are exceptions: region strings use samtools command-line coordinates. Prefer explicit `contig`, `start`, and `stop` integers in generated code unless the user gave a region string.
- `fetch(contig, start, stop)` returns reads overlapping the interval, including reads that begin before `start` or end after `stop`.
- `pileup(contig, start, stop, truncate=True)` limits returned columns to the requested interval; without `truncate=True`, pileup may emit overlapping columns outside the interval.

## Opening `AlignmentFile`

Primary constructor shape:

```python
pysam.AlignmentFile(
    filepath_or_object,
    mode=None,
    template=None,
    reference_names=None,
    reference_lengths=None,
    text=None,
    header=None,
    add_sq_text=True,
    add_sam_header=True,
    check_header=True,
    check_sq=True,
    reference_filename=None,
    filename=None,
    index_filename=None,
    filepath_index=None,
    require_index=False,
    duplicate_filehandle=True,
    ignore_truncation=False,
    format_options=None,
    threads=1,
)
```

Use these modes most often:

- `"r"` / `"w"`: SAM text.
- `"rb"` / `"wb"`: BAM binary.
- `"rc"` / `"wc"`: CRAM.
- `"-"`: stdin/stdout stream endpoint; combine with the correct mode, for example `"rb"` for BAM input from stdin or `"w"` for SAM output to stdout.

Important constructor inputs:

- `template=other_alignment_file`: copy format/header information when writing derived output.
- `header=dict_or_alignment_header`: pass a SAM header with `SQ` records when creating files from scratch.
- `reference_names=[...]` and `reference_lengths=[...]`: alternative way to provide references when writing.
- `reference_filename="reference.fa"`: needed for many CRAM reads/writes if the CRAM cannot use embedded reference information.
- `index_filename=` or `filepath_index=`: explicit index path when the index is not discoverable beside the alignment file.
- `require_index=True`: fail at open time if an index is required by the workflow.
- `duplicate_filehandle=False`: useful for some streams/file descriptors, but changes ownership/lifetime expectations.
- `threads=N`: enable htslib worker threads for supported compression/decompression operations; avoid mixing with unsafe shared-iterator patterns.

Frequently used `AlignmentFile` members:

```python
handle.fetch(contig=None, start=None, stop=None, region=None, tid=None,
             until_eof=False, multiple_iterators=False, reference=None, end=...)
handle.pileup(contig=None, start=None, stop=None, region=None, reference=None,
              end=None, truncate=False, max_depth=8000, stepper="samtools",
              fastafile=None, ignore_overlaps=True, flag_filter=..., flag_require=...,
              ignore_orphans=True, min_base_quality=13, adjust_capq_threshold=0,
              min_mapping_quality=0, compute_baq=True, redo_baq=False)
handle.count(contig=None, start=None, stop=None, region=None, until_eof=False,
             read_callback="nofilter", reference=None, end=None)
handle.count_coverage(contig=None, start=None, stop=None, region=None,
                      quality_threshold=15, read_callback="all", reference=None, end=None)
handle.write(read)
handle.head(n, multiple_iterators=False)
handle.mate(read)
handle.has_index(); handle.check_index(); handle.get_index_statistics()
handle.get_tid(reference); handle.get_reference_name(tid); handle.get_reference_length(reference)
handle.references; handle.lengths; handle.nreferences; handle.mapped; handle.unmapped; handle.nocoordinate
```

Notes:

- `reference` and `end` are legacy aliases for `contig` and `stop`; prefer `contig` and `stop` in new code.
- `count_coverage()` returns four arrays in `A, C, G, T` order.
- `mapped`, `unmapped`, `nocoordinate`, and index statistics require an index for BAM/CRAM counts to be meaningful.
- `mate(read)` may move the file position; do not mix it with active iterators unless you isolate iterators.

## Header model

`AlignmentHeader` represents SAM header records and reference metadata.

```python
header = pysam.AlignmentHeader.from_references(
    reference_names=["chr1"],
    reference_lengths=[1000],
)
header = pysam.AlignmentHeader.from_dict({
    "HD": {"VN": "1.6", "SO": "coordinate"},
    "SQ": [{"SN": "chr1", "LN": 1000}],
})
header = pysam.AlignmentHeader.from_text("@HD\tVN:1.6\n@SQ\tSN:chr1\tLN:1000\n")
header_dict = header.to_dict()
```

Operational rules:

- Writing mapped reads requires reference definitions, typically `SQ` entries with `SN` and `LN`.
- `AlignedSegment(header)` lets `reference_name` and `next_reference_name` resolve through the header.
- Header objects are effectively read-only through mapping syntax; use `to_dict()`, modify the dictionary, then create a new `AlignmentHeader` if needed.
- When reading unusual SAM files without `SQ` lines, `check_sq=False` can permit opening, but random access and reference-name resolution may still be limited.

## `AlignedSegment` object model

Create or edit reads with `pysam.AlignedSegment()` or `pysam.AlignedSegment(header)`.

Common fields:

```python
read.query_name = "read1"
read.query_sequence = "ACGTACGT"
read.flag = 0
read.reference_id = 0
read.reference_start = 10
read.mapping_quality = 60
read.cigarstring = "8M"              # or read.cigartuples = [(0, 8)]
read.next_reference_id = -1
read.next_reference_start = -1
read.template_length = 0
read.query_qualities = pysam.qualitystring_to_array("FFFFFFFF")
read.set_tag("NM", 0)
```

Properties and helpers agents commonly need:

- Positional fields: `reference_id`, `reference_name`, `reference_start`, `reference_end`, `reference_length`, `next_reference_id`, `next_reference_name`, `next_reference_start`, `template_length`.
- Query fields: `query_name`, `query_sequence`, `query_length`, `query_qualities`, `query_qualities_str`, `query_alignment_sequence`, `query_alignment_qualities`, `query_alignment_start`, `query_alignment_end`, `query_alignment_length`.
- Flag booleans: `is_paired`, `is_proper_pair`, `is_unmapped`, `mate_is_unmapped`, `is_mapped`, `mate_is_mapped`, `is_reverse`, `mate_is_reverse`, `is_forward`, `mate_is_forward`, `is_read1`, `is_read2`, `is_secondary`, `is_qcfail`, `is_duplicate`, `is_supplementary`.
- CIGAR helpers: `cigarstring`, `cigartuples`, `get_cigar_stats()`, `get_aligned_pairs(matches_only=False, with_seq=False, with_cigar=False)`, `get_blocks()`, `get_overlap(start, end)`, `get_reference_positions(full_length=False)`.
- Orientation helpers: `get_forward_sequence()`, `get_forward_qualities()`.
- Tags: `set_tag(tag, value, value_type=None, replace=True)`, `has_tag(tag)`, `get_tag(tag, with_value_type=False)`, `get_tags(with_value_type=False)`, `set_tags(tags)`.
- Serialization: `to_string()`, `AlignedSegment.fromstring(sam_line, header)`, `to_dict()`, `AlignedSegment.from_dict(data, header)`.

CIGAR operation codes used in `cigartuples` include:

- `0` `M` alignment match or mismatch.
- `1` `I` insertion to the reference.
- `2` `D` deletion from the reference.
- `3` `N` reference skip, often intron/skipped region.
- `4` `S` soft clip.
- `5` `H` hard clip.
- `6` `P` padding.
- `7` `=` sequence match.
- `8` `X` sequence mismatch.

Read construction rules:

- Set `query_sequence` before `query_qualities`; assigning a new sequence invalidates existing qualities.
- Ensure `len(query_qualities) == len(query_sequence)` unless qualities are intentionally absent.
- Use `reference_id = -1`, `reference_start = -1`, and `is_unmapped = True` for unplaced unmapped reads.
- Use a header-aware read when setting reference names instead of ids.
- `to_string()` needs enough header context to render reference names for mapped reads.

## Pileup model

`AlignmentFile.pileup()` returns an iterator of `PileupColumn` objects. Each column is a reference position and contains `PileupRead` entries.

Common `PileupColumn` members:

```python
column.reference_id
column.reference_name
column.reference_pos      # 0-based reference position
column.nsegments          # reads covering/considered at the column
len(column)
column.pileups            # list of PileupRead proxy objects
column.get_num_aligned()
column.get_query_sequences(mark_matches=False, mark_ends=False, add_indels=False)
column.get_query_qualities()
column.get_mapping_qualities()
column.get_query_positions()
column.get_query_names()
```

Common `PileupRead` members:

```python
pileup_read.alignment             # AlignedSegment
pileup_read.query_position        # None for deletions/refskips
pileup_read.query_position_or_next
pileup_read.indel                 # insertion length or negative deletion length
pileup_read.level
pileup_read.is_del
pileup_read.is_refskip
pileup_read.is_head
pileup_read.is_tail
```

Pileup rules:

- Guard query-base access with `if not pileup_read.is_del and not pileup_read.is_refskip` because `query_position` can be `None`.
- Use `truncate=True` for exact interval columns.
- `stepper="samtools"` follows samtools-like filtering and may need `fastafile=` for BAQ/reference-dependent behavior.
- `stepper="all"` applies less filtering; `stepper="nofilter"` is useful for raw coverage checks.
- `min_base_quality`, `min_mapping_quality`, `flag_filter`, `flag_require`, `ignore_overlaps`, `ignore_orphans`, `compute_baq`, and `redo_baq` materially change reported depth.

## Indexed reads by query name

`IndexedReads` builds an in-memory index from query name to alignments:

```python
with pysam.AlignmentFile("reads.bam", "rb") as bam:
    by_name = pysam.IndexedReads(bam, multiple_iterators=True)
    by_name.build()
    hits = list(by_name.find("read1"))
```

Use it when the task is query-name lookup inside one alignment file. It is not a BAM/CRAM coordinate index and does not replace `.bai`, `.csi`, or `.crai` files.

## Quality and sequence helpers

```python
qualities = pysam.qualitystring_to_array("FFFFFFFF", offset=33)
quality_text = pysam.array_to_qualitystring(qualities, offset=33)
quality_text = pysam.qualities_to_qualitystring(read.query_qualities, offset=33)
rev = pysam.reverse_complement("ACGTN")
buf = bytearray(b"ACGTN")
pysam.reverse_complement_inplace(buf)
```

Rules:

- `qualitystring_to_array()` converts ASCII Phred quality characters to integer values.
- `array_to_qualitystring()` and `qualities_to_qualitystring()` return `None` for absent qualities.
- `reverse_complement()` accepts `str`, `bytes`, `bytearray`, `memoryview`, and packed integer sequence forms; output type follows the overload contract.
- `reverse_complement_inplace()` mutates a `bytearray` or writable `memoryview`.
