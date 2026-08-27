---
name: data-pipeline
description: "Prepare, validate, preprocess, filter, standardize, and
  deduplicate SMILES datasets with REINVENT4 reinvent_datapre."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Pipeline

Use this sub-skill when a task mentions `data_pipeline.toml`, `reinvent_datapre`, SMILES preprocessing, CSV-to-SMI conversion, token filtering, allowed elements, RDKit standardization, `transform_file`, deduplication, or cleaning a dataset before sampling, scoring, transfer learning, staged learning, or enumeration.

## Read First

- `references/data-formats.md` for accepted input files, required config keys, CLI invocation, output files, and helper usage.
- `references/preprocessing-workflow.md` for a safe build-validate-run-scale workflow and what each regex/RDKit filter does.
- `references/troubleshooting.md` for invalid SMILES, unexpected elements, bad delimiters/headers, transform-file mistakes, output writes, multiprocessing, and dependency triage.
- `scripts/validate_data_pipeline_config.py` to parse a TOML config, verify input/output fields and filter structure, and sample-check the selected SMILES column without running `reinvent_datapre`.
- `scripts/make_tiny_smiles_fixture.py` to generate a small CSV/SMI fixture plus matching `data_pipeline.toml` for smoke checks.

## Fast Path

1. Create a TOML config with `input_csv_file`, `smiles_column`, `separator`, `output_smiles_file`, `num_procs`, `chunk_size`, and a `[filter]` table.
2. Use a headered CSV/TSV for tabular data, or `.smi`/`.smi.gz` for headerless SMILES input. For `.smi`, `smiles_column` names the synthetic column used internally.
3. Validate before preprocessing:
   ```bash
   python sub-skills/data-pipeline/scripts/validate_data_pipeline_config.py data_pipeline.toml --sample-rows 20
   ```
4. Run a small preprocessing smoke check:
   ```bash
   reinvent_datapre data_pipeline.toml --log-filename data_pipeline.log
   ```
5. Inspect `output_smiles_file`, the log, and the side-effect `regex.smi` in the working directory before scaling to a large dataset.

## Scope Boundaries

- This sub-skill owns `reinvent_datapre`, `data_pipeline.toml`, CSV/SMI inputs, `smiles_column`, `separator`, regex token filtering, allowed elements, RDKit cleanup, standardization transforms, deduplication, output `.smi`, and tiny-fixture validation.
- For molecule generation after preprocessing, use the `sampling` sub-skill.
- For scoring preprocessed molecules, use the `scoring` sub-skill.
- For transfer learning or staged reinforcement learning on cleaned data, use the `learning` sub-skill.
- For peptide or molecule enumeration, use the `enumeration` sub-skill.
