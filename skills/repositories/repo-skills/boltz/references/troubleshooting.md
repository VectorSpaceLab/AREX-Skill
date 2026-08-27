# Cross-Cutting Troubleshooting

Use this page for failures that affect multiple Boltz workflows. For workflow-specific diagnosis, route to the nearest sub-skill troubleshooting reference.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: boltz`.
- `boltz: command not found`.
- Package installs but CLI/import checks fail.

Fix:

- Use Python `>=3.10,<3.13` in a fresh environment.
- Install the package with `pip install boltz -U` for CPU/general use or `pip install 'boltz[cuda]' -U` only when CUDA extras are required and compatible.
- Verify both metadata and import:

  ```bash
  python - <<'PY'
  import importlib.metadata as md
  import boltz
  print(md.version('boltz'))
  PY
  boltz --help
  boltz predict --help
  ```

## CUDA Or Optional Kernel Problems

Symptoms:

- Optional cuEquivariance/kernel import errors.
- Old NVIDIA GPU compatibility failures.
- CUDA available in the host but prediction/training fails at runtime.

Fix:

- For prediction, retry with `--no_kernels` when optional kernel errors appear.
- Confirm the PyTorch/CUDA wheel, driver, and GPU architecture are compatible before blaming Boltz input files.
- Use `--accelerator cpu` only for tiny inspection or parser-oriented checks; real prediction/training can be too slow on CPU.

## Cache And Downloads

Symptoms:

- Model/CCD/molecule downloads fail or stall.
- `BOLTZ_CACHE` errors.
- Existing processed outputs are reused unexpectedly.

Fix:

- Set `--cache` or `BOLTZ_CACHE` to an absolute writable path.
- If inputs changed but output names did not, add `--override` for prediction.
- Decide explicitly before large downloads or network calls; model weights, molecule/CCD archives, raw training data, and benchmark assets can be large.

## CLI Or Config Misuse

Symptoms:

- Input directory contains nested directories or unsupported suffixes.
- FASTA input lacks YAML-only features such as affinity, modifications, covalent bonds, or pocket conditioning.
- Training config still contains placeholders such as `SET_PATH_HERE`.

Fix:

- Use `sub-skills/prediction/scripts/boltz_input_validator.py` for prediction inputs.
- Use `sub-skills/training/scripts/boltz_training_config_check.py` for training configs.
- Route raw data layout issues to `sub-skills/data-preparation/SKILL.md` before attempting training.

## External Dependencies

Symptoms:

- Raw-data processing fails around Redis, `mmseqs`, taxonomy/CCD databases, or very large archives.
- Evaluation fails around OpenStructure or missing benchmark folders.

Fix:

- Use `sub-skills/data-preparation/scripts/boltz_preprocessing_checklist.py` before launching preprocessing.
- Treat OpenStructure-based evaluation as benchmark reproduction, not ordinary output summarization.
- Use `sub-skills/evaluation/scripts/boltz_evaluation_summary.py` for safe local JSON/CSV summaries that do not require benchmark targets.
