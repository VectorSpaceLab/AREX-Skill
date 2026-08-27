---
name: genotypes-and-visualization
description: "Inspect DARTS CNN/RNN genotype schemas, interpret search outputs,
  and emit safe DOT graphs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Genotypes and Visualization

Use this sub-skill when the task is about DARTS genotype definitions, search-output interpretation, schema differences, or DOT-only visualization.

Start here:

- [references/genotype-reference.md](references/genotype-reference.md) for the CNN and RNN genotype schemas, built-ins, primitive lists, and validation rules.
- [references/visualization.md](references/visualization.md) for how the CNN normal/reduction cells and RNN recurrent cell are turned into graphs.
- [references/troubleshooting.md](references/troubleshooting.md) for invalid names, operation mismatches, index mistakes, missing Graphviz, and CNN/RNN schema mixups.
- [scripts/darts_genotype_tools.py](scripts/darts_genotype_tools.py) for `list`, `show`, and `dot` inspection with DOT emission only.

Operating rules:

1. Keep CNN and RNN genotype schemas separate. `DARTS` is overloaded across the two families, so qualify the schema when the name alone is ambiguous.
2. Use the bundled helper to inspect, validate, and emit DOT. It never renders through Graphviz by default.
3. Treat search outputs as discrete genotype tuples: CNN search selects two non-`none` incoming edges per intermediate node; RNN search selects one predecessor and one non-`none` op per step.
4. Route training, evaluation, and long-running architecture-search commands to the sibling workflow sub-skills.
5. Do not depend on the original checkout at runtime; this subtree must stay self-contained.
