# SaProt Data Formats

This reference summarizes the runtime dataset and LMDB conventions used by SaProt data modules.

## LMDB Directory Layout

SaProt datasets are Lightning data modules built around LMDB directories. A task config usually points to three separate directories:

- `train_lmdb`: training split directory, often under `LMDB/<Task>/<normal-or-foldseek>/train`.
- `valid_lmdb`: validation split directory, often under `LMDB/<Task>/<normal-or-foldseek>/valid`.
- `test_lmdb`: test split directory, often under `LMDB/<Task>/<normal-or-foldseek>/test`.

Each LMDB directory stores UTF-8 string values with these keys:

| Key | Meaning |
| --- | --- |
| `info` | Human-readable description of the key layout. |
| `length` | Decimal string count of dataset rows. Dataset `__len__` reads this key. |
| `0` through `length - 1` | One JSON object row per key, stored as the original JSONL line. |

If `length` is absent, malformed, or disagrees with numeric keys, dataloaders fail or silently skip rows. Always validate a newly created LMDB before training.

## Dataset Initialization

`LMDBDataset(train_lmdb=None, valid_lmdb=None, test_lmdb=None, dataloader_kwargs=None)` stores the split paths and opens one path when the matching dataloader is requested. The base class sets `shuffle=True` only for the `train` stage and passes `collate_fn` from the concrete dataset class to the PyTorch dataloader.

`DataInterface.init_dataset(dataset_py_path, **kwargs)` dynamically imports the dataset file and instantiates the last class decorated with `register_dataset`. In YAML, `dataset_py_path` is a module-like path relative to the dataset package, using slashes and no `.py` suffix, for example:

- `saprot/saprot_classification_dataset`
- `saprot/saprot_regression_dataset`
- `saprot/saprot_lm_dataset`
- `saprot/saprot_foldseek_dataset`
- `saprot/saprot_ppi_dataset`
- `saprot/saprot_contact_dataset`
- `mutation_zeroshot_dataset`

## JSON Row Schemas

All rows are JSON objects. Extra keys are usually ignored by the dataset class, but missing required keys raise `KeyError` during `__getitem__`.

| Dataset class | Typical `dataset_py_path` | Required row fields | Conditional fields | Label dtype/shape |
| --- | --- | --- | --- | --- |
| `SaprotClassificationDataset` | `saprot/saprot_classification_dataset` | `seq`, `label` | `coords` when `use_bias_feature: true`; `plddt` when `plddt_threshold` is set | integer class label |
| `SaprotRegressionDataset` | `saprot/saprot_regression_dataset` | `seq`, `fitness` | `plddt` when `plddt_threshold` is set | numeric fitness value |
| `SaprotLMDataset` | `saprot/saprot_lm_dataset` | `seq` | `coords` when `use_bias_feature: true` | masked-token ids generated internally |
| `SaprotFoldseekDataset` | `saprot/saprot_foldseek_dataset` | `seq` | none | masked structure-token ids generated internally |
| `SaprotPPIDataset` | `saprot/saprot_ppi_dataset` | `seq_1`, `seq_2`, `label` | `plddt_1` and `plddt_2` when `plddt_threshold` is set | integer interaction label |
| `SaprotContactDataset` | `saprot/saprot_contact_dataset` | `seq`, `valid_mask`, `tertiary` | none | contact targets generated from coordinates |

`seq` for SaProt tasks is the combined amino-acid plus structure-token string. `seq` for ESM2-style baselines is typically amino-acid only. Keep the dataset and tokenizer/model directory aligned.

## Field Details

- `seq`: string accepted by the tokenizer; SaProt combined tokens are tokenized as adjacent amino-acid and structure characters.
- `label`: integer class id for classification and PPI tasks.
- `fitness`: numeric regression target; optional config transforms include clipping and min-max normalization.
- `coords`: object keyed by atom name such as `N`, `CA`, `C`, or `O`, with coordinate arrays truncated to `max_length` when bias features are enabled.
- `plddt`: list of per-token confidence scores. Its length must match tokenizer tokens after any sequence truncation relevant to masking.
- `plddt_1` and `plddt_2`: PPI per-token confidence scores for `seq_1` and `seq_2`.
- `valid_mask`: boolean-like list used by contact prediction to mask invalid residues.
- `tertiary`: list of three-dimensional coordinates used to compute an 8 angstrom contact map.

## Bundled JSONL Converter

Use `scripts/jsonl_to_lmdb.py` instead of importing SaProt utility modules. It preserves SaProt key behavior while adding schema validation and clear errors.

Examples:

```bash
python scripts/jsonl_to_lmdb.py \
  --jsonl rows.jsonl \
  --lmdb-dir LMDB/Thermostability/foldseek/train \
  --dataset-type regression \
  --map-size-gb 10240
```

```bash
python scripts/jsonl_to_lmdb.py \
  --jsonl ppi.jsonl \
  --lmdb-dir LMDB/HumanPPI/foldseek/valid \
  --dataset-type ppi \
  --require-plddt
```

The converter writes `info`, `length`, and numeric keys. It refuses to overwrite a non-empty output directory unless `--overwrite` is set.

## Data Preparation Checklist

- Confirm each split has its own LMDB directory.
- Check that `length` is present and equals the number of numeric row keys.
- Match `dataset_py_path` to the JSON row fields.
- Match `dataset.kwargs.tokenizer` to the sequence type: SaProt combined sequences need a SaProt tokenizer directory; amino-acid-only baselines need an ESM tokenizer directory.
- If using `plddt_threshold`, ensure pLDDT arrays exist and align with tokenized sequence lengths.
- If using contact prediction, ensure `valid_mask` and `tertiary` lengths match `seq` tokens.
