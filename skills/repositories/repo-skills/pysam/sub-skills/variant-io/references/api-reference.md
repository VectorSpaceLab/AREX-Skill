# VCF/BCF API Reference

## Main Entry Points

- Import with `from pysam import VariantFile, VariantHeader` or access through `pysam.VariantFile` and `pysam.VariantHeader`.
- Open files with `VariantFile(filename, mode=None, index_filename=None, header=None, drop_samples=False, duplicate_filehandle=True, ignore_truncation=False, threads=1)`.
- Use `mode=None` or `mode='r'` for auto-detected VCF, VCF.GZ, or BCF reading. Use `mode='w'` for text VCF writing, `mode='wz'` for BGZF-compressed VCF writing, and `mode='wb'` for BCF writing. A filename ending in `.gz` or `.bcf` can steer write-mode autodetection from plain `mode='w'`.
- Use context managers: `with pysam.VariantFile(path) as variants:` and `with pysam.VariantFile(out_path, 'w', header=header) as out:`.
- `threads > 1` can speed compression/decompression, but cannot be combined with `ignore_truncation=True`.

## VariantFile

Important members and signatures:

- `variant_file.header` returns a `VariantHeader`.
- `variant_file.fetch(contig=None, start=None, stop=None, region=None, reopen=False, end=None, reference=None)` returns `VariantRecord` objects.
- `variant_file.write(record)` writes one `VariantRecord` and returns the number of bytes written.
- `variant_file.subset_samples(include_samples)` keeps only selected samples and must be called before records are fetched.
- `variant_file.new_record(*args, **kwargs)` delegates to `variant_file.header.new_record`.
- `variant_file.index` is available when a BCF CSI index or bgzipped VCF tabix/CSI index is loaded.
- `drop_samples=True` ignores sample data while reading to reduce memory and parsing work.

`fetch()` with no `contig` and no `region` iterates sequentially over records from the start of the file. Regional `fetch(contig, start, stop)` requires an index. If multiple iterators over the same file are used at once, pass `reopen=True` for independent handles.

## VariantHeader

Create a write header with `header = pysam.VariantHeader()` or derive from an input file via `header = in_file.header.copy()`.

Header collections:

- `header.contigs`: mapping of contig names or integer ids to `VariantContig`; add with `header.contigs.add(id, length=None, **kwargs)`.
- `header.filters`: mapping of FILTER ids to `VariantMetadata`; add with `header.filters.add(id, number, type, description, **kwargs)`.
- `header.info`: mapping of INFO ids to `VariantMetadata`; add with `header.info.add(id, number, type, description, **kwargs)`.
- `header.formats`: mapping of FORMAT ids to `VariantMetadata`; add with `header.formats.add(id, number, type, description, **kwargs)`.
- `header.samples`: sequence-like sample-name collection; add one sample with `header.add_sample(name)` or several with `header.add_samples(*args)`.
- `header.records`: ordered `VariantHeaderRecord` objects for all metadata lines.
- `header.alts`: dictionary of ALT header records for symbolic alternate alleles.

Header mutation methods:

- `header.add_meta(key, value=None, items=None)` adds generic or structured metadata. Use `value` for simple `##key=value`; use `items=[('ID', ...), ...]` for structured lines.
- `header.add_line(line)` parses and adds a full header line such as `##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">`.
- `header.add_record(record)` copies an existing `VariantHeaderRecord` into this header.
- `header.merge(other_header)` merges metadata from another header.
- `header.copy()` returns an independent copy.
- `header.new_record(contig=None, start=0, stop=0, alleles=None, id=None, qual=None, filter=None, info=None, samples=None, **kwargs)` creates a `VariantRecord` attached to the header. Arguments are documented as experimental, so prefer explicit tests around generated records.

For new records, add contig, INFO, FORMAT, FILTER, and sample declarations to the header before assigning those fields to records.

## VariantHeaderRecord And Metadata

`VariantHeaderRecord` represents one raw metadata line. Useful properties:

- `record.type`, `record.key`, `record.value`, and `record.attrs` describe the metadata record.
- It behaves like a string-keyed mapping and supports `items()`, `keys()`, `values()`, `get()`, `update()`, and `pop()`.
- `record.remove()` exists in the API surface, but avoid relying on it in reusable workflows because the typing stub marks it as unsafe.

`VariantMetadata` describes a declared INFO, FORMAT, FILTER, or related field:

- `metadata.name`, `metadata.number`, `metadata.type`, `metadata.description`, and `metadata.record` expose declaration details.
- `remove_header()` removes the metadata from the header.

## VariantRecord

Key scalar and allele fields:

- `record.contig` and `record.chrom` are synonyms.
- `record.pos` is 1-based inclusive VCF position.
- `record.start` is 0-based inclusive Python position.
- `record.stop` is 0-based exclusive Python end.
- `record.rlen` equals `stop - start`.
- `record.id`, `record.qual`, `record.ref`, `record.alleles`, and `record.alts` are mutable properties.
- `record.copy()` returns a duplicate record attached to the same header.
- `record.translate(dst_header)` remaps the record to a different compatible header. The destination header must have the same number of samples.

Record mappings:

- `record.filter` is a `VariantRecordFilter` mapping. Use `record.filter.add('PASS')` or another declared filter; use `record.filter.clear()` before replacing filters.
- `record.info` is a mutable mapping of INFO field names to values. `END` is reserved; use `record.stop` rather than `record.info['END']`.
- `record.format` is a mapping of FORMAT field names present on the record.
- `record.samples` maps sample names or integer positions to `VariantRecordSample` objects.

## VariantRecordSample

A sample object is a mutable mapping for per-sample FORMAT values:

- Access with `record.samples['SAMPLE']` or `record.samples[0]`.
- Set declared FORMAT values with `sample['DP'] = 8`, `sample['GT'] = (0, 1)`, or `sample.update({'DP': 8})`.
- `sample.name` and `sample.index` identify the sample.
- `sample.allele_indices` gives integer allele indices with `None` for missing alleles.
- `sample.alleles` gives allele strings and can be assigned strings from `record.alleles`.
- `sample.phased` controls whether genotype alleles are phased.

Use integer genotype tuples for `GT`, for example `(0, 1)` for REF/first-ALT heterozygous. Use `sample.alleles = ('G', 'A')` only when assigning allele strings that are already defined in the record; use `sample.allele_indices` or `sample['GT']` for integer allele indices.
