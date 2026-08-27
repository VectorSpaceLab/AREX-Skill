# Cross-Cutting Troubleshooting

## `run.py` or imports fail

Symptoms:

- `python: can't open file 'run.py'`
- `ModuleNotFoundError: No module named 'data_provider'`, `models`, or `exp`
- `ModuleNotFoundError` for a dependency while showing help.

Fixes:

- Run from the TSLib source tree, or set `PYTHONPATH` so the source tree is importable.
- Install the base dependencies before task imports: PyTorch, NumPy, Pandas, SciPy, Scikit-learn, Matplotlib, Sktime, PyWavelets, datasets, Hugging Face Hub, einops, and Reformer-PyTorch.
- Use `python scripts/check_tslib_environment.py --check-core-imports` before training.

## Local data path falls through to Hugging Face and fails

Symptoms:

- `BuilderConfig '<name>' not found`
- Hub download starts unexpectedly.
- An unauthenticated Hugging Face warning appears for a local dataset.

Cause:

The local file expected by the loader does not exist, so the loader derives a dataset config from `data_path` or `model_id` and tries the Hub.

Fixes:

- Verify `--root_path` includes the trailing directory and `--data_path` is the exact CSV filename.
- For `custom`, ensure the CSV exists locally and has a `date` column plus `--target`.
- For UEA, ensure `<model_id>_TRAIN.ts` and `<model_id>_TEST.ts` exist under `--root_path`.
- Run `sub-skills/data-and-cli/scripts/validate_tslib_data.py` before `run.py`.

## GPU is used when a CPU smoke was intended

Symptoms:

- CUDA out-of-memory in a quick test.
- TSLib selects CUDA even for a tiny command.

Fix:

Add `--no_use_gpu`. The parser default for `--use_gpu` is true, and CUDA is selected when available. Also remove or rewrite `CUDA_VISIBLE_DEVICES` exports copied from benchmark shell recipes.

## Optional model dependency missing

Symptoms:

- `ModuleNotFoundError: No module named 'mamba_ssm'`
- `No module named 'chronos'`, `timesfm`, `uni2ts`, `tirex`, or `transformers`.

Fixes:

- Decide whether the requested model family is necessary. If not, switch to a core model such as `DLinear`, `TimesNet`, `PatchTST`, `TimeXer`, or `Transformer`.
- For Mamba/MambaSL, install a wheel that matches OS, Python, PyTorch, CUDA, and ABI. Do not install a random wheel just because a GPU exists.
- For LTSM models, install the specific package and prepare model cache/network access. Check source device assumptions before attempting CPU-only execution.

## Shape or channel mismatch

Symptoms:

- Model output channels do not match `batch_y`.
- Classification model build changes `seq_len`, `enc_in`, or `num_class` unexpectedly.
- TimeXer `features MS` returns one channel.

Fixes:

- Ensure `--enc_in`, `--dec_in`, and `--c_out` match the dataset feature count for forecasting/imputation/anomaly tasks.
- For `features S` or `MS`, set `--target` correctly.
- For UEA classification, let `Exp_Classification` derive dimensions from TRAIN/TEST files; do not force forecasting channel counts.

## Results are missing after a run

Checks:

- Was `--is_training 1` used? Training writes checkpoints before testing.
- Was `--checkpoints` changed? Checkpoint path controls load/save location.
- Which task was used? M4 writes under `m4_results/<model>/`, classification writes `result_classification.txt` inside `results/<setting>/`, while long-term/zero-shot write arrays and root-level result text files.
- Did early failure occur before `test()`? Inspect stdout around dataset construction, model import, and first batch.

## Benchmark script copied verbatim fails

Common causes:

- Hard-coded `CUDA_VISIBLE_DEVICES` points to a nonexistent or busy GPU.
- Dataset folder differs from the script's official benchmark path.
- Command is benchmark-scale and not suitable for a smoke check.
- Optional model dependency is not installed.
- `num_workers` is too high for a constrained environment.

Fixes:

- Render a new command with `sub-skills/forecasting/scripts/build_tslib_command.py` and explicit local paths.
- Start with `--no_use_gpu --train_epochs 1 --num_workers 0` and small windows.
- Scale back up only after data and model plumbing pass.
