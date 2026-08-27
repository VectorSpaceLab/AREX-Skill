---
name: single-table
description: "Use SDV single-table synthesizers to fit, sample, conditionally
  sample, customize, save/load, and inspect GaussianCopula, CTGAN, TVAE,
  CopulaGAN, DayZ parameters, and legacy SingleTablePreset."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SDV Single-Table Synthesis Router

Use this sub-skill when the task is to fit a single-table synthesizer, sample rows, conditionally sample rows, complete missing columns from known values, save/load a fitted model, inspect learned distributions or loss values, or choose among SDV single-table models.

## Route Here For

- `GaussianCopulaSynthesizer`, `CTGANSynthesizer`, `TVAESynthesizer`, `CopulaGANSynthesizer`.
- Public `DayZSynthesizer.create_parameters` / `validate_parameters` for single-table DayZ parameter files.
- Legacy `sdv.lite.SingleTablePreset`, especially `FAST_ML` migration to GaussianCopula.
- Common synthesizer methods: `fit`, `preprocess`, `fit_processed_data`, `sample`, `sample_from_conditions`, `sample_remaining_columns`, `save`, `load`, `get_info`, `get_parameters`, `get_metadata`.
- Synthesizer-level constraints, transformer assignment, deep-model `enable_gpu`, CTGAN/TVAE loss values, GaussianCopula/CopulaGAN learned distributions.

## Route Elsewhere

- Metadata detection, column sdtype editing, demo data, local CSV/Excel loading, or metadata visualization: use the data-preparation sub-skill.
- Constraint class design, programmable constraint internals, and custom constraint factories: use the constraints sub-skill; return here to attach constraints to a synthesizer.
- Quality reports and synthetic-vs-real plots: use the evaluation sub-skill.
- Relational/multi-table or sequential/time-series synthesis: use the multi-table or sequential sub-skill.

## Read Order

1. For model choice, signatures, public methods, and persistence details, read [references/api-reference.md](references/api-reference.md).
2. For task recipes, read [references/workflows.md](references/workflows.md).
3. If sampling, fitting, GPU, constraints, or DayZ parameters fail, read [references/troubleshooting.md](references/troubleshooting.md).

## Operating Assumptions

- `real_data` is a pandas `DataFrame` and `metadata` is an SDV `Metadata` object that describes exactly one table. If either is missing or invalid, prepare it before selecting a model.
- Prefer the modern unified `Metadata` class. `SingleTableMetadata` and `SingleTablePreset` remain usable but emit deprecation warnings.
- Keep synthetic generation code self-contained: do not depend on source checkout examples or test fixtures.
