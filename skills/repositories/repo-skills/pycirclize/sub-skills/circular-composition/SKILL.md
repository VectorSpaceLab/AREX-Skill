---
name: circular-composition
description: "Compose and export general pyCirclize circular layouts with Circos
  sectors, global primitives, links, custom polar axes, and Matplotlib figure
  lifecycle."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Circular composition

Use this route when the task is to build a general Circos layout from sector
sizes or coordinate ranges, add composition-level annotations or links, and
render/export a Matplotlib figure. This route is for pyCirclize **1.10.1** on
Python **>=3.10** with the base dependencies (`biopython`, `matplotlib`,
`numpy`, `pandas`). Tooltip interaction is optional (`pycirclize[tooltip]`,
`ipympl`) and is not required for static output.

## Route first

- Use [`plot-primitives`](../plot-primitives/SKILL.md) for `Sector.add_track`
and every track-local drawing/data method.
- Use [`data-parsers`](../data-parsers/SKILL.md) for matrix/table input,
`Circos.chord_diagram`, and `Circos.radar_chart`.
- Use [`genomics-and-trees`](../genomics-and-trees/SKILL.md) for BED/GenBank/GFF
initialization, cytobands, biological features, and phylogenetic trees.
- Use the [pyCirclize root route](../../SKILL.md) for installation, shared
provenance, environment checks, and cross-workflow decisions.

## Operating procedure

1. Normalize each sector as `name -> size` or `name -> (start, end)` and choose
the global degree interval, inter-sector spaces, optional final space, and
per-sector direction before adding any coordinates.
2. Construct `Circos`, inspect `circos.deg_lim`, `circos.sectors`, and each
sector's `start`, `end`, `size`, `deg_lim`, and `clockwise`; use
`get_sector()` rather than indexing by an assumed order.
3. Add composition-level `axis`, `text`, `line`, `rect`, `link`, `link_line`,
or `colorbar` calls. Keep x/degree coordinates in the declared sector ranges;
track data belongs to the plot-primitives route.
4. Render with `plotfig()` when a caller needs the returned Figure, a custom
`matplotlib.projections.polar.PolarAxes`, a legend, subplots, or other
post-render Matplotlib edits. Add legends through `circos.ax` only after
`plotfig()` returns, then save the returned Figure.
5. Use `savefig()` for a self-contained static export when no post-render
legend/subplot/annotation must be retained. Verify the output exists and has
the requested format.

## Contracts and checks

- `start`/`end` must satisfy `-360 <= start < end <= 360`, with span at most
360 degrees. A sequence `space` has one value per sector when `endspace=True`,
or one fewer when `endspace=False`; total spaces cannot consume the plot.
- Tuple sector ranges require `start < end`; their widths determine angular
allocation, while coordinates remain in each tuple's own range.
- `sector2clockwise` changes coordinate conversion for named sectors; it does
not change the order of sectors. Validate directed links in both directions
when mixing clockwise and anti-clockwise sectors.
- `circos.ax` is unavailable until `plotfig()` has initialized or accepted a
polar axis. `plotfig(ax=...)` rejects a non-polar Matplotlib axis.
- Run the bundled [deterministic composition smoke](scripts/circos_smoke.py)
with an explicit output path. It exercises invalid configuration recovery,
nonuniform spaces, tuple ranges, directed links, global primitives, the
`savefig()` lifecycle, custom `PolarAxes`, legend insertion, and PNG export.

For signatures, coordinate conventions, lifecycle details, and recovery, use:

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
