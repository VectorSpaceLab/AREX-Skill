# LimiX benchmark CLI reference

This reference covers the benchmark-style classification and regression command surface. It is self-contained; use it from a LimiX repository checkout without relying on external repo-file links.

## Preflight assumptions

- Run commands from the repository root so the benchmark scripts can import local modules and find relative config/result paths.
- Full checkpoint inference needs a local LimiX checkpoint path and may require CUDA/GPU. The current benchmark scripts stop immediately when `torch.cuda.is_available()` is false.
- Prefer local data and model paths. If `--data_dir` or `--model_path` is omitted, the scripts may contact the network and populate `./cache`.
- Validate the dataset root before model inference:
  ```bash
  python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py "$LIMIX_DATA_ROOT" --task classification
  python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py "$LIMIX_DATA_ROOT" --task regression
  ```

## CLI entry points

| Task | Command entry point | Expected dataset root |
| --- | --- | --- |
| Classification benchmark inference | `python inference_classifier.py ...` | A root containing dataset folders with `<dataset>_train.csv` and optional `<dataset>_test.csv` files. |
| Regression benchmark inference | `python inference_regression.py ...` | A root containing dataset folders with `<dataset>_train.csv`; provide `<dataset>_test.csv` for the current regression CLI to score datasets. |

The `benchmark_list/*.csv` files in the project are benchmark-suite dataset-name lists, not dataset contents and not valid `--data_dir` roots.

## Shared flags

| Flag | Default behavior | Practical guidance |
| --- | --- | --- |
| `--data_dir PATH` | If omitted, classification downloads `stableai-org/bcco_cls` to `./cache/bcco_cls`; regression downloads `stableai-org/bcco_reg` to `./cache/bcco_reg`. | Prefer a local validated dataset root to avoid network, cache, and reproducibility surprises. |
| `--save_name NAME` | If omitted, a timestamp is generated. Results go under `./result/<NAME>/`. | Use a simple slug, not an absolute path. Slashes in `NAME` create nested directories below `./result`. |
| `--inference_config_path PATH` | Classification default is `./config/cls_default_retrieval.json`; regression default is `./config/reg_default_retrieval.json`. If the chosen path does not exist, the script writes a generated no-retrieval-style config at that path. | Prefer an existing explicit config: `config/cls_default_noretrieval.json`, `config/cls_default_16M_retrieval.json`, `config/cls_default_2M_retrieval.json`, `config/reg_default_noretrieval.json`, `config/reg_default_16M_retrieval.json`, or `config/reg_default_2M_retrieval.json`. Match 16M/2M config families to the checkpoint family when possible. |
| `--model_path PATH` | If omitted, downloads `stableai-org/LimiX-16M` / `LimiX-16M.ckpt` into `./cache`. | Prefer a local checkpoint such as a LimiX-16M or LimiX-2M `.ckpt` file. Do not claim checkpoint inference ran unless the checkpoint was present and the command completed. |
| `--inference_with_DDP` | False. When set, the predictor tries the DDP inference path for applicable no-retrieval-style workloads. | Use with `torchrun` and one process per visible GPU. Sample-retrieval configs can take the retrieval inference path instead of the DDP branch. |
| `--debug` | False. Dataset-level exceptions are caught, truncated, and the script continues. | Use for smoke/debug runs when you want full tracebacks and per-dataset metric prints. |
| `--search_space_sample_num N` | `0`, meaning one default pass. | With `N > 0`, the loop records search-space indices `0..N-1`: index `0` is the default config and later indices use sampled preprocessing/base parameters. This can multiply runtime and may overwrite per-dataset prediction CSVs; `all_rst.csv` keeps rows by `search_space_sample_index`. |

## Safe local command templates

Set shell variables first to keep recipes portable:

```bash
export LIMIX_CLS_DATA_ROOT="path/to/classification_dataset_root"
export LIMIX_REG_DATA_ROOT="path/to/regression_dataset_root"
export LIMIX_CKPT="path/to/LimiX-16M.ckpt"
```

### Classification, no retrieval config

```bash
python inference_classifier.py \
  --data_dir "$LIMIX_CLS_DATA_ROOT" \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/cls_default_noretrieval.json \
  --save_name cls_local_noretrieval \
  --debug
```

### Classification, retrieval config

```bash
python inference_classifier.py \
  --data_dir "$LIMIX_CLS_DATA_ROOT" \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/cls_default_16M_retrieval.json \
  --save_name cls_local_retrieval
```

Retrieval configs usually need more memory and are best treated as GPU-first. For LimiX-2M checkpoints, prefer the matching `cls_default_2M_retrieval.json` config.

### Regression, no retrieval config

```bash
python inference_regression.py \
  --data_dir "$LIMIX_REG_DATA_ROOT" \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/reg_default_noretrieval.json \
  --save_name reg_local_noretrieval \
  --debug
```

### Regression, retrieval config

```bash
python inference_regression.py \
  --data_dir "$LIMIX_REG_DATA_ROOT" \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/reg_default_16M_retrieval.json \
  --save_name reg_local_retrieval
```

For LimiX-2M checkpoints, prefer the matching `reg_default_2M_retrieval.json` config.

### Explicit auto-download shape, not recommended for offline work

Only use this when network downloads are acceptable:

```bash
python inference_classifier.py \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/cls_default_noretrieval.json \
  --save_name cls_download_data

python inference_regression.py \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/reg_default_noretrieval.json \
  --save_name reg_download_data
```

If `--model_path` is also omitted, the command attempts to download the default LimiX-16M checkpoint into `./cache`.

### Search-space sampling shape

```bash
python inference_classifier.py \
  --data_dir "$LIMIX_CLS_DATA_ROOT" \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/cls_default_noretrieval.json \
  --save_name cls_search3 \
  --search_space_sample_num 3
```

This records rows for `search_space_sample_index` 0, 1, and 2 in `all_rst.csv`. The per-dataset prediction file name does not include the sample index, so it can retain only the last successful prediction file for each dataset unless you copy/rename outputs between runs.

## DDP launch templates

Use DDP only after a single-process command has validated imports, data layout, checkpoint loading, and a small workload. One process should map to one visible GPU.

### Classification DDP

```bash
CUDA_VISIBLE_DEVICES=0,1 torchrun --standalone --nproc_per_node=2 inference_classifier.py \
  --data_dir "$LIMIX_CLS_DATA_ROOT" \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/cls_default_noretrieval.json \
  --save_name cls_ddp_2gpu \
  --inference_with_DDP
```

### Regression DDP

```bash
CUDA_VISIBLE_DEVICES=0,1 torchrun --standalone --nproc_per_node=2 inference_regression.py \
  --data_dir "$LIMIX_REG_DATA_ROOT" \
  --model_path "$LIMIX_CKPT" \
  --inference_config_path config/reg_default_noretrieval.json \
  --save_name reg_ddp_2gpu \
  --inference_with_DDP
```

If a cluster launcher already supplies rendezvous settings, replace `--standalone` with that environment's standard `torchrun` arguments. Only rank 0 writes final CSV outputs.

## Output files

All outputs are under `./result/<save_name>/`.

| File | Producer | Contents |
| --- | --- | --- |
| `config.json` | Both CLIs | The loaded or generated inference config copied into the result directory. |
| `all_rst.csv` | Both CLIs | One row per dataset and search-space index, written by rank 0. |
| `<dataset>_pred_LimiX.csv` | Classification CLI | `label` plus probability columns `pred_0`, `pred_1`, ... for the latest successful write for that dataset. |
| `<dataset>_pred_LimiX.csv` | Regression CLI | `label` plus `pred`; labels and predictions are in the original target scale. |

## Metrics written to `all_rst.csv`

Classification rows include dataset size/shape plus:

- `auc`: binary ROC AUC or multiclass OVO ROC AUC.
- `acc`: accuracy from `argmax` probabilities.
- `f1`: binary F1 for two classes; macro F1 for multiclass.
- `logloss`: cross-entropy/log-loss.
- `ece`: expected calibration error with 10 bins.

Regression rows include dataset size/shape plus:

- `rmse`: root mean squared error after the script normalizes the target using the training mean/std.
- `R2`: R² on the normalized target.
- Prediction CSV values are denormalized back to the original target scale; recompute original-scale RMSE from that CSV if needed.
