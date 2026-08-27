# Chemprop Troubleshooting

Use this root troubleshooting guide for cross-cutting issues. For workflow-specific failures, use the nearest sub-skill troubleshooting reference.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'chemprop'`.
- `ImportError` from `rdkit`, `torch`, `lightning`, `numpy`, or `pandas`.
- `chemprop: command not found`.

Likely fixes:

1. Use Python `>=3.11,<3.15`.
2. Install Chemprop in the active environment, then run `python -c "import chemprop"` and `chemprop --help`.
3. Verify core dependencies with `python -m pip check`.
4. Install optional extras only for selected workflows: hpopt for Ray Tune, cuik-molmaker for accelerated featurization, notebook/docs extras for notebooks/docs.
5. If the CLI command is missing but import works, check whether the environment's script directory is on `PATH` or call `python -m chemprop.cli.main` only if appropriate for the environment.

## Backend Or Runtime Device Problems

Symptoms:

- PyTorch reports CUDA unavailable.
- Lightning rejects `--accelerator` or `--devices`.
- A checkpoint trained on GPU is loaded on a CPU-only machine.

Likely fixes:

- Use `--accelerator cpu` for deterministic smoke tests.
- Keep `--devices` as the string format expected by Lightning, especially for multi-device selections.
- Do not assume GPU availability from the presence of model files; Chemprop can inspect and run many workflows on CPU.
- For GPU training, match the installed PyTorch build to the system driver/runtime stack before blaming Chemprop flags.

## CLI Argument Conflicts

Symptoms:

- Parser errors before training or prediction starts.
- Config values appear ignored.
- `-k` or `--num-folds` fails.

Likely fixes:

- Command-line flags override `--config-path` values.
- `-k`/`--num-folds` was removed; use `--num-replicates`.
- `--class-balance` is for binary classification, not regression or multiclass.
- `--freeze-encoder` requires a compatible checkpoint.
- `--checkpoint` and foundation initialization workflows should not be mixed unless the target sub-skill explicitly supports the combination.

## Data And Feature Shape Problems

Symptoms:

- Missing target columns, SMILES columns, or reaction columns.
- NPZ descriptor/features row-count mismatch.
- Invalid reaction or atom/bond target parsing.

Likely fixes:

- Validate CSV and NPZ shape with `sub-skills/data-featurization/scripts/validate_chemprop_tabular_inputs.py`.
- Use explicit `--smiles-columns`, `--reaction-columns`, `--target-columns`, or `--mol-target-columns`/`--atom-target-columns`/`--bond-target-columns`.
- Ensure each descriptor/feature NPZ aligns row-for-row with the CSV or component CSV.
- Use `--reorder-atoms` only when atom maps define the intended atom target order.

## Optional Workflow Missing Dependencies

Symptoms:

- `chemprop hpopt` fails importing Ray Tune, hyperopt, optuna, or pydantic.
- `--use-cuikmolmaker-featurization` fails.
- Notebook examples require plotting or notebook kernels.

Likely fixes:

- Install the hpopt extra only when running `chemprop hpopt`.
- Install the cuik-molmaker extra only when the workflow and platform support it.
- Treat notebooks as examples, not required runtime dependencies for normal CLI/API usage.

## Routing To Deeper Help

- Training command and output issues: `sub-skills/training-cli/references/troubleshooting.md`.
- Prediction/fingerprint/model file issues: `sub-skills/prediction-fingerprints/references/troubleshooting.md`.
- CSV/NPZ/featurizer issues: `sub-skills/data-featurization/references/troubleshooting.md`.
- Python API construction issues: `sub-skills/python-api-modeling/references/troubleshooting.md`.
- Reaction/MolAtomBond/special task issues: `sub-skills/specialized-molecular-tasks/references/troubleshooting.md`.
- Uncertainty/hpopt/conversion issues: `sub-skills/uncertainty-advanced/references/troubleshooting.md`.
