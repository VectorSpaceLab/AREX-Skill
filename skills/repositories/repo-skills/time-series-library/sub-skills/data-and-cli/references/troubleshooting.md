# Data and CLI Troubleshooting

## `BuilderConfig '<name>' not found`

Likely cause: TSLib did not find the local CSV or `.ts` file and tried the Hugging Face dataset using a config derived from `data_path` or `model_id`.

Fix:

```bash
python scripts/validate_tslib_data.py --task long_term_forecast --data custom \
  --root-path ./dataset/my-data --data-path my.csv --target OT
```

Then correct `--root_path` and `--data_path`. For a directory path, keep the final slash in commands for readability, but the essential requirement is that `os.path.join(root_path, data_path)` exists.

## CSV column errors

Symptoms:

- `ValueError: list.remove(x): x not in list`
- Missing `date` errors from pandas/time feature code.
- Channel mismatch later in the model.

Fixes:

- Include a `date` column and numeric feature columns.
- For `custom`, ensure `--target` names an existing column.
- Count non-date columns and set `--enc_in`, `--dec_in`, and `--c_out` accordingly for `features M`; for `features MS`, `c_out` is often one target but scripts may still set all channel counts for model internals.

## DataLoader hangs or is slow

Use `--num_workers 0` for smoke tests and constrained environments. Increase workers only after the dataset is known to load.

## GPU selected unexpectedly

`run.py` chooses CUDA when `torch.cuda.is_available()` and `use_gpu` is true. Add `--no_use_gpu` to smoke commands. Also check any copied shell script for `export CUDA_VISIBLE_DEVICES=...`.

## Missing output files

- Check whether training reached `test()`; failures during data loading or model build can leave only a checkpoint folder or no result folder.
- For M4, averaged metrics require all six seasonal forecast CSVs.
- For classification, the result text is under `results/<setting>/`, not at repo root.
- If `--checkpoints` was changed, checkpoint loading in test-only mode must use the same path.

## Test-only mode cannot load a checkpoint

`--is_training 0` calls `test(setting, test=1)` for most tasks and expects a matching `checkpoint.pth`. Train first or point `--checkpoints` to the folder containing the setting used during training.
