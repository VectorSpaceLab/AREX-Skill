---
name: io-metadata
description: "Use scikit-bio IO registry formats and metadata objects for
  reading, writing, validation, and serialization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# scikit-bio IO and Metadata

Use this sub-skill when a task involves `skbio.io.read`, `skbio.io.write`, `skbio.io.sniff`, object-oriented `.read()` / `.write()`, supported file formats, QIIME-style sample metadata, metadata column validation, missing-value schemes, or interval metadata serialization.

## Route Here For

- Reading or writing FASTA, FASTQ, Newick, GFF3, GenBank, EMBL, CLUSTAL, PHYLIP, BIOM, ordination, distance-matrix, BLAST, taxonomy dump, embedding, Stockholm, QSeq, LSMat, or sample metadata files.
- Choosing between procedural I/O (`skbio.io.read(file, format=..., into=...)`) and object-oriented I/O (`SomeClass.read(file, format=...)`, `obj.write(file, format=...)`).
- Streaming sequence records from large files or writing generators without loading a full object into memory.
- Diagnosing format sniffing, `UnrecognizedFormatError`, `FileFormatError`, format-specific parse errors, compression/filehandle caveats, and reader/writer route mismatches.
- Constructing, loading, saving, filtering, merging, and converting `SampleMetadata`, `MetadataColumn`, `NumericMetadataColumn`, and `CategoricalMetadataColumn` objects.
- Validating sample/feature metadata ID headers, directives, duplicate IDs/columns, column types, and missing-data schemes.
- Creating or attaching `Interval` and `IntervalMetadata` objects, especially for GFF3, GenBank, and EMBL feature annotations.

## Start With

- `references/format-reference.md` for supported formats, registry patterns, read/write routes, streaming, sniffing, and custom-format extension guidance.
- `references/metadata-reference.md` for `SampleMetadata`, metadata columns, missing schemes, dataframe conversion, filtering, merging, ID-header rules, and interval metadata.
- `references/troubleshooting.md` for compact diagnosis and repair patterns covering the common IO and metadata failures.
- `scripts/io_metadata_smoke.py` for a deterministic public-API smoke check that reads/writes a Newick tree, streams FASTA records, builds sample metadata, and prints JSON.

## Boundaries

- For sequence construction, sequence validation, `TabularMSA` manipulation, alignment, translation, or per-sequence metadata after records are read, use `../sequences-alignment/SKILL.md`.
- For `TreeNode` editing, rooting, comparison, or phylogenetic algorithms after Newick parsing, use `../trees-phylogeny/SKILL.md`.
- For diversity metrics, BIOM-like count table analysis, distance-matrix statistics, or ordination interpretation after files are read, use `../diversity-tables/SKILL.md` and `../statistics-ordination/SKILL.md` when present.
- Keep this sub-skill focused on serialization, registry route selection, metadata validation, metadata object transformations, and interval annotation attachment.
- Do not depend on source repository examples, fixtures, or docs at runtime; the references and smoke script here are self-contained.

## Quick Sanity Check

From any working directory with scikit-bio and its runtime dependencies installed, run:

```bash
python /path/to/skills/scikit-bio/sub-skills/io-metadata/scripts/io_metadata_smoke.py
```

The script also supports `--help` and `--indent`. It imports only public scikit-bio APIs, uses `StringIO` inputs, catches common import/format/metadata exceptions, and prints compact JSON on success.
