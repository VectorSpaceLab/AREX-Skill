# Recipe training troubleshooting

## `!PLACEHOLDER` or override errors

- Pass the hparams file first, then overrides.
- Use exact override names from the YAML.
- Use the tested flag spelling from `tests/recipes/*.csv` when available.
- Print the generated `hyperparams.yaml` in the output folder to confirm overrides were applied.

## Data preparation failures

- Confirm raw data paths and write permissions.
- Decide whether network downloads are allowed before running preparation scripts.
- Use `--skip_prep=True` with prebuilt CSV/JSON manifests or tiny fixtures.
- In DDP, wrap one-time data preparation in `run_on_main` so all ranks do not write the same files.

## Missing optional dependencies

- Locate the nearest `extra_requirements.txt` for the selected recipe family.
- Install only that file; do not install every recipe extra.
- Some extras need external system dependencies or compiled packages. Record them before retrying.
- If the missing import belongs to Hugging Face integration, `transformers` is usually the key optional dependency.

## Training is too slow

- Use `--debug`, `--debug_batches`, `--debug_epochs`, or recipe CSV debug flags.
- Reduce model dimensions only when the recipe exposes such hparams.
- Use CPU for syntax/data-flow checks and CUDA for performance-sensitive verification.
- Separate data preparation time from model training time.

## Output files are missing

- Check `output_folder` after overrides.
- Confirm `create_experiment_directory` is called before training.
- Compare expected files against the selected recipe CSV `test_debug_checks` rather than guessing.
- If `test_only` is set, some training checkpoint files may not be produced.

## CUDA/DDP failures

- Confirm Torch/Torchaudio backend match and `torch.cuda.is_available()`.
- Run a single-GPU command before `torchrun`.
- In DDP, check per-process batch size, local rank, and data path visibility.
- Prefer `torchrun`; do not start new work with deprecated DataParallel patterns.

## Performance checks fail on tiny data

- Recipe CSV performance checks are calibrated to the listed debug flags and fixtures. If you change epochs, model size, or data, expected thresholds may no longer apply.
- File-existence checks are a better first smoke test than numeric metrics.
- Do not use a tiny fixture metric as evidence of production model quality.
