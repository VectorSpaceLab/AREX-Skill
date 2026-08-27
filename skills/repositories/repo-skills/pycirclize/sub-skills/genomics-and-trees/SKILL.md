---
name: genomics-and-trees
description: "Guide pyCirclize biological circular plots from local GenBank,
  GFF, BED/cytoband, and Newick or Bio.Phylo inputs, including sequence
  features, GC summaries, and TreeViz annotation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Genomics and trees

Use this route when the task is to turn biological coordinates or a phylogenetic
tree into a pyCirclize circular plot. Prefer local files, file-like objects,
or in-memory Biopython objects. Keep the input parser, coordinate convention,
sequence-id mapping, and plot track aligned before rendering.

## Route by input

- **GenBank:** use `pycirclize.parser.Genbank` for sequences plus qualified
  `SeqFeature` objects. Use `get_seqid2size()` to create `Circos` sectors and
  `get_seqid2features()` or `extract_features()` for feature tracks.
- **GFF:** use `pycirclize.parser.Gff`. Select `target_seqid` for a one-seqid
  view, or use `get_seqid2features()` to retain a mapping for all seqids.
- **BED or cytoband:** use `Circos.initialize_from_bed()` for chromosome
  sectors. Then call `add_cytoband_tracks()` with a local UCSC-style BED-like
  cytoband file. Use `data-parsers` for generic tables and
  `circular-composition` for lifecycle/composition questions.
- **Newick/Bio.Phylo:** use `Circos.initialize_from_tree()` or attach
  `track.tree()` to an existing sector. The returned `TreeViz` owns node
  styling, highlights, markers, and confidence labels.

For generic `Track` drawing, `Sector`/`Track` radius conventions, and ordinary
annotations, link to `plot-primitives`. For matrix/table preparation, link to
`data-parsers`. For figure creation, shared axes, links, and final export,
link to `circular-composition`.

## Safe operating sequence

1. Identify whether coordinates are 0-based half-open (BED) or 1-based closed
   (GFF); GenBank becomes Biopython 0-based feature locations.
2. Parse locally and inspect names, `seqid_list`, `records`, and
   `get_seqid2size()` before constructing sectors.
3. Construct sectors from the same identifiers and lengths used by the feature
   mapping. Check strand and qualifier availability before styling.
4. Add dedicated tracks for forward/reverse features, GC content/skew, or
   cytobands. Keep all plotted x coordinates inside their sector range.
5. For trees, inspect `tv.leaf_labels`, `tv.innode_labels`, and
   `tv.all_node_labels` before querying nodes. Apply styling before
   `plotfig()`/`savefig()`.
6. Render with Matplotlib's `Agg` backend for batch work and verify a non-empty
   output file. Use the bundled deterministic smoke test for a minimal check:
   [`scripts/genomics_tree_smoke.py`](scripts/genomics_tree_smoke.py).

## Data-source boundary

`load_example_tree_file()` and `load_example_image_file()` resolve packaged
local example data. `load_prokaryote_example_file()`,
`load_eukaryote_example_dataset()`, and `fetch_genbank_by_accid()` are
network-backed helpers that may download and cache data; never call them
implicitly. Ask for an explicit dataset/cache policy, or replace them with
user-provided local files. The optional `ipympl` tooltip extra is not required
for static plots or PNG export.

Detailed signatures, coordinate rules, parser properties, and TreeViz methods
are in [api-reference.md](references/api-reference.md). Input conventions and
local/network boundaries are in [data-formats.md](references/data-formats.md).
Runnable recipes are in [workflows.md](references/workflows.md), and recovery
for malformed or mismatched biological data is in
[troubleshooting.md](references/troubleshooting.md).
