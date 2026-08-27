---
name: datasets-configs
description: "Understand SaProt LMDB datasets, JSONL-to-LMDB conversion, task
  YAML paths, and safe config validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SaProt Datasets and Configs

Use this sub-skill when the task is about SaProt LMDB layout, JSON row fields, dataset initialization paths, tokenizer/model asset locations, or editing a task YAML before a training or evaluation run.

## Quick Routing

- Convert JSONL rows into a SaProt-style LMDB with `scripts/jsonl_to_lmdb.py`; read `references/data-formats.md` first for the row schema.
- Validate a YAML task config without importing PyTorch, Transformers, or Lightning with `scripts/validate_config.py`; read `references/configuration.md` for path rules.
- Route full training, evaluation, Lightning launch behavior, WandB logging, checkpoint selection, and expensive benchmark execution to `training-evaluation`.
- Route model loading, tokenization behavior, embeddings, mutation scoring, and forward-pass details to `model-inference`.
- Route PDB/mmCIF-to-SaProt sequence conversion, Foldseek setup, chain selection, and pLDDT masking from structures to `structure-sequences`.

## Core Facts

- `LMDBDataset(train_lmdb=None, valid_lmdb=None, test_lmdb=None, dataloader_kwargs=None)` opens one LMDB directory per stage and expects an integer-like `length` key plus numeric row keys from `0` to `length - 1`.
- `DataInterface.init_dataset(dataset_py_path, **kwargs)` dynamically imports a dataset module path such as `saprot/saprot_regression_dataset`; do not include the leading `dataset/` directory or the `.py` suffix in YAML.
- SaProt config paths are conventionally resolved from the run base: LMDB data under `LMDB/`, Hugging Face tokenizer/model directories under `weights/PLMs/`, model modules under `model/`, and dataset modules under `dataset/`.
- LMDB row values are UTF-8 JSON object strings; each dataset class expects different fields, so validate JSONL with the matching `--dataset-type` before writing a database.
- Keep data/config checks separate from execution: a config can be syntactically valid while still requiring model weights, LMDB assets, compatible GPUs, and the training stack before a real run.

## Safe Workflows

### JSONL to LMDB

1. Choose the target dataset schema from `references/data-formats.md`.
2. Validate and write rows with the bundled converter:
   `python scripts/jsonl_to_lmdb.py --jsonl rows.jsonl --lmdb-dir LMDB/MyTask/foldseek/train --dataset-type regression --map-size-gb 10240`
3. Confirm the converter reports `info`, `length`, and numeric keys.
4. Repeat for `train`, `valid`, and `test` directories if the YAML will use all three stages.

### YAML validation

1. Edit paths relative to the intended SaProt run base, not relative to the config file location unless those are the same.
2. Check module paths, asset paths, LMDB keys, and Trainer backend choices:
   `python scripts/validate_config.py --config task.yaml --base-dir .`
3. Add `--require-assets` when the machine is expected to already contain LMDB and model/tokenizer directories.
4. Do not launch training until validation errors are resolved and remaining warnings are intentionally accepted.

## Reference Map

- `references/data-formats.md`: LMDB key layout, dataset constructor behavior, JSON row fields, and converter usage.
- `references/configuration.md`: YAML section meanings, module path resolution, asset placement, CPU smoke-test adaptation, and backend validation.
- `references/troubleshooting.md`: common LMDB, JSON field, tokenizer path, pLDDT, map-size, relative path, and GPU-device failures.
