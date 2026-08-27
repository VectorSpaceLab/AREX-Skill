# Protenix Cross-Cutting Troubleshooting

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError` for `protenix`, `runner`, `configs`, `Bio`, `rdkit`, `gemmi`, `torch`, `cuequivariance`, or `deepspeed`.
- `python -m pip check` reports dependency conflicts.
- The package imports from an unexpected environment.

Actions:

1. Verify Python 3.11 or newer and the intended `protenix` distribution.
2. Run `python -c "import protenix, runner.batch_inference; import importlib.metadata as md; print(md.version('protenix'))"`.
3. Run `python scripts/check_protenix_environment.py --json` from this skill for package/import/backend/tool status.
4. Reinstall the package only in the user's intended environment; do not mutate base/shared environments without confirmation.
5. If the user only needs command planning or JSON validation, use bundled no-import helpers before forcing a full runtime dependency repair.

## `protenix` Command Not Found

Symptoms:

- `protenix --help` fails but Python imports work.
- Shell cannot find the console script after install.

Actions:

1. Confirm the active environment's script directory is on `PATH`.
2. Check package metadata with `python -m pip show protenix` or `python -c "import importlib.metadata as md; print(md.entry_points(group='console_scripts'))"`.
3. Run `python scripts/check_protenix_environment.py --json` to distinguish metadata/import/CLI issues.
4. Use `sub-skills/cli-and-inference/SKILL.md` for command-shape and prediction-specific diagnosis.

## Checkpoints, Cache, Or `PROTENIX_ROOT_DIR`

Symptoms:

- Prediction tries to download checkpoint/cache files unexpectedly.
- Common chemistry/cache files are missing.
- Outputs, checkpoints, or caches appear under an unintended location.

Actions:

1. Set `PROTENIX_ROOT_DIR` deliberately before prediction, data preparation, or database-heavy workflows.
2. Keep checkpoints, common CCD/cache data, search databases, and training datasets under a stable data root.
3. Treat first-run downloads as side effects; ask before running them in constrained, offline, or shared environments.
4. Use `sub-skills/cli-and-inference/SKILL.md` for prediction cache/checkpoint routing and `sub-skills/training-and-data-pipeline/SKILL.md` for training data roots.

## CUDA, Kernel, Or Optional Backend Failures

Symptoms:

- Torch imports but CUDA is unavailable.
- cuEquivariance, Triton, DeepSpeed, CUTLASS, or fast layer norm import/JIT fails.
- Prediction errors mention kernel image, driver mismatch, ABI mismatch, or compilation.

Actions:

1. Run `scripts/check_protenix_environment.py --json` at the root and `sub-skills/advanced-model-configuration/scripts/protenix_runtime_doctor.py --json` for deeper backend detail.
2. Try safe fallbacks before editing code: `LAYERNORM_TYPE=torch`, `--trimul_kernel torch`, and `--triatt_kernel torch`.
3. Confirm torch wheel CUDA support, NVIDIA driver compatibility, GPU visibility, and whether optional extension wheels match the installed torch/CUDA ABI.
4. Use `sub-skills/advanced-model-configuration/SKILL.md` before changing configs, kernel choices, TFG settings, or model internals.

## System Tools And Databases Missing

Symptoms:

- `protenix mt` or `protenix prep` fails for missing `hmmsearch`, `hmmbuild`, `nhmmer`, `hmmalign`, `kalign`, MMseqs, or database paths.
- JSON path fields for `pairedMsaPath`, `unpairedMsaPath`, `templatesPath`, or RNA MSA files point to missing files.

Actions:

1. Route to `sub-skills/msa-template-and-prep/SKILL.md` before rerunning searches.
2. Validate existing paths and directory layout with `sub-skills/msa-template-and-prep/scripts/check_msa_template_layout.py`.
3. Treat database downloads and searches as network/storage/time-heavy unless local resources are confirmed.
4. Prefer repairing stale path fields or reusing valid precomputed files over rerunning expensive searches.

## Input JSON Rejected

Symptoms:

- Parser rejects entity keys, ligand/ion values, covalent bonds, constraints, or MSA/template fields.
- Model runs without expected MSA/template/RNA features.

Actions:

1. Route to `sub-skills/input-data-and-features/SKILL.md` and run `sub-skills/input-data-and-features/scripts/validate_protenix_input_json.py`.
2. Fix entity block names and `count`/`id` consistency first.
3. Use `CCD_` prefixes for ligand CCD values, not ions.
4. Confirm path fields are strings pointing to existing precomputed files before prediction.
5. Route missing path generation to `sub-skills/msa-template-and-prep/SKILL.md` instead of editing JSON blindly.

## Data Or Training Workflow Fails

Symptoms:

- Training cannot find `common`, `indices`, `mmcif`, `mmcif_bioassembly`, `mmcif_msa_template`, `rna_msa`, or `search_database`.
- Index CSV columns are missing.
- W&B, DDP/NCCL, checkpoint/EMA, CUDA OOM, or config override failures occur.

Actions:

1. Route to `sub-skills/training-and-data-pipeline/SKILL.md`.
2. Run `sub-skills/training-and-data-pipeline/scripts/check_training_data_layout.py` before proposing downloads, preprocessing, or `torchrun`.
3. Disable W&B by default in generated commands unless the user explicitly wants remote logging.
4. Distinguish read-only preflight from real training-scale work.
