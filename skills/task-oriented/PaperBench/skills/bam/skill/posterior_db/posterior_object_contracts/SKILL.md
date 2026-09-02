---
name: posterior_object_contracts
description: Validate and normalize posteriordb posterior, model, data, and reference object contracts for benchmarking workflows.
---

# Posterior Object Contracts

Use this skill when a recovery or benchmark task needs to inspect a posteriordb-style database snapshot and verify that a named posterior has valid links to model, data, dimensions, and reference posterior metadata. Do not use it to run Stan code or infer posterior samples.

## Inputs

- `database_root`: directory containing `posteriors/`, `models/info/`, `data/info/`, and optionally `reference_posteriors/info/`.
- `posterior_name`: posterior JSON basename, for example `eight_schools-eight_schools_centered`.

## Outputs

- A normalized contract JSON with posterior name, model name, data name, reference posterior name, dimensions, total dimension, existing linked paths, and errors.
- A nonzero CLI exit only for invalid CLI usage; ordinary contract problems are returned as `valid: false`.

## Workflow

1. Load `posteriors/<posterior_name>.json` from the supplied snapshot.
2. Accept common posteriordb keys such as `model_name`, `data_name`, `reference_posterior_name`, `dimensions`, and `dimension`.
3. Resolve linked metadata paths under `models/info/`, `data/info/`, and `reference_posteriors/info/` without reading implementation code.
4. Compute `total_dimension` from numeric dimension entries and collect missing-link errors.
5. Return a JSON report that downstream recovery can log as object-linking evidence.

## Validation

Run `python scripts/posterior_contracts.py --database-root <root> --posterior <name> --output contract.json` or `python tests/test_posterior_contracts.py` through the Distiller skill validator.

## Limitations

The script validates file contracts and metadata links only. It does not guarantee that model code compiles, reference draws are high quality, or all posteriordb schemas use exactly the same optional fields.
