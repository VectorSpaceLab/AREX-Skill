---
name: objects-interface
description: "Use seaborn.objects for declarative Plot composition with marks,
  stats, moves, scales, layering, faceting, and output handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Objects Interface

Use this sub-skill when a task mentions `seaborn.objects`, `so.Plot`, marks, stats, moves, scales, declarative layering, or grammar-like plot construction.

## Route Here For

- Building a `so.Plot(data, x=..., y=..., color=...)` and adding layers with `.add(mark, stat, move, ...)`.
- Choosing mark classes such as `Dot`, `Line`, `Bar`, `Area`, `Band`, `Text`, `Range`, `Dash`, `Path`, or their plural variants.
- Choosing stat classes such as `Agg`, `Est`, `Count`, `Hist`, `KDE`, `Perc`, and `PolyFit`.
- Using move classes `Dodge`, `Jitter`, `Norm`, `Shift`, and `Stack` to adjust layer positions.
- Applying `Continuous`, `Nominal`, `Temporal`, or `Boolean` scales and setting labels, limits, layout, pair/facet specs, and themes.
- Rendering with `.plot()`, `.show()`, or `.save(...)`, or directing output to a matplotlib axes/figure with `.on(...)`.

## Use Another Sub-skill For

- Classic `sns.*plot` functions: `../function-interface/SKILL.md`.
- `FacetGrid`, `PairGrid`, `JointGrid`, `pairplot`, or `jointplot`: `../figure-grids/SKILL.md`.
- Palette/theme constructors used outside `Plot.theme`: `../themes-palettes/SKILL.md`.
- Long/wide-form data validation: `../data-utilities/SKILL.md`.

## Start With

1. Decide whether the request benefits from declarative layering; if a single high-level function is enough, route to `function-interface`.
2. Build `so.Plot` with shared data and variable mappings.
3. Add one layer at a time with a mark and optional stat/move objects.
4. Use `.facet()` or `.pair()` for small multiples and `.scale()` for property/value mapping rules.
5. Render explicitly with `.plot()`, `.save(path)`, or `.show()`.

## References

- Object taxonomy and key method signatures: `references/api-reference.md`.
- Layering/faceting recipes: `references/workflows.md`.
- Failure recovery: `references/troubleshooting.md`.
- Shared package API map: `../../references/api-summary.md`.

## Quick Smoke Check

```bash
python sub-skills/objects-interface/scripts/objects_smoke.py --output objects_smoke.png
```

The helper uses synthetic data, the Agg backend, and no network access.
