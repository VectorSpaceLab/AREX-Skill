# Tabix, FASTA, and FASTQ Workflows

## When To Read

Read this for copyable patterns that create tabix-indexed tables, fetch rows with parser proxies, access FASTA intervals, and stream FASTQ records with `pysam`.

## Compress and Index a BED-Like Table

Use `tabix_compress()` plus `tabix_index()` when you already have sorted text rows:

```python
from pathlib import Path
import pysam

rows = Path("regions.bed")
rows.write_text("chr1\t10\t20\tgeneA\nchr1\t30\t40\tgeneB\n", encoding="utf-8")

compressed = Path("regions.bed.gz")
pysam.tabix_compress(str(rows), str(compressed), force=True)
pysam.tabix_index(str(compressed), preset="bed", force=True)

with pysam.TabixFile(str(compressed), parser=pysam.asBed()) as table:
    hits = list(table.fetch("chr1", 0, 25))
    print([(hit.contig, hit.start, hit.end, getattr(hit, "name", None)) for hit in hits])
```

Use `preset="bed"` for normal BED files. For a custom table, pass explicit 0-based column indexes:

```python
pysam.tabix_index(
    "custom.tsv.gz",
    seq_col=0,
    start_col=1,
    end_col=2,
    zerobased=True,
    force=True,
)
```

## Fetch Rows Safely

Prefer integer intervals when your code already works with Python coordinates:

```python
with pysam.TabixFile("regions.bed.gz", parser=pysam.asBed()) as table:
    for row in table.fetch("chr1", 10, 20):
        print(row.contig, row.start, row.end)
```

Use `region=` only when accepting samtools-style strings from users:

```python
for row in table.fetch(region="chr1:11-20"):
    ...
```

Remember that `region="chr1:11-20"` describes the same 0-based half-open interval as `fetch("chr1", 10, 20)`.

## Use Parsers Deliberately

- Use `asTuple()` first when the table has unknown or non-standard columns.
- Use `asBed()`, `asGTF()`, `asGFF3()`, or `asVCF()` when the row format matches the parser.
- Pass `parser=` either at `TabixFile(...)` construction or per `fetch(...)` call.
- Convert parser proxy values to plain tuples, strings, or dictionaries before storing them outside a loop.

Example:

```python
with pysam.TabixFile("annotations.gtf.gz") as table:
    for feature in table.fetch("chr1", 1000, 2000, parser=pysam.asGTF()):
        print(feature.contig, feature.start, feature.end)
```

## Sequential Table Iteration Without an Index

Use `tabix_iterator()` only for sequential parsing of stream-like input:

```python
import io
import pysam

text = io.StringIO("chr1\t10\t20\nchr1\t30\t40\n")
for row in pysam.tabix_iterator(text, pysam.asTuple()):
    print(row[0], int(row[1]), int(row[2]))
```

If the task needs random access by genomic interval, create a BGZF file and tabix index instead.

## FASTA Random Access

Create or verify a `.fai` index before depending on random access. With pysam command wrappers installed, `pysam.faidx("genome.fa")` can create it.

```python
import pysam

with pysam.FastaFile("genome.fa") as fasta:
    sequence = fasta.fetch("chr1", 100, 120)
    print(sequence)
    print(fasta.references, fasta.lengths)
```

Use `region="chr1:101-120"` only when accepting command-style coordinates. Prefer integer coordinates in Python APIs.

## FASTQ and FASTA Streaming

Use `FastxFile` for sequential FASTA/FASTQ reads:

```python
import pysam

with pysam.FastxFile("reads.fq", persist=True) as reads:
    for record in reads:
        qualities = record.get_quality_array() if record.quality is not None else None
        print(record.name, len(record.sequence), qualities)
```

Set `persist=True` when you store records or compare them after advancing the iterator. With the default `persist=False`, record data is backed by the iterator buffer and can be overwritten as iteration continues.

## Tiny Smoke Helper

Run the bundled helper when you need a source-free sanity check:

```bash
python sub-skills/tabix-fasta/scripts/tabix_fasta_smoke.py
```

The helper creates tiny BED, FASTA, and FASTQ fixtures in a temporary directory, exercises compression/index/fetch and sequence/quality reads, and prints JSON. Use `--keep` or `--outdir` when you want to inspect the generated files.

## Workflow Selection

- If the user asks to manipulate VCF headers, INFO, FORMAT, samples, or `VariantRecord` objects, switch to `../variant-io/SKILL.md`.
- If the user asks to invoke `samtools faidx`, `bcftools index`, or other command-line wrappers from Python, switch to `../command-wrappers/SKILL.md`.
- If the user asks about BAM/CRAM/SAM reads or pileup, switch to `../alignment-io/SKILL.md`.
