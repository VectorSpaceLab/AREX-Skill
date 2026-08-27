# VCF/BCF Workflows

## Read Records And Inspect Fields

```python
import pysam

with pysam.VariantFile("input.vcf.gz") as variants:
    print(list(variants.header.contigs))
    print(list(variants.header.samples))
    for record in variants.fetch():
        print(record.contig, record.pos, record.ref, record.alts)
        print(dict(record.info))
        for sample_name, sample in record.samples.items():
            print(sample_name, sample.get("GT"), sample.get("DP"))
```

Use `fetch()` without arguments for sequential iteration. Use `fetch('chr1', 100_000, 200_000)` only when a BCF CSI index or bgzipped VCF tabix/CSI index is available.

## Regional Fetch

```python
with pysam.VariantFile("cohort.vcf.gz") as variants:
    for record in variants.fetch(contig="chr1", start=999, stop=2_000):
        assert record.start >= 999 or record.stop > 999
```

`start` and `stop` are 0-based, half-open coordinates. Region strings such as `region='chr1:1000-2000'` use samtools-style 1-based inclusive coordinates. Do not mix `region` with `contig`, `start`, or `stop` in the same call.

## Filter And Write Records

```python
import pysam

with pysam.VariantFile("input.vcf.gz") as incoming:
    out_header = incoming.header.copy()
    with pysam.VariantFile("filtered.vcf", "w", header=out_header) as outgoing:
        for record in incoming.fetch():
            if record.qual is None or record.qual < 20:
                continue
            if record.alts is None or len(record.alts) != 1:
                continue
            outgoing.write(record)
```

When writing records attached to a different header, first copy or reconstruct a compatible header. If the destination header is not the record's current header, call `record.translate(out_header)` before `write(record)` and ensure the sample count matches.

## Build A Header From Scratch

```python
import pysam

header = pysam.VariantHeader()
header.add_meta("fileformat", value="VCFv4.2")
header.contigs.add("chr1", length=248956422)
header.filters.add("q10", None, None, "Quality below 10")
header.info.add("DP", 1, "Integer", "Total read depth")
header.info.add("AF", ".", "Float", "Alternate allele frequency")
header.formats.add("GT", 1, "String", "Genotype")
header.formats.add("DP", 1, "Integer", "Sample read depth")
header.add_samples(["SAMPLE1", "SAMPLE2"])
```

Declare every contig, INFO key, FORMAT key, FILTER key, and sample before creating or writing records that use them. `Number` can be an integer or VCF symbolic cardinality such as `'.'`, `'A'`, `'R'`, or `'G'`.

## Create And Edit A Record

```python
record = header.new_record(
    contig="chr1",
    start=999,
    stop=1000,
    alleles=("A", "G"),
    id="rs-demo",
    qual=50,
    filter="PASS",
    info={"DP": 12, "AF": (0.25,)},
    samples=[{"GT": (0, 1), "DP": 8}, {"GT": (0, 0), "DP": 4}],
)
record.info["DP"] = 20
record.samples["SAMPLE1"]["DP"] = 11
record.samples["SAMPLE2"].phased = False
```

The reference allele is `alleles[0]`; alternate alleles are `alleles[1:]`. Genotype values are allele indices into `record.alleles`: `(0, 1)` means REF/first ALT, `(1, 1)` means first ALT homozygous, and `None` represents a missing allele within a genotype tuple.

## Assign Alleles Through Samples

```python
sample = record.samples["SAMPLE1"]
sample["GT"] = (0, 1)
assert sample.allele_indices == (0, 1)
assert sample.alleles == ("A", "G")

sample.alleles = ("G", "A")
assert sample["GT"] == (1, 0)
```

Only assign strings through `sample.alleles`. To assign integer allele indices, use `sample['GT']` or `sample.allele_indices`; assigning `(1, 0)` to `sample.alleles` raises an error.

## Subset Samples Efficiently

```python
with pysam.VariantFile("cohort.vcf.gz") as variants:
    variants.subset_samples(["SAMPLE1", "SAMPLE3"])
    for record in variants.fetch():
        assert list(record.samples) == ["SAMPLE1", "SAMPLE3"]
```

Call `subset_samples()` before iterating, fetching, or calling `next()`. It changes the read header and parsed records for that open file. If sample data is not needed at all, open with `drop_samples=True`.

## Translate Records To A Different Header

```python
with pysam.VariantFile("input.vcf") as incoming:
    out_header = pysam.VariantHeader()
    out_header.add_samples(incoming.header.samples)
    for header_record in incoming.header.records:
        out_header.add_line(str(header_record))

    with pysam.VariantFile("copy.vcf", "w", header=out_header) as outgoing:
        for record in incoming:
            record.translate(out_header)
            outgoing.write(record)
```

Use `translate()` when reconstructing headers or writing records into a header copy that is not the record's current object. The destination header must define all contigs and metadata used by records and must have the same number of samples in the same semantic order.

## Choose VCF, VCF.GZ, Or BCF

- Plain VCF (`mode='w'`) is readable and easy to inspect, but not random-access indexed unless compressed and tabix-indexed later.
- BGZF VCF (`mode='wz'` or output filename ending `.vcf.gz`) is suitable for tabix/CSI indexing and interoperability.
- BCF (`mode='wb'` or output filename ending `.bcf`) is compact and efficient; use a CSI index for regional access.
- Streams can use `'-'`, but indexing and random regional access require real seekable files.
