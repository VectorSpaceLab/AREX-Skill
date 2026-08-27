# Genomics and tree troubleshooting

## Parser and dependency failures

### `ModuleNotFoundError: Bio` or a parser import fails

Install the base package dependencies in the active Python environment; the
biological parser and tree routes require Biopython. The core package runtime
also requires Matplotlib, NumPy, and pandas. The optional `tooltip` extra adds
`ipympl` only; it does not replace Biopython or enable static parsing.

Confirm the environment and public API before diagnosing data:

```python
import inspect
import pycirclize
from pycirclize.parser import Bed, Genbank, Gff
from pycirclize import Circos

print(pycirclize.__version__)
print(inspect.signature(Circos.initialize_from_tree))
```

The verified target is pyCirclize 1.10.1 with Python >=3.10. Avoid mixing a
source checkout, a different installed version, and a different interpreter.

### GenBank parse failure or empty records

`Genbank` raises when no records are parsed. Check that:

- the source is actually GenBank text, not FASTA/GFF or an HTML error page;
- `LOCUS`, `ORIGIN`/sequence content, feature syntax, and terminating `//` are
  intact;
- a compressed file suffix is `.gz`, `.bz2`, or `.zip` and the archive contains
  a readable first member;
- a `StringIO`/`TextIOWrapper` is positioned at the beginning;
- a list input contains `SeqRecord`s, not plain dictionaries.

For a malformed upstream file, repair or re-export it outside pyCirclize and
preserve the original. Do not silently drop records. After parsing, inspect
`len(gbk.records)`, `gbk.get_seqid2size()`, and `gbk.records[0].features`.

### GFF parse failure, missing `seq_region`, or missing attributes

A GFF row must have nine tab-separated fields and integer start/end values.
Comments and short rows are ignored, so a file with only headers can appear
empty and raises a parse error. Ensure `##sequence-region` uses exactly
`seqid start end` after the pragma name. Without it, `Gff` infers size from the
largest feature coordinate; this is an annotation extent, not proof of full
chromosome length.

Attributes are parsed only when a token contains `=`; values are split on
commas. If labels or parent/exon reconstruction are absent, inspect the raw
attributes and normalize them to `ID=...;Parent=...` before parsing. A GFF
with `Parent` values referring to another seqid or a nonmatching parent feature
cannot be reconstructed by `extract_exon_features()` without preprocessing.

### Compressed input behaves differently

GenBank and GFF support `.gz`, `.bz2`, and `.zip`. BED does not: `Bed.parse()`
opens the given path as text. Decompress BED/cytoband files explicitly into a
new local file before passing them to `Bed` or `add_cytoband_tracks()`. For ZIP
inputs, the parser consumes the first archive member; use a single-member
archive or extract the intended member yourself.

## Coordinate, seqid, and feature issues

### Features are shifted by one base

GFF is 1-based closed; Biopython and pyCirclize feature locations are 0-based
half-open after conversion. BED is already 0-based half-open. Use:

```python
# GFF record fields: start=1, end=12 -> feature location [0:12]
start = int(feature.location.start)
end = int(feature.location.end)
```

Do not subtract one from a `SeqFeature` location. When manually constructing a
`SeqFeature`, use the Biopython convention consistently.

### `KeyError`/empty features for a sector

Compare `set(circos.sectors)` names to `set(features_by_seqid)` keys. GenBank
uses `SeqRecord.id`; GFF uses the first field; BED uses the first column. Common
mismatches include `chr1` vs `1`, version suffixes such as `.1`, whitespace, and
case. Normalize identifiers in a deliberate pre-processing step or provide an
explicit mapping; never guess across multiple possible contigs.

For GFF, `Gff(path)` without `target_seqid` selects only the first seqid for
`records`/`extract_features()`. Use `get_seqid2features()` when all seqids are
needed. For GenBank, `extract_features()` is first-record only. Multi-contig
workflows should use the seqid dictionaries and check every expected key.

### A feature is missing despite being in the source

The default filter is `feature_type="CDS"`. Pass `feature_type=None` or the
needed type/list. Check `target_strand`; `None` means both strands, while `1`
and `-1` select one. GenBank mapping skips features whose locations straddle
the circular origin. Inspect the original `SeqFeature.location` if an origin
crossing feature is biologically important and decide how to represent it.
Range filtering requires the entire feature to lie within the normalized range;
partially overlapping features are excluded.

### `genomic_features()` rejects a range or style

`r_lim` must be fully inside `track.r_plot_lim`. Create the track with enough
radius and reserve separate ranges for forward and reverse strands. Only
`plotstyle="box"` and `plotstyle="arrow"` are accepted. A location that cannot
be converted to integer start/end is printed and skipped by the plotting bridge;
fix the source or pre-filter that feature if skipping is unacceptable.

A `facecolor` qualifier can override a generic fill; a supplied
`facecolor_handler` is applied afterward. If a handler assumes a qualifier is
present, use `.get()` with a fallback and return a valid Matplotlib color.

## GC content and FASTA output

### GC arrays are empty, too short, or visually unstable

`calc_gc_content()` and `calc_gc_skew()` use the first GenBank record by default.
For a contig-specific plot pass `seq=` from `get_seqid2seq()`. On very short
sequences, explicitly set a positive `window_size` and `step_size`, or let the
small-sequence fallback use a whole-sequence window. A sequence containing no
G/C has zero GC skew; do not treat that as a parser error.

For comparative plots, document the baseline (first sequence, full concatenated
sequence, or a separately measured reference). Use symmetric limits around
zero after subtracting a baseline, and split positive/negative arrays before
`fill_between` so strand/GC interpretation is not hidden by autoscaling.

### FASTA output is empty or missing expected entries

`write_cds_fasta()` writes translations only and skips CDS features without a
`translation` qualifier. It does not translate nucleotide coordinates. Use
`write_genome_fasta()` for complete record sequences. Write to a new path and
inspect the headers; generated IDs include a counter and location, with
`protein_id`/`product` when available.

## BED/cytoband and network data

### Cytoband track is blank or bands are white

Check that chromosome/sector names match exactly, intervals are within the BED
sector range, and the fifth field contains the expected band key. Unknown keys
fall back to white. Use a custom `cytoband_cmap` for nonstandard labels. The
method creates one track per sector even if no matching band row exists, so a
blank track may indicate a mapping problem rather than a rendering failure.

### Example dataset helper fails, hangs, or modifies the cache

The prokaryote/eukaryote dataset helpers call `urlretrieve`, create/use a cache,
and may overwrite files when `overwrite_cache=True`. `fetch_genbank_by_accid`
uses Entrez and may require an email/network policy. These are explicit
network-backed operations, not offline fallbacks. In a deterministic or
restricted run:

1. skip the helper;
2. ask for or use a local BED/GFF/GenBank fixture;
3. run the parser and plot from those paths;
4. record that network acquisition was not verified.

If network use is approved, use a dedicated writable cache, verify downloaded
file sizes/content before plotting, and replace a corrupt cache explicitly. Do
not make a generated smoke script download automatically.

## Tree parsing and styling

### Newick cannot be parsed or labels are absent

Check parentheses, commas, terminal semicolon, branch lengths, and the selected
Biopython `format`. Use a local file/string or an in-memory `Tree`; a URL string
is network-backed. After initialization inspect:

```python
circos, tv = Circos.initialize_from_tree(local_tree)
print(tv.leaf_labels)
print(tv.innode_labels)
print(tv.all_node_labels)
```

TreeViz assigns names to unnamed internal nodes. Confidence values are not
necessarily node names; `show_confidence()` reads Biopython `Clade.confidence`.
If an expected leaf is absent, fix the tree or the query instead of styling a
nearby label.

### `ValueError` says a node is missing or duplicated

`search_target_node_name`, `highlight`, `marker`, and line styling validate
names. A list/tuple query resolves an MRCA, but every queried leaf must exist.
TreeViz rejects duplicate names because coordinates and styling dictionaries
would collide. Rename/uniquify nodes in a copied Biopython tree before passing
it, and retain a mapping back to source labels if interpretation requires it.

### Highlight, marker, confidence, or line style is not visible

Apply TreeViz changes before rendering. Check that `color`, `alpha`, marker
kwargs, and text size are valid Matplotlib values. `marker(...,
descendent=True)` includes all nodes below the target clade; use `False` for the
MRCA/root only. `set_node_line_props(..., descendent=False)` affects only the
resolved node. `set_node_label_props(..., size=0)` hides a leaf label.

`show_confidence()` skips internal nodes with `confidence is None`; supply a
label formatter only for values that exist. If labels are crowded, decrease
`leaf_label_size`, increase `leaf_label_rmargin`, disable alignment, or use a
smaller tree/explicit label subset. `ignore_branch_length=True` changes display
spacing when branch lengths are zero or incomparable.

### Local replacement for network tree data

If a remote tree is unavailable or disallowed, save a caller-provided Newick
string to a new local file or pass the string directly. Preserve the original
label set and confidence values needed by annotation queries. This replacement
is preferable to making retry loops or silently switching to a different public
dataset.

## Rendering, tooltips, and output checks

Use `matplotlib.use("Agg")` before importing `matplotlib.pyplot` in a headless
script. `Circos.plotfig()` can draw into an existing polar axis; `Circos.savefig`
creates a static file without requiring Jupyter. Verify `Path.exists()` and a
positive file size after export.

Interactive tooltips require the optional `ipympl` extra and a compatible
Jupyter/widget backend. A missing tooltip backend does not invalidate feature,
cytoband, tree styling, or static PNG behavior. The bundled smoke script
intentionally uses no network and no tooltip mode.
