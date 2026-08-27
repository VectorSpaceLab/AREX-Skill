# IO Format Reference

This reference summarizes the public scikit-bio IO registry and supported bundled formats. Examples are self-contained and use file paths, file handles, or `io.StringIO`; they do not require source-repository fixtures.

## Core Registry APIs

| Task | API | Notes |
| --- | --- | --- |
| Procedural read | `skbio.io.read(file, format=None, into=None, verify=True, **kwargs)` | `file` may be a path, file handle, or supported IO source. Provide `into` to get one concrete object when that route exists; omit `into` or use format-specific kwargs such as `constructor=DNA` to stream records. |
| Procedural write | `skbio.io.write(obj, format, into, **kwargs)` | `format` is required because a single object may serialize to multiple formats. `into` is the output path or handle. |
| Sniff format | `skbio.io.sniff(file, into=None, **kwargs)` | Returns a format name and sniffer-provided kwargs. Use to diagnose unknown formats, but prefer explicit `format=` in production scripts. |
| Object read | `SomeSkbioClass.read(file, format=None, **kwargs)` | Built from the registry. Useful when the target type is known, e.g. `TreeNode.read(...)`, `DNA.read(...)`, `SampleMetadata.read(...)`. |
| Object write | `obj.write(file, format=None, **kwargs)` | Object defaults may exist, but pass `format=` when ambiguity matters. |
| Registered formats | `skbio.io.io_registry.list_read_formats(cls)` / `list_write_formats(cls)` | Use for route discovery by class, especially when an `UnrecognizedFormatError` says no reader/writer exists. |

Minimal patterns:

```python
from io import StringIO
from skbio import DNA, TreeNode, read, write

# Concrete object read with explicit route.
tree = read(StringIO("(a,b)root;"), format="newick", into=TreeNode)

# Equivalent object-oriented read.
tree = TreeNode.read(StringIO("(a,b)root;"), format="newick")

# Single FASTA record as DNA.
record = read(StringIO(">seq1\nACGT\n"), format="fasta", into=DNA)

# Streaming FASTA records as DNA objects.
records = list(read(StringIO(">seq1\nACGT\n"), format="fasta", constructor=DNA))

# Explicit write route.
out = StringIO()
write(tree, format="newick", into=out)
```

## Supported Bundled Formats

| Format | Reader | Writer | Main object route(s) | Route notes |
| --- | --- | --- | --- | --- |
| `binary_dm` | Yes | Yes | `PairwiseMatrix`, `SymmetricMatrix`, `DistanceMatrix` | Binary distance-matrix serialization. Use statistics/distance sub-skills for matrix analysis. |
| `biom` | Yes | Yes | `skbio.table.Table` | Binary BIOM table route. Use diversity/table sub-skill for table operations after loading. |
| `blast6` | Yes | No | `pandas.DataFrame` | Tabular BLAST outfmt 6. Requires column expectations through format kwargs when needed. |
| `blast7` | Yes | No | `pandas.DataFrame` | BLAST outfmt 7 with comments/field declarations. |
| `clustal` | Yes | Yes | `TabularMSA` | Alignment route; object manipulation belongs in `../sequences-alignment/SKILL.md`. |
| `embl` | Yes | Yes | `Sequence`, `DNA`, `RNA`, generator of `Sequence` | Feature annotations may populate interval metadata. Protein route is not supported. |
| `embed` | Yes | Yes | `ProteinEmbedding`, `ProteinVector`, and generators | Protein embedding/vector serialization. |
| `fasta` | Yes | Yes | generator of `Sequence`, `Sequence`, `DNA`, `RNA`, `Protein`, `TabularMSA` | Ambiguous by design: use `into=DNA`/`RNA`/`Protein` for a single record, `constructor=DNA`/`RNA`/`Protein` for record generators, or `into=TabularMSA` for aligned equal-length records. |
| `fastq` | Yes | Yes | generator of `Sequence`, `Sequence`, `DNA`, `RNA`, `Protein`, `TabularMSA` | Requires quality scores; specify variant/encoding kwargs when needed. |
| `genbank` | Yes | Yes | `Sequence`, `DNA`, `RNA`, `Protein`, generator of `Sequence` | Rich sequence metadata and interval features. |
| `gff3` | Yes | Yes | `Sequence`, `DNA`, `IntervalMetadata`, generator of `(seq_id, IntervalMetadata)` | `IntervalMetadata` reads usually require `seq_id`; writer may require sequence ID context. |
| `lsmat` | Yes | Yes | `PairwiseMatrix`, `SymmetricMatrix`, `DistanceMatrix` | Text lower/linear square-matrix style route. |
| `newick` | Yes | Yes | `TreeNode` | Parsing/serialization only; tree edits belong in `../trees-phylogeny/SKILL.md`. |
| `ordination` | Yes | Yes | `OrdinationResults` | Ordination object serialization; statistical interpretation belongs in the ordination/statistics sub-skill. |
| `phylip` | Yes | Yes | `TabularMSA` | PHYLIP alignment route with strict ID/shape constraints. |
| `phylip_dm` | Yes | Yes | `DistanceMatrix` | PHYLIP distance matrix route. |
| `qseq` | Yes | No | generator of `Sequence`, `Sequence`, `DNA`, `RNA`, `Protein` | Illumina QSeq reads; no writer route. |
| `sample_metadata` | Yes | Yes | `SampleMetadata` | QIIME-style sample/feature metadata TSV. See `metadata-reference.md`. |
| `stockholm` | Yes | Yes | `TabularMSA` | MSA route with Stockholm GF/GS/GR/GC metadata. |
| `taxdump` | Yes | No | `pandas.DataFrame` | NCBI taxonomy dump route. |

The registry also imports an internal empty-file sniffer to provide clearer errors for empty inputs when format inference is attempted.

## Choosing `format` and `into`

Many failures are route-selection problems rather than file corruption:

- Use `format=` when the format is known. Sniffing is convenient but can be ambiguous or impossible for streams.
- Use `into=` when the target object matters and one object should be returned. FASTA can return one `DNA` record with `into=DNA` or a `TabularMSA` with `into=TabularMSA`; Newick should use `TreeNode`; sample metadata should use `SampleMetadata`.
- If `into` is omitted or a generator route is selected with kwargs such as `constructor=DNA`, `read` may return a generator. Consume it deliberately and avoid assuming list-like behavior.
- If a file can be read but not written in a format, choose a different output route or transform the object first.
- Check `io_registry.list_read_formats(TargetClass)` and `io_registry.list_write_formats(TargetClass)` during diagnosis.

## Streaming Records

Use streaming when a file is too large to materialize:

```python
from skbio import DNA, read, write

records = read(input_handle, format="fasta", constructor=DNA)
for record in records:
    process(record.metadata.get("id"), str(record))

# Re-create or buffer a generator before writing; consumed generators cannot be reused.
write(list(read(input_handle_2, format="fasta", constructor=DNA)), format="fasta", into=output_handle)
```

For stdin or non-seekable streams, pass an explicit `format` and usually `verify=False` because sniffing needs to inspect and rewind input. Only use `verify=False` when the caller already trusts the format.

## Compression and File Handles

`skbio.io` can work with paths and many file-like sources. Practical rules:

- Prefer paths for compressed inputs when possible so registry utilities can infer and manage compression.
- For already-open handles, match text/binary mode to the format. Binary formats such as `biom` and `binary_dm` require binary-compatible handles.
- If a format appears to fail only with a handle, retry with a path or a `StringIO`/`BytesIO` object that supports `seek` and `tell`.
- Avoid relying on filename extensions for correctness; registry routes are format-name based.

## Custom Format Extension Route

Only extend the IO registry when built-in routes are insufficient. The public route is:

```python
from skbio.io import create_format

myformat = create_format("myformat")

@myformat.sniffer()
def _myformat_sniffer(fh):
    return True, {}

@myformat.reader(MyClass)
def _myformat_to_myclass(fh, **kwargs):
    return MyClass(...)

@myformat.writer(MyClass)
def _myclass_to_myformat(obj, fh, **kwargs):
    fh.write(...)
```

Extension guardrails:

- For binary formats, call `create_format("name", encoding="binary")`; for text formats, specify encoding/newline only when needed.
- Reader functions receive a file handle and return the target object; writer functions receive `(obj, fh)` and return nothing meaningful.
- Reader/writer kwargs must not use reserved registry names: `format`, `into`, `verify`, `mode`, `encoding`, `errors`, `newline`, `compression`, or `compresslevel`.
- Raise a subclass of `FileFormatError` for parse/serialization problems so callers can catch registry-format errors consistently.
- scikit-bio’s bundled formats are imported by `skbio.io`; external extensions must ensure their decorators execute before registry lookup.
