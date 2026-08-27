---
name: multi-table
description: "Route SDV relational and multi-table synthesis workflows with HMA and DayZ."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SDV multi-table synthesis router

Use this sub-skill when the task is to model connected tables, preserve primary/foreign-key relationships, sample a relational synthetic dataset, or debug `HMASynthesizer` and multi-table `DayZSynthesizer` workflows.

## Route here for

- Natural requests such as "multi-table SDV", "relational synthetic data", "HMA", "foreign keys", "sample scale", "drop unknown references", or multi-table DayZ parameters.
- Building on already prepared multi-table `Metadata` and `dict[str, pandas.DataFrame]` data.
- `HMASynthesizer(metadata, locales=['en_US'], verbose=True)` fit/sample/save/load and table-parameter customization.
- Multi-table `DayZSynthesizer.create_parameters` / `validate_parameters` and synthetic data from DayZ parameter dictionaries when the runtime supports it.
- Relationship-aware constraints, transformer inspection, referential-integrity cleanup, and sampling repeatability.

## Route elsewhere

- Loading CSV/demo data, detecting metadata, and fixing basic table/column metadata: use the data-preparation sub-skill first.
- Single DataFrame synthesis with GaussianCopula/CTGAN/TVAE/CopulaGAN: use the single-table sub-skill.
- One-table sequence modeling with a sequence key: use the sequential sub-skill.
- Constraint class internals or JSON design: use the constraints sub-skill, then return here to attach compatible constraints.
- Quality reports, diagnostics, and comparison plots: use the evaluation sub-skill.

## Operating path

1. Confirm `data` is a dictionary mapping table names to pandas DataFrames and that `metadata` has one table entry per DataFrame.
2. Validate metadata first, then validate data. Fix primary keys, foreign keys, composite keys, and relationship sdtypes before fitting.
3. Use `drop_unknown_references` only after deciding that rows with invalid child foreign keys may be removed.
4. Prefer `HMASynthesizer` for community relational modeling. Use multi-table DayZ parameter helpers when the task asks for DayZ-style parameter dictionaries or an enterprise runtime owns actual DayZ generation.
5. Attach constraints before `fit`; per-table constraints in multi-table metadata usually need explicit `table_name`.
6. Use `sample(scale=...)` to generate proportional table sizes; use `reset_sampling()` when a repeatable sequence of samples is required after fit.
7. Save/load the fitted synthesizer with the same class that created it, and verify the target runtime has compatible dependencies before sampling.

## References

- [API reference](references/api-reference.md) for constructors, methods, relationship metadata, and utility signatures.
- [Workflows](references/workflows.md) for two-table setup, HMA fit/sample, referential cleanup, constraints, and DayZ parameter recipes.
- [Troubleshooting](references/troubleshooting.md) for relationship, foreign-key, scale, and serialization failures.
