---
name: pycirclize
description: "Use pyCirclize 1.10.1 for circular visualization, Circos plots,
  chord and radar charts, genomic feature plots, phylogenetic trees,
  parser-driven layouts, and deterministic Matplotlib export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pyCirclize

Use this skill when a task asks to create or debug circular figures in Python
with pyCirclize: Circos sectors, radial tracks, links, chord/radar charts,
genomics/cytoband plots, phylogenetic trees, or figure export. It targets
pyCirclize 1.10.1 on Python >=3.10 with `biopython`, `matplotlib`, `numpy`, and
`pandas`.

## Install and smoke-check

```bash
python -m pip install pycirclize
python -c "import pycirclize; print(pycirclize.__version__)"
```

For interactive Jupyter tooltips only, install `pycirclize[tooltip]` (or
`ipympl`) and use a live widget kernel. Static PNG/SVG/PDF rendering does not
need that extra. For headless work select Matplotlib's `Agg` backend before
importing pyplot.

For a safe package/import/export check, read and run
[`scripts/check_environment.py`](scripts/check_environment.py). It does not
download data or overwrite an existing output.

## Route by task

- **General Circos layout, sectors, global links, composition, legends, and
  export:** read [`circular-composition`](sub-skills/circular-composition/SKILL.md).
- **Sector/track drawing, annotations, ticks, bars, heatmaps, images, and
  numeric data:** read [`plot-primitives`](sub-skills/plot-primitives/SKILL.md).
- **Matrix/table/from-to/BED preparation, chord diagrams, radar charts, and
  stacked-bar helpers:** read [`data-parsers`](sub-skills/data-parsers/SKILL.md).
- **GenBank, GFF, BED/cytoband, genomic features, Newick trees, and TreeViz
  styling:** read [`genomics-and-trees`](sub-skills/genomics-and-trees/SKILL.md).

Read the shared [troubleshooting guide](references/troubleshooting.md) when an
import, optional dependency, input schema, coordinate, or output problem is
not clearly owned by one route. Read
[repository provenance](references/repo-provenance.md) before deciding whether
this graph is stale for a changed checkout.

## Cross-route operating rules

1. Normalize the input first: sector sizes/ranges, table labels and delimiter,
   biological coordinate convention and sequence IDs, or tree format.
2. Keep the object hierarchy explicit: `Circos` owns sectors; `Sector` owns
   tracks; `Track` owns most data primitives. High-level factories create the
   appropriate hierarchy for matrix/radar/tree inputs.
3. Render only after all patches and plot callbacks are registered. Use
   `Circos.savefig(path)` for a self-contained static export. Use
   `fig = circos.plotfig()` and then `fig.savefig(...)` when a caller must add
   legends, subplots, or other Matplotlib objects after rendering.
4. Validate every x coordinate against its sector range and every feature/tree
   identifier against the parsed mapping. Do not silently download example
   datasets: network-backed helpers require an explicit data/cache decision.
5. Verify output existence and non-zero size in automated workflows. Treat
   interactive tooltip support as optional and separate from static rendering.

## Scope boundary

This is a user-facing package skill, not a maintainer guide. It does not
require the original checkout, notebooks, tests, caches, or generated images at
runtime. The bundled references and smoke helpers contain the reusable facts
needed for future tasks.
