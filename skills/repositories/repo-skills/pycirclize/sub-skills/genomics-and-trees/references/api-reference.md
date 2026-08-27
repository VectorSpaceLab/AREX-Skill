# Genomics and tree API reference

Verified against pyCirclize **1.10.1** on Python 3.11 with the public package
imports and signatures. Runtime requirements are Python >=3.10,
`biopython`, `matplotlib`, `numpy`, and `pandas`; `ipympl` is only the optional
`tooltip` extra. These APIs have no CUDA, ROCm, MPS, or vendor accelerator
variant.

## Parser imports

```python
from pycirclize.parser import Bed, Genbank, Gff
from pycirclize import Circos
```

`Bed`, `Genbank`, and `Gff` are the public parser classes. They are file-oriented
except that `Genbank` also accepts a text stream or a list of Biopython
`SeqRecord`s.

## `Genbank`

Constructor:

```text
Genbank(gbk_source: str | Path | StringIO | TextIOWrapper | list[SeqRecord], *,
        name: str | None = None, min_range=None, max_range=None)
```

`gbk_source` may be an uncompressed file, `.gz`, `.bz2`, or `.zip` file, a
text stream, or a list of `Bio.SeqRecord.SeqRecord`. `name` overrides the
inferred file/record name. `min_range` and `max_range` are retained only for
backward compatibility; supplying them emits a warning and does not limit the
new parser.

Useful properties:

- `name`: parser name.
- `records`: list of Biopython `SeqRecord` objects.
- `genome_seq` and `genome_length`: sequence and length of the **first** record.
- `full_genome_seq` and `full_genome_length`: concatenated sequence and length
  across all records.
- `range_size`: compatibility alias for `genome_length`, not the full length.

Sequence and feature methods:

```text
calc_genome_gc_content(seq: str | None = None) -> float
calc_gc_skew(window_size: int | None = None, step_size: int | None = None,
             *, seq: str | None = None) -> (positions, values)
calc_gc_content(window_size: int | None = None, step_size: int | None = None,
                *, seq: str | None = None) -> (positions, values)
get_seqid2seq() -> dict[str, str]
get_seqid2size() -> dict[str, int]
get_seqid2features(feature_type: str | list[str] | None = "CDS",
                   target_strand: int | None = None) -> dict[str, list[SeqFeature]]
extract_features(feature_type: str | list[str] | None = "CDS", *,
                 target_strand: int | None = None,
                 target_range: tuple[int, int] | None = None) -> list[SeqFeature]
write_cds_fasta(outfile: str | Path) -> None
write_genome_fasta(outfile: str | Path) -> None
```

`calc_genome_gc_content` returns a percentage. Sliding methods return NumPy
position/value arrays; positions include the sequence endpoint, and small
sequences are handled by falling back to a whole-sequence window. GC skew is
`(G-C)/(G+C)` and is `0.0` for a window without G or C. The default sequence is
only the first record unless `seq=` is supplied explicitly.

`get_seqid2features()` filters feature types and strand and returns simplified
`SeqFeature` objects retaining `type` and `qualifiers`. Features that straddle
the circular origin are excluded. `extract_features()` operates on the first
record and optionally filters a fully contained target range. If a multi-record
plot is needed, use the dictionary method and select by sector name.

`write_cds_fasta()` writes translated CDS features only; CDS features without a
`translation` qualifier are skipped. `write_genome_fasta()` writes every record
as FASTA. These methods write to the caller's chosen path; create a temporary
or new output path when a non-destructive run is required.

## `Gff` and `GffRecord`

Constructor:

```text
Gff(gff_file: str | Path, *, name: str | None = None,
    target_seqid: str | None = None, min_range=None, max_range=None)
```

GFF input may be plain, `.gz`, `.bz2`, or `.zip`. Without `target_seqid`, the
first seqid becomes the selected record set, while all parsed seqids remain
available through `all_records` and the mapping methods.

Properties:

- `name`, `records`, `all_records`, `target_seqid`, and `seqid_list`.
- `seq_region`: `(start, end)` in internal 0-based/half-open coordinates when a
  `##sequence-region` pragma exists; otherwise `(0, max_feature_end)`.
- `genome_length`/`range_size`: the selected seqid's region end.
- `full_genome_length`: sum of all inferred/declared seqid sizes.
- `get_seqid2size()`: all seqid-to-size values, not only the selected seqid.

Methods:

```text
get_seqid2features(feature_type="CDS", target_strand=None)
extract_features(feature_type="CDS", *, target_strand=None,
                 target_range=None)
extract_exon_features(feature_type="mRNA", *, target_strand=None,
                      target_range=None)
```

`get_seqid2features()` converts GFF records to Biopython `SeqFeature`s and
retains parsed attributes as qualifiers. `extract_features()` uses the selected
seqid and returns features with optional type, strand, and fully-contained range
filters. `extract_exon_features()` joins `exon` records by `ID`/`Parent` into a
`CompoundLocation` for a parent feature when two or more exons exist.

`GffRecord` uses 1-based inclusive `start`/`end` fields as represented in GFF;
`to_feature_location()` converts them to `SimpleLocation(start - 1, end,
strand)`. Parsed strand is `1`, `-1`, or `0` for `+`, `-`, or other values.
Attributes are a `dict[str, list[str]]`. Preserve this distinction when
comparing parser records with Biopython locations.

## `Bed`, `BedRecord`, and chromosome tracks

```text
Bed(bed_file: str | Path)
Bed.records -> list[BedRecord]
BedRecord(chr, start, end, name=None, score=None)
BedRecord.size -> end - start
```

The parser reads tab-separated local files, skips comment/short/malformed rows,
and keeps the first five columns (`chr`, `start`, `end`, optional `name` and
`score`). Coordinates are zero-based half-open. It does not parse a strand
column and does not transparently decompress files.

```text
Circos.initialize_from_bed(
    bed_file, start=0, end=360, *, space=0, endspace=True,
    sector2clockwise=None,
) -> Circos
```

This uses each BED record as `{rec.chr: (rec.start, rec.end)}`. Duplicate
chromosome rows therefore cannot represent multiple ranges safely; normalize
or reject them before initialization. `sector2clockwise` is useful when query
and reference chromosomes need opposite directions.

```text
Circos.add_cytoband_tracks(
    r_lim, cytoband_file, *, track_name="cytoband", cytoband_cmap=None,
) -> None
```

The cytoband file is consumed with the same five-column BED parser. The fifth
column (`score`) is used as a cytoband label such as `gneg`, `gpos100`, `acen`,
`gvar`, or `stalk`; each matching sector gets a track and rectangles. Unknown
scores use white when the map has no key. Sector names must exactly equal the
cytoband chromosome names.

## Genomic feature bridge

```text
Track.genomic_features(
    features, *, plotstyle="box", r_lim=None,
    facecolor_handler=None, **patch_kwargs,
) -> None
```

`features` is one `Bio.SeqFeature.SeqFeature` or a sequence. `plotstyle` is
`"box"` or `"arrow"`; an unknown value raises `ValueError`. `r_lim` must be
inside the containing track's plotting limits. `facecolor_handler(feature)`
can provide a color per feature. A `facecolor` qualifier, if present, is
applied before the handler and both become patch face-color kwargs. Feature
start/end are obtained from the first/last location parts; reverse-strand
features reverse the drawing direction. Qualifiers are used to build tooltips,
but static export does not require the optional tooltip extra.

## GC track pattern

Use `get_seqid2seq()` to select the sequence for the current sector and call
`calc_gc_content(seq=seq)` or `calc_gc_skew(seq=seq)`. To show deviation from a
baseline, subtract a separately chosen percentage such as
`calc_genome_gc_content(seq=full_sequence)`. Split positive and negative values
with NumPy before passing them to `Track.fill_between`, with symmetric `vmin`
and `vmax` when visual comparison matters. Route the actual low-level fill or
line styling to `plot-primitives`.

## Trees and `TreeViz`

```text
Circos.initialize_from_tree(
    tree_data, *, start=0, end=360, r_lim=(50, 100), format="newick",
    outer=True, align_leaf_label=True, ignore_branch_length=False,
    leaf_label_size=12, leaf_label_rmargin=2.0, reverse=False,
    ladderize=False, line_kws=None, label_formatter=None,
    align_line_kws=None,
) -> (Circos, TreeViz)
```

`tree_data` may be a local path, a Newick/tree string, or a copied
`Bio.Phylo.BaseTree.Tree`. A string that parses as an HTTP(S) URL is network
backed; do not use that form in an offline workflow. Supported formats are
Biopython formats named by `format` (default `newick`), including the formats
advertised by the package such as `phyloxml`, `nexus`, `nexml`, and `cdao` when
Biopython supports them.

`track.tree(tree_data, ...) -> TreeViz` has the same tree styling controls and
is preferred when a tree must share a sector with other tracks. A sector with
size equal to `tv.leaf_num` makes alignment with leaf-indexed bar/heatmap data
straightforward.

Key properties: `track`, `tree`, `leaf_num`, `leaf_labels`, `innode_labels`,
`all_node_labels`, `max_tree_depth`, `name2xr`, and `name2rect`.

Key methods:

```text
TreeViz.load_tree(data, format) -> Bio.Phylo.BaseTree.Tree
search_target_node_name(query) -> str
get_target_xlim(query) -> tuple[float, float]
show_confidence(*, size=8, orientation="vertical", label_formatter=None, **kwargs)
highlight(query, *, color, alpha=0.5, **kwargs)
marker(query, *, marker="o", size=6, descendent=True, **kwargs)
set_node_label_props(target_node_label, **kwargs)
set_node_line_props(query, *, descendent=True,
                    apply_label_color=False, **kwargs)
```

A query can be one node label or a list/tuple; a multi-node query targets its
most recent common ancestor (MRCA). `marker(..., descendent=True)` marks all
nodes beneath the resolved clade; set it to `False` for the resolved node only.
`set_node_line_props(..., apply_label_color=True)` copies a supplied line color
to descendant labels. `show_confidence()` displays Biopython confidence values
on internal nodes and skips nodes with no confidence.

TreeViz assigns names such as `N_1` to unnamed internal nodes so it can address
them internally. Leaf labels remain the caller's names. Duplicate names are a
hard error because styling/search cannot disambiguate them; missing query names
are a `ValueError` listing available labels. `ignore_branch_length=True` or a
tree with zero maximum depth is converted to an ultrametric display tree; this
changes visual spacing, not the source tree's biological interpretation.

## Dataset helpers and boundaries

```text
load_example_tree_file(filename) -> Path
load_prokaryote_example_file(filename, cache_dir=None,
                             overwrite_cache=False) -> Path
load_eukaryote_example_dataset(name="hg38", cache_dir=None,
                               overwrite_cache=False) -> (Path, Path, list[ChrLink])
fetch_genbank_by_accid(accid, gbk_outfile=None, email=None) -> StringIO
```

Only `load_example_tree_file()` is package-local. The other three helpers use
network downloads and local caches (or NCBI Entrez for an accession). They are
explicit opt-in utilities, not safe defaults for an offline script. `ChrLink`
contains query/reference chromosome and start/end coordinates for callers that
choose to plot links.
