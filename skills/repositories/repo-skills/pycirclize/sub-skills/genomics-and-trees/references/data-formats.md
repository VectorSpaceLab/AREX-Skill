# Biological input formats and source boundaries

## Coordinate contract

Keep one coordinate convention visible in every workflow:

| Input | pyCirclize handling | Practical rule |
|---|---|---|
| BED chromosome/interval | `BedRecord.start`/`end` are zero-based, half-open | Use directly for `Circos.initialize_from_bed`; size is `end - start`. |
| Cytoband BED-like rows | Same zero-based, half-open coordinates; fifth field is the band class | Sector names in column 1 must match chromosome/sector names exactly. |
| GFF3 | Input rows are one-based, closed; `GffRecord` retains those values | `to_feature_location()` and `Gff` feature conversion use `[start - 1, end)` Biopython locations. |
| GenBank | Biopython `SeqRecord`/`SeqFeature` locations | Use integer `feature.location.start/end`; strand is normally `1` or `-1`. |
| Newick | Biopython `Tree`/`Clade` names and branch lengths | Labels are lookup keys for TreeViz; branch lengths affect radial depth unless ignored. |

Do not silently add or subtract one to GenBank/Biopython locations. Convert only
when crossing a GFF/BED boundary, and state the conversion in code comments or
workflow notes.

## GenBank

A local GenBank source can be a path, supported compressed path (`.gz`, `.bz2`,
`.zip`), `StringIO`/`TextIOWrapper`, or a list of Biopython `SeqRecord`s:

```python
from pycirclize.parser import Genbank

gbk = Genbank("sample.gbk")
seqid2size = gbk.get_seqid2size()
seqid2features = gbk.get_seqid2features(feature_type=["CDS", "tRNA"])
```

The parser uses Biopython `SeqIO.parse(..., "genbank")`. Every record needs a
valid sequence/record structure; an empty or malformed source raises a parse
failure. Compressed files are recognized by their final suffix. `Genbank`'s
`genome_seq`, `genome_length`, and `extract_features()` refer to the first
record, while `full_genome_*` and `get_seqid2*()` make multi-contig behavior
explicit.

Feature extraction defaults to `CDS`. Set `feature_type=None` to include all
feature types, or pass a list. Set `target_strand=1` or `-1` for strand-specific
tracks. A feature whose compound location crosses the circular origin is
excluded by the mapping method; inspect the original record if such features
matter biologically.

`write_cds_fasta()` requires a `translation` qualifier and skips CDS entries
without one. It writes protein translations, not nucleotide slices. Use
`write_genome_fasta()` for record sequences. Both write caller-chosen files and
should target a new temporary/output path when preserving inputs matters.

## GFF/GFF3

The parser accepts a local GFF path, including `.gz`, `.bz2`, and `.zip`.
Comments and rows with fewer than nine tab-separated columns are skipped. A
valid feature row has:

```text
seqid  source  type  start  end  score  strand  phase  attributes
```

`##sequence-region seqid start end` defines a sequence region. Its coordinates
are converted to internal `(start - 1, end)` limits. If absent, the parser
infers each seqid size from the maximum feature end, which can be smaller than
the biological sequence. Record attributes are parsed as `key=value` pairs
with comma-separated values; malformed attributes should be normalized before
plotting if they are needed as labels.

By default `Gff(path)` selects the first seqid for `records` and
`extract_features()`. For multi-seqid data:

```python
from pycirclize.parser import Gff

gff = Gff("sample.gff", target_seqid="contig-2")
features_by_seqid = gff.get_seqid2features(feature_type=None)
```

Use `target_seqid` when intentionally plotting one contig. Use the dictionary
mapping when creating one sector per seqid. A missing target seqid is an error,
not an empty plot. `extract_exon_features()` relies on `ID`/`Parent` relations
and constructs a compound location for parent features with multiple exons.

## BED and cytoband

`Bed` reads local tab-separated rows, ignores comments and malformed coordinate
rows, and retains only `chr`, `start`, `end`, optional `name`, and optional
`score`. It does not decompress input and does not validate chromosome order or
duplicate rows.

Chromosome BED:

```text
# chr  start  end
chrA   0      32
chrB   0      24
```

Cytoband rows use the same parser shape; a common form is:

```text
chrA   0   8    p1   gneg
chrA   8   16   p2   gpos100
chrA   16  32   q1   gvar
```

`Circos.initialize_from_bed()` uses the first three columns to define sectors.
`add_cytoband_tracks()` matches `rec.chr` and maps `rec.score` to a color. If a
file has headers, comments, or extra columns, ensure the first five columns
still have the expected meanings. If a chromosome is present in one file but
not the other, the unmatched bands are simply not drawn; fix the mapping when
that omission is not intentional.

## Newick and Bio.Phylo trees

TreeViz accepts a local tree path, a Newick/tree string, or an in-memory
Biopython `Tree`. The default format is `newick`; pass another Biopython format
when appropriate. Newick leaf names and internal confidence values are distinct:

```text
((A:1,B:1)90:1,(C:1,D:1)80:1)100;
```

Here `A`-`D` are leaf labels and `90`, `80`, `100` are confidence values. An
internal node with no name receives an internal TreeViz name (`N_1`, etc.) so
that its coordinates can be computed. Before annotation, inspect
`tv.all_node_labels`; use a multi-leaf query to resolve an MRCA rather than
inventing an internal label.

Trees with duplicate names are rejected. A malformed Newick string, unsupported
format, missing label, or network URL that cannot be reached should be reported
as an input problem. A local replacement tree is the reliable recovery path.

## Network-backed helpers

These helpers are intentionally separate from local parsers:

- `load_prokaryote_example_file()` downloads an allow-listed example GenBank or
  GFF file and caches it.
- `load_eukaryote_example_dataset()` downloads chromosome BED, cytoband, and
  link files and caches them.
- `fetch_genbank_by_accid()` calls NCBI Entrez and can optionally write a file.
- `TreeViz.load_tree("https://...")` reads a URL through `urlopen`.

Never make these calls automatic in a reusable or offline script. Require an
explicit network-enabled mode and cache directory, or ask the user for local
replacements. Network tests in the upstream suite are skip-if-unavailable and
are not proof that an offline run can fetch data. A cache can be absent,
read-only, stale, or corrupt; check files after fetching and prefer a fresh
local fixture for deterministic verification.

## Tooltip and static output

Feature and cytoband plotting may attach tooltip text, and `TreeViz.marker()`
passes node tooltip values to scatter. Static PNG rendering works without the
optional `ipympl` tooltip extra. Interactive notebook behavior depends on an
appropriate Jupyter backend and is outside the CPU/Agg export gate. Treat a
missing tooltip widget as a limitation of interactivity, not a parser or
rendering failure.
