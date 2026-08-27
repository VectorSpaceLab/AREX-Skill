---
name: constraints
description: "Route SDV constraint design, serialization, loading, and debugging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SDV constraints

Use this sub-skill when the task is about adding or debugging SDV logical constraints: built-in CAG constraints, legacy tabular constraints, custom constraint factories, programmable constraints, constraints JSON files, or synthesizer constraint methods.

## Route here for

- Natural requests such as "add SDV constraints", "custom constraint", "programmable constraint", "load constraints JSON", `FixedCombinations`, `Inequality`, or "constraint validation error".
- Choosing between current `sdv.cag` constraints and legacy `sdv.constraints` tabular constraints.
- Creating, saving, loading, and attaching constraints with `add_constraints`, `get_constraints`, `set_constraints`, and `load_constraints`.
- Diagnosing constraint metadata, data-shape, sdtype, table-name, serialization, and custom-function failures.

## Do not own

- Metadata table and column creation: route those decisions to the data-preparation sub-skill.
- Synthesizer model selection, fitting, sampling, conditions, or save/load model lifecycle: route to the single-table, multi-table, or sequential synthesis sub-skills after constraints are attached.
- Quality metrics or visual evaluation of constrained synthetic output: route to the evaluation sub-skill.

## Operating path

1. Confirm the metadata already has the target table and columns. For multi-table metadata, supply `table_name` on every one-table CAG constraint.
2. Prefer current `sdv.cag` objects for `synthesizer.add_constraints([...])`; use legacy `sdv.constraints` only for old tabular/data-processor workflows or when translating existing legacy constraint definitions.
3. Add constraints before `fit` when possible. If constraints are added after fitting, refit the synthesizer before relying on them.
4. For custom logic, use `create_custom_constraint_class` only when the legacy tabular interface is required; otherwise prefer a `ProgrammableConstraint` subclass.
5. For JSON round-trips, use the current CAG dictionary shape and `sdv.utils.load_constraints`, then compare the number of loaded constraints with the file entries because unknown classes are warned and skipped.
6. When an error names a column, sdtype, `table_name`, row index, or `is_valid` return type, jump directly to [troubleshooting](references/troubleshooting.md).

## References

- [API reference](references/api-reference.md): constructors, current-vs-legacy distinction, JSON shapes, and synthesizer methods.
- [Workflows](references/workflows.md): concise recipes for built-ins, custom classes, programmable classes, JSON load/save, and refitting.
- [Troubleshooting](references/troubleshooting.md): symptom-to-fix table for common constraint failures.
