# SaProt Cross-Cutting Troubleshooting

## Import Failures

Symptoms:

- `ModuleNotFoundError` for `torch`, `transformers`, `pytorch_lightning`, `torchmetrics`, `easydict`, `Bio`, `lmdb`, `pandas`, or `esm`.
- Repository modules import only when run from a specific project root.

Fix:

- Use an isolated Python 3.10 environment for full repository execution.
- Install only helper-specific dependencies for static validation tasks.
- Add the active SaProt project root to `PYTHONPATH` or run launchers from the project root when using repository modules.
- For model inference, check local assets with `sub-skills/model-inference/scripts/check_model_assets.py` before importing heavyweight classes.

## Missing Model Assets

Symptoms:

- Hugging Face loaders fail on a path.
- `.pt` checkpoint loading is attempted with a directory, or Hugging Face loading is attempted with a `.pt` file.
- Empty or placeholder model directories.

Fix:

- Use a local Hugging Face directory for `EsmTokenizer`, `EsmForMaskedLM`, `SaprotBaseModel`, `SaprotFoldseekMutationModel`, and `SaProtIFModel`.
- Use a local `.pt` checkpoint only with the ESM-style loader.
- Validate expected files with `sub-skills/model-inference/scripts/check_model_assets.py`.
- Do not assume weights are bundled with the repository or this skill.

## Missing Foldseek

Symptoms:

- Structure conversion fails before producing AA/3Di sequences.
- Zero-shot mutation configs point at a stale or absolute `foldseek_path`.

Fix:

- Install Foldseek or use the user-provided executable path.
- Validate it with `python scripts/check_sa_prot_environment.py --foldseek <foldseek>`.
- For structure conversion details, route to `sub-skills/structure-sequences/SKILL.md`.
- For config path cleanup, route to `sub-skills/datasets-configs/SKILL.md` and `sub-skills/training-evaluation/SKILL.md`.

## LMDB and Data Path Failures

Symptoms:

- Dataloader fails with missing `length` key.
- Dataset path exists but lacks `data.mdb` or `lock.mdb`.
- JSON rows are missing `seq`, `fitness`, `label`, `seq_1`, `seq_2`, `valid_mask`, or `tertiary`.

Fix:

- Validate schemas with `sub-skills/datasets-configs/scripts/jsonl_to_lmdb.py --dry-run`.
- Validate YAML paths with `sub-skills/datasets-configs/scripts/validate_config.py`.
- Use one LMDB directory per split and ensure `length` matches numeric keys.

## CUDA and Resource Mismatches

Symptoms:

- `Torch not compiled with CUDA enabled`.
- CUDA out-of-memory.
- `Trainer.devices` exceeds `CUDA_VISIBLE_DEVICES`.
- Large model inference is impractical on CPU.

Fix:

- Start with CPU-safe diagnostics.
- Validate visible GPUs and optional imports with `scripts/check_sa_prot_environment.py --check-cuda`.
- For smoke tests, use one GPU, fewer workers, smaller batches, and logger disabled.
- Do not hard-code CUDA in reusable snippets; use `torch.cuda.is_available()` when writing inference code.

## WandB and Secret Handling

Symptoms:

- Training tries to start WandB unexpectedly.
- Config contains placeholder or missing `WANDB_API_KEY`.
- Non-root distributed ranks log unexpectedly.

Fix:

- Set `Trainer.logger: false` for dry-runs and non-interactive checks.
- Provide WandB credentials only through private user environment variables.
- Keep `NODE_RANK: 0` for single-machine smoke tests; repository training code disables logging on non-root nodes.

## Stale Skill Signals

Run a refresh when the active SaProt checkout differs from `references/repo-provenance.md` in commit, dirty paths, package layout, public model/dataset classes, config shape, script behavior, or dependency pins. A changed README alone can also matter because many public SaProt workflows are documented there.
