# SaProt Dataset and Config Troubleshooting

## LMDB Problems

### Missing `length` key

Symptoms: dataloader initialization succeeds but `__len__` fails with a decode or integer conversion error.

Fix:

1. Inspect the LMDB with the bundled converter’s validation mode or a small LMDB reader.
2. Ensure the database contains string keys `info`, `length`, and numeric keys from `0` to `length - 1`.
3. Recreate the split with `scripts/jsonl_to_lmdb.py` if the database was written by a generic LMDB tool that did not create SaProt metadata keys.

### Numeric keys do not match `length`

Symptoms: iteration raises missing-row errors for high indices or ignores extra rows.

Fix: rebuild the LMDB from JSONL in a deterministic order, or manually repair `length` only when the numeric key range is known to be complete.

### Very large `map_size`

The original helper opens LMDB with a very large map size. On some filesystems this reserves address space or appears alarming in quota tools. Use `--map-size-gb` in the bundled converter to choose a smaller value for tiny smoke datasets, and increase it for large datasets before the first write.

## JSON Row Problems

### Required field missing

Symptoms: dataset `__getitem__` raises `KeyError` for fields such as `seq`, `label`, `fitness`, `seq_1`, `seq_2`, `valid_mask`, or `tertiary`.

Fix: select the correct `--dataset-type` in `jsonl_to_lmdb.py` before conversion and compare the row schema in `data-formats.md` with the YAML `dataset_py_path`.

### pLDDT length mismatch

Symptoms: low-confidence masking silently covers fewer tokens than expected or leaves residues unmasked because `zip(tokens, plddt)` stops early.

Fix:

- Ensure `plddt` length matches the tokenizer token count for `seq`.
- For PPI rows, check `plddt_1` against `seq_1` and `plddt_2` against `seq_2`.
- If no pLDDT arrays are available, remove `plddt_threshold` from dataset kwargs instead of leaving incomplete fields.

### Contact row shape mismatch

Symptoms: contact prediction fails while computing pairwise distances or masking invalid residues.

Fix: ensure `valid_mask` length, `tertiary` row count, and tokenized `seq` length agree after truncation. `tertiary` should be a list of 3D coordinates.

## Config Path Problems

### Invalid `model_py_path` or `dataset_py_path`

Symptoms: dynamic import fails before any training work begins.

Fix:

- Use slash-style paths with no `.py` suffix.
- Resolve model paths under `model/` and dataset paths under `dataset/`.
- Examples: `saprot/saprot_regression_model`, `saprot/saprot_regression_dataset`, `mutation_zeroshot_dataset`.
- Run `scripts/validate_config.py --config task.yaml --base-dir <run-base>` before execution.

### Relative paths resolve from the wrong directory

Symptoms: config validation passes from one directory but the runtime launcher cannot find LMDB or weights.

Fix: use the same `--base-dir` for validation as the directory from which the launcher will run, or rewrite paths to be absolute for private local execution. Do not bake machine-specific absolute paths into reusable skill content.

### Tokenizer or model path missing

Symptoms: `EsmTokenizer.from_pretrained` or model initialization cannot find files.

Fix:

- Place Hugging Face model/tokenizer directories under a known local path such as `weights/PLMs/<model-name>`.
- Keep `model.kwargs.config_path` and `dataset.kwargs.tokenizer` aligned unless intentionally mixing model and tokenizer assets.
- Use `--require-assets` in the validator when local assets are expected to exist.

## Trainer Backend Problems

### GPU device count mismatch

Symptoms: Lightning reports invalid devices, CUDA index errors, or distributed initialization hangs.

Fix:

- If using `CUDA_VISIBLE_DEVICES`, `Trainer.devices` should not exceed the number of visible device ids.
- For CPU checks, use `accelerator: cpu`, `devices: 1`, `precision: 32`, and often `num_workers: 0`.
- For multi-GPU runs, confirm `num_nodes`, `WORLD_SIZE`, `NODE_RANK`, `MASTER_ADDR`, and `MASTER_PORT` match the launcher environment.

### WandB should not run

Symptoms: run prompts for a WandB API key or logs unexpectedly.

Fix: set `Trainer.logger: False` for smoke tests, or configure an intentional offline/online logging mode in `setting.os_environ` before execution.

## When to Route Elsewhere

- If the problem is converting structures to combined SaProt sequences, use `structure-sequences`.
- If the problem is model loading, embeddings, mutation scoring, or inverse folding, use `model-inference`.
- If the problem is launching training, evaluating checkpoints, managing WandB, or interpreting Lightning runtime failures, use `training-evaluation`.
