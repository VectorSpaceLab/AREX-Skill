---
name: sequential
description: "Route SDV PAR sequential synthesis workflows for sequence-keyed data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SDV sequential synthesis router

Use this sub-skill when the task is about SDV time series or sequential data where multiple rows belong to a sequence identified by a sequence key. The main owned model is `PARSynthesizer`.

## Route here for

- Natural requests such as "PARSynthesizer", "sequence key", "sequence index", "context columns", "time series SDV", `sample_sequential_columns`, or `get_random_sequence_subset`.
- Building one-table sequential metadata that declares a sequence key and, optionally, a datetime or numerical sequence index.
- Fitting PAR, sampling whole new sequences, or generating sequential columns for known context rows.
- Reducing a long sequential table before fitting while preserving sequence membership.
- PAR-specific save/load, transformer updates, constraint compatibility, and `cuda` behavior.

## Route elsewhere

- Ordinary non-sequential single-table modeling: use the single-table sub-skill.
- Metadata primitives, local I/O, generic metadata validation, visualization, and broad data cleaning: use the data-preparation sub-skill.
- Constraint class design and programmable constraint internals: use the constraints sub-skill, then return here to attach compatible constraints to PAR.
- Quality metrics, diagnostics, or plots comparing real and synthetic data: use the evaluation sub-skill.

## Operating path

1. Confirm the data is a single sequential table, not just a flat table with a timestamp. A valid PAR workflow needs a sequence key column whose values group rows into independent sequences.
2. Build or inspect metadata with `sequence_key`; add `sequence_index` only when row order/timing matters and the column is datetime or numerical.
3. Identify `context_columns`: columns that remain constant within each sequence. Never include the sequence key itself as a context column.
4. Validate that each context column has exactly one value per sequence key before fitting; if not, fix the data or remove that context column.
5. Instantiate `PARSynthesizer` with a small `epochs` value for quick smoke work and a larger value for production modeling. Set `cuda=False` when deterministic CPU-only behavior matters or CUDA/torch availability is uncertain.
6. Use `sample(num_sequences, sequence_length=None)` for new sequence contexts. Use `sample_sequential_columns(context_columns, sequence_length=None)` only when the synthesizer was created with context columns and the caller supplies one context row per desired sequence.
7. For long data, call `get_random_sequence_subset` before fitting; verify the resulting sequence count and per-sequence lengths before handing the subset to PAR.
8. Attach constraints before `fit` and only when every constraint covers either context columns only or non-context sequential columns only; overlapping constraints on the same columns are not supported.
9. Save/load with PAR's inherited `save` and `load` methods after checking whether the target runtime has compatible torch/CUDA support.

## References

- [API reference](references/api-reference.md): PAR constructor, methods, metadata helpers, and sequence-subset utility signatures.
- [Workflows](references/workflows.md): sequence metadata setup, fit/sample, known-context generation, long-sequence subsetting, constraints, and save/load recipes.
- [Troubleshooting](references/troubleshooting.md): sequence-specific errors and fixes.
