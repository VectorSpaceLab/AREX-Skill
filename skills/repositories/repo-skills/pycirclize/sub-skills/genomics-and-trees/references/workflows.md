# Biological plotting workflows

The snippets below assume pyCirclize 1.10.1 and a local, already available
input. They show the handoff between parser objects, sectors, tracks, and
rendering; generic track styling is intentionally kept brief and routes to
`plot-primitives`.

## 1. Parse a local GenBank file and draw strand-separated features

```python
from pycirclize import Circos
from pycirclize.parser import Genbank

parser = Genbank("organism.gbk.gz")
seqid2size = parser.get_seqid2size()
circos = Circos(seqid2size, space=0 if len(seqid2size) == 1 else 2)
features_by_seqid = parser.get_seqid2features(feature_type="CDS")

for sector in circos.sectors:
    forward = sector.add_track((94, 99))
    reverse = sector.add_track((88, 93))
    for feature in features_by_seqid.get(sector.name, []):
        target = forward if feature.location.strand == 1 else reverse
        target.genomic_features(feature, plotstyle="arrow", fc="tomato" if target is forward else "skyblue", lw=0.4)

circos.savefig("genbank-features.png")
```

Use `.get()` only when an absent mapping is expected; otherwise index the
mapping so a seqid mismatch fails loudly. For several feature classes, call
`get_seqid2features(feature_type=None)` once and route by `feature.type` and
strand. Qualifiers remain available for labels:

```python
label = feature.qualifiers.get("gene", feature.qualifiers.get("product", [""]))[0]
```

Avoid labeling every feature in a dense genome. Filter labels by qualifier,
length, or a user-defined subset.

## 2. Use GFF features and GC summaries

```python
import numpy as np
from pycirclize import Circos
from pycirclize.parser import Gff

parser = Gff("annotations.gff", target_seqid="contig-1")
seqid2size = parser.get_seqid2size()
circos = Circos(seqid2size)
seqid2features = parser.get_seqid2features(feature_type=["CDS", "tRNA"])

for sector in circos.sectors:
    track = sector.add_track((90, 100))
    for feature in seqid2features.get(sector.name, []):
        track.genomic_features(feature, plotstyle="arrow", fc="orchid")

# GFF contains annotations, so obtain sequence from a matching local source.
from pycirclize.parser import Genbank
matching_gbk = Genbank("matching.gbk")
seq = matching_gbk.get_seqid2seq()["contig-1"]
positions, gc = matching_gbk.calc_gc_content(seq=seq, window_size=40, step_size=20)
positive = np.where(gc > 50, gc - 50, 0)
negative = np.where(gc < 50, gc - 50, 0)
```

`Gff` parses annotations, not nucleotide sequences; calculate GC using the
matching GenBank sequence or another explicitly supplied sequence. Do not
assume a GFF seqid is a FASTA/GenBank record id without checking.

For a first-record feature view, `parser.extract_features("CDS",
target_strand=1)` and `target_strand=-1` are convenient. For multi-seqid plots,
prefer `get_seqid2features()` and retain the key through the plotting loop.

## 3. Build chromosome sectors and cytoband tracks from local BED files

```python
from pycirclize import Circos

circos = Circos.initialize_from_bed("chromosomes.bed", space=2)
circos.add_cytoband_tracks(
    (95, 100),
    "cytoband.tsv",
    cytoband_cmap={
        "gneg": "white",
        "gpos25": "#555555",
        "gpos50": "#333333",
        "gpos75": "#111111",
        "gpos100": "black",
        "gvar": "#bbbbbb",
        "stalk": "#eeeeee",
        "acen": "#cc6666",
    },
)
for sector in circos.sectors:
    sector.text(sector.name, r=105, size=7)

circos.savefig("cytobands.png")
```

The chromosome BED must have one unambiguous row per sector name. Cytoband
rows may contain several intervals per chromosome, but their first and fifth
columns must be chromosome and band class. Add links from an explicit local
link table only after validating that both endpoint chromosome names exist.
`data-parsers` owns generic table normalization; this route owns the BED/
cytoband-to-sector bridge.

## 4. Render a local Newick tree and annotate TreeViz

```python
from pycirclize import Circos

tree_text = "((A:1,B:1)90:1,(C:1,D:1)80:1)100;"
circos, tv = Circos.initialize_from_tree(
    tree_text,
    r_lim=(40, 95),
    leaf_label_size=9,
    line_kws={"color": "grey", "lw": 1},
)

required = {"A", "B", "C", "D"}
missing = required - set(tv.leaf_labels)
if missing:
    raise ValueError(f"Tree is missing expected leaves: {sorted(missing)}")

tv.highlight(["A", "B"], color="salmon", alpha=0.35)
tv.marker("C", marker="D", size=7, color="navy", descendent=False)
tv.set_node_line_props(["C", "D"], color="royalblue", apply_label_color=True)
tv.show_confidence(size=7, color="black")

circos.savefig("tree.png")
```

A list/tuple query selects the MRCA. Use `descendent=False` when styling only
that clade root. Apply `set_node_label_props("A", size=0)` to hide a leaf label;
use `label_formatter` at initialization when a systematic label rewrite is
needed. For large trees, reduce `leaf_label_size`, consider
`ignore_branch_length=True`, and avoid dozens of individual annotations.

## 5. Combine a tree with leaf-indexed data

The tree track's `leaf_num` is the number of terminal nodes. Add adjacent tracks
to the same `tv.track.parent_sector` and order data by `tv.leaf_labels`:

```python
sector = tv.track.parent_sector
bar_track = sector.add_track((30, 38))
bar_track.bar(
    [i + 0.5 for i in range(tv.leaf_num)],
    values_in_leaf_label_order,
    width=0.3,
    color="orange",
)
```

The data vector must have exactly `tv.leaf_num` values and the same leaf order.
If the values come from a table with labels, reindex explicitly rather than
assuming input row order. Route heatmap/bar mechanics to `plot-primitives` or
`data-parsers`.

## 6. Offline replacement for network-backed examples

When a README or notebook uses a dataset helper, replace the call with paths
provided by the caller:

```python
# Explicitly local; no URL, cache creation, or overwrite.
chromosome_bed = "data/hg38.chromosomes.bed"
cytoband = "data/hg38.cytoband.tsv"
circos = Circos.initialize_from_bed(chromosome_bed)
circos.add_cytoband_tracks((95, 100), cytoband)
```

If network use is explicitly approved, run the helper separately, record the
chosen cache directory and downloaded filenames, inspect file existence, and
then pass those local paths to the plotting workflow. Never hide the fetch in a
plot constructor or smoke script.

## 7. Deterministic verification

Run the bundled no-network check:

```text
python scripts/genomics_tree_smoke.py --output /tmp/pycirclize-genomics-tree.png
```

The script embeds tiny GenBank, GFF, BED/cytoband, and Newick inputs, sets the
`Agg` backend before importing pyplot, exercises parsing, GC, feature plotting,
cytoband tracks, TreeViz styling/confidence, and writes a PNG. It does not read
from a checkout, call a URL, install dependencies, or overwrite an existing
output path.
