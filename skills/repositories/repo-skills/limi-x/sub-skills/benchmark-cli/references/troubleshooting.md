# LimiX benchmark CLI troubleshooting

Use this when a benchmark-style classification or regression command fails before, during, or after inference.

## GPU guard stops immediately

Symptom:

```text
SystemError: GPU device not found. For fast training, please enable GPU.
```

Cause and response:

- The benchmark CLI files check `torch.cuda.is_available()` at import/startup time and stop before processing arguments when CUDA is unavailable.
- Full checkpoint benchmark inference needs a local LimiX checkpoint and may require CUDA/GPU. Do not report that a benchmark CLI ran on CPU unless the actual command completed in that environment.
- On CPU-only machines, use this sub-skill only for dataset validation and command construction. For direct no-retrieval API experiments, route to `../predictor-inference/SKILL.md` instead of the benchmark CLI.
- If a GPU should be available, check the active Python environment, CUDA-visible devices, driver/runtime compatibility, and `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"` before retrying.

## Missing data/model triggers downloads or network failures

Symptoms:

- Command hangs or fails before inference while trying to access model/data hosting.
- Files appear under `./cache` unexpectedly.
- Offline environment fails even though the dataset layout is valid.

Cause and response:

- If `--data_dir` is omitted, classification downloads the default classification benchmark dataset into `./cache/bcco_cls`; regression downloads the default regression benchmark dataset into `./cache/bcco_reg`.
- If `--model_path` is omitted, the command downloads the default LimiX-16M checkpoint into `./cache`.
- The CLI sets a Hugging Face-compatible endpoint override internally, so network behavior can differ from a user's default Hugging Face settings.
- Safer pattern: always pass both `--data_dir` and `--model_path`, and validate that the checkpoint file exists before launching inference.

## Config path does not mean what you expected

Symptoms:

- A command using the default `--inference_config_path` creates a new config file.
- Retrieval was expected, but behavior looks like a no-retrieval generated config.
- The command fails because a target directory for the config path does not exist.

Cause and response:

- The classifier's default config path is `./config/cls_default_retrieval.json`; the regression default is `./config/reg_default_retrieval.json`.
- In this checkout, explicit shipped retrieval configs use 16M/2M names such as `config/cls_default_16M_retrieval.json` and `config/reg_default_16M_retrieval.json`; no-retrieval configs use `config/*_default_noretrieval.json` names.
- If the requested path does not exist, the script writes a generated no-retrieval-style config at that path. Pass an existing config explicitly when reproducibility matters.

## Target column or data shape problems

Symptoms:

- Dataset is skipped with a truncated error message.
- Debug mode raises pandas, sklearn, or shape errors.
- Prediction CSVs are missing for one dataset while other datasets complete.

Checklist:

1. Dataset root contains folders, not direct CSV files only.
2. Each folder has `<folder>/<folder>_train.csv`.
3. Provide `<folder>/<folder>_test.csv` for regression; classification can split train when test is absent.
4. Train/test CSVs include a header row and at least two columns.
5. The last column is the target.
6. Train/test feature columns match in name and order.
7. Rows are non-empty and have a consistent number of columns.
8. Regression targets parse as floats and have nonzero training variance.

Run the validator first:

```bash
python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py DATASET_ROOT --task auto
```

## Classification has too few or too many classes

Symptoms:

- Error text includes `rst is None`.
- Dataset is silently absent from `all_rst.csv` when not using `--debug`.

Cause and response:

- The benchmark classifier supports 2 to 10 training classes. One-class datasets and datasets with more than 10 classes are skipped.
- Recode/filter the target before using the benchmark CLI, or choose a different workflow outside this benchmark-CLI surface.
- The validator reports class counts before inference.

## Training rows at or above 50,000

Symptoms:

- Classification dataset is skipped with a message about `seq_len` greater than 50,000 or GPU-memory limitations.

Cause and response:

- The classification CLI skips datasets with `len(X_train) >= 50000`.
- LimiX usage guidance targets tabular datasets below 50,000 samples and below 10,000 features; larger datasets can require more hardware and may not benefit relative to supervised tabular baselines.
- Subsample, split into smaller benchmark tasks, or choose a non-benchmark workflow if the goal is large-data training/inference.

## Categorical feature surprises

Symptoms:

- A feature column disappears from the effective classification input.
- Classification metrics differ after adding a test CSV.

Cause and response:

- Classification object/string feature columns are label-encoded from training values. If test values include unseen categories and transform fails, the CLI drops that feature column from both train and test.
- Keep test categorical values within train categories when possible, or pre-encode categories explicitly before writing CSVs.
- Regression uses predictor preprocessing on the combined train/test feature frame; still prefer simple, consistently represented categories.

## Search-space sampling overwrites prediction CSVs

Symptoms:

- `all_rst.csv` has multiple rows per dataset, but each dataset has only one prediction CSV.

Cause and response:

- `--search_space_sample_num N` records multiple `search_space_sample_index` rows in `all_rst.csv` when `N > 0`.
- Per-dataset prediction files are named only `<dataset>_pred_LimiX.csv`; later successful samples can overwrite earlier prediction CSVs.
- If sample-specific predictions matter, run one sample count at a time or copy/rename the prediction files after each run.

## DDP / torchrun issues

Symptoms:

- NCCL initialization errors, port conflicts, hangs, duplicate logs, or missing outputs from nonzero ranks.

Checklist:

1. Validate a single-process command first.
2. Use one process per visible GPU, for example:
   ```bash
   CUDA_VISIBLE_DEVICES=0,1 torchrun --standalone --nproc_per_node=2 inference_classifier.py ... --inference_with_DDP
   ```
3. Ensure the active environment has a CUDA-capable PyTorch build and working NCCL.
4. If a cluster launcher already controls rendezvous, use that launcher's `torchrun` arguments instead of `--standalone`.
5. Only rank 0 writes `config.json`, per-dataset prediction CSVs, and `all_rst.csv`.
6. If ranks conflict or the run hangs, fall back to the single-process command and inspect the PyTorch distributed environment before retrying.

## Output path confusion

Symptoms:

- Results are not where `--save_name` seemed to point.
- Nested directories appear below `./result`.
- Existing results are overwritten.

Cause and response:

- `--save_name` is interpolated as `./result/<save_name>`, not used as an independent output path.
- Use simple run slugs such as `cls_local_noretrieval_001`.
- Avoid path separators in `--save_name` unless nested result directories are intentional.
- Reusing a save name reuses the same result directory and can overwrite `config.json`, `all_rst.csv`, and per-dataset prediction CSVs.
