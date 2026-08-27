---
name: plot-primitives
description: "Guide pyCirclize 1.10.1 Sector and Track plotting primitives,
  coordinate conversion, radial scaling, annotations, and deterministic
  Matplotlib export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Plot primitives

Use this skill when an existing `Circos` object needs sector-local or
track-local drawing. Treat `Sector` and `Track` as the plotting surface: user
coordinates are converted into polar radians and normalized radii when the
plot is built, while ordinary Matplotlib style keyword arguments remain the
main styling interface.

## Route the request

- Read [api-reference.md](references/api-reference.md) for signatures,
  coordinate rules, normalization, and method families.
- Read [workflows.md](references/workflows.md) for the recommended build
  order, mixed primitive recipes, export, and validation patterns.
- Read [troubleshooting.md](references/troubleshooting.md) before changing data
  ranges, annotations, or image inputs.
- Run the bundled [plot_primitives_smoke.py](scripts/plot_primitives_smoke.py)
  only with a caller-provided output path when a small Agg rendering check is
  useful. It uses in-memory deterministic data and refuses to overwrite an
  existing file.

Route instead of duplicating adjacent workflows:

- `Circos` construction, global sector composition, global links, legends,
  colorbars, axes, and figure lifecycle -> `../circular-composition/SKILL.md`.
- Matrix/radar preparation and high-level chart factories ->
  `../data-parsers/SKILL.md`.
- Tree interpretation, GenBank/GFF/BED semantics, and feature-derived
  coordinates -> `../genomics-and-trees/SKILL.md`. This skill only records the
  primitive call used after those semantics have been resolved.

## Operating contract

1. Start with a valid sector and add a non-degenerate track, usually with a
   radius range such as `(70, 100)` and an explicit `r_pad_ratio` when data
   should not touch the track boundary.
2. Keep x values in the sector's own coordinate range. Use `x_to_rad()` only
   for inspection or custom integrations; primitive methods accept x, not
   radians. Keep y/value data separate and map it with `vmin`/`vmax`.
3. Choose a primitive family, pass its Matplotlib-compatible style kwargs,
   render through the parent `Circos`, and assert the requested output exists.
4. Diagnose invalid x, y, radius, width, length, image, or annotation inputs
   from [troubleshooting.md](references/troubleshooting.md) rather than
   bypassing validation with `ignore_range_error` indiscriminately.

This sub-skill is self-contained for package use and does not require the
source checkout, notebooks, test fixtures, or a network connection at runtime.
