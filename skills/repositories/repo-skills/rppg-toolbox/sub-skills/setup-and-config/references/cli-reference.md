# CLI reference

## Invocation

Run from the repository root so the default config and package imports resolve:

```bash
python main.py --config_file configs/infer_configs/PURE_UBFC-rPPG_TSCAN_BASIC.yaml
python main.py --config_file configs/train_configs/PURE_PURE_UBFC-rPPG_TSCAN_BASIC.yaml
```

`main.py` defines `--config_file` as an optional string. Its default is the repository-relative training example `configs/train_configs/PURE_PURE_UBFC-rPPG_TSCAN_BASIC.yaml`. A path may be absolute or relative to the current working directory; prefer a repository-relative path when running from the checkout root. The README's inference examples use `configs/infer_configs/`, and its training examples use `configs/train_configs/`.

The parser is extended by the imported base classes. The accepted flags are:

| Flag | Parser type/default | Operational note |
|---|---|---|
| `--config_file` | string; default training YAML | Selects the YAML passed to `config.get_config`. |
| `--lr` | float; default `None` | Registered by `BaseTrainer`; the current `config.update_config` does not merge this value, so set `TRAIN.LR` in YAML. |
| `--model_file_name` | float; default `None` | Registered with a float type even though `TRAIN.MODEL_FILE_NAME` is a string; do not rely on this flag. Set the YAML value instead. |
| `--cached_path` | string; default `None` | Registered by `BaseLoader`; the current config updater does not apply it. Set each split's `CACHED_PATH` in YAML. |
| `--preprocess` | boolean `store_true`; default `False` | Registered by `BaseLoader`; the current config updater does not apply it. Set each split's `DO_PREPROCESS` in YAML. |

No command-line override for `DEVICE`, `INFERENCE.MODEL_PATH`, `TOOLBOX_MODE`, dataset names, or log paths is defined in the inspected entry point. Use YAML for those settings. The program prints the merged/frozen configuration before constructing loaders.

## Mode dispatch

`TOOLBOX_MODE` is an exact string:

- `train_and_test`: resolve a training dataset, optionally construct validation data, resolve a test dataset, then call the selected trainer's `train` and `test` methods.
- `only_test`: resolve a test dataset, then call the selected trainer's `test` method. The selected trainer loads `INFERENCE.MODEL_PATH`; provide a readable checkpoint.
- `unsupervised_method`: resolve the unsupervised dataset and call `unsupervised_method_inference` once for each token in `UNSUPERVISED.METHOD`.

Any other mode raises an unsupported-mode `ValueError` during configuration update or loader setup. The final fallback message in `main.py` is less complete than the actual three-mode check; trust the exact mode list above.

## Dispatch names

The current supervised model branches in both `train_and_test` and `test` are `Physnet`, `iBVPNet`, `FactorizePhys`, `Tscan`, `EfficientPhys`, `DeepPhys`, `BigSmall`, `PhysFormer`, `PhysMamba`, and `RhythmFormer`. These are case-sensitive.

The supervised dataset branches cover `UBFC-rPPG`, `PURE`, `SCAMPS`, `MMPD`, `BP4DPlus`, `BP4DPlusBigSmall`, `UBFC-PHYS`, `iBVP`, `PhysDrive`, `LADH`, and `SUMS` for train/test paths. The unsupervised branch covers `UBFC-rPPG`, `PURE`, `SCAMPS`, `MMPD`, `BP4DPlus`, `UBFC-PHYS`, and `iBVP` in the inspected `main.py`; it does not include the later train/test-only names.

The accepted unsupervised tokens are `POS`, `CHROM`, `ICA`, `GREEN`, `LGI`, `PBV`, and `OMIT`. An empty list raises `Please set unsupervised method in yaml!`; an unrecognized token raises `Not supported unsupervised method!`.

## Evidence and scope

Facts above come from `main.py` (`add_args`, mode dispatch, model/dataset branches), `config.py` (`get_config`/`update_config`), `neural_methods/trainer/BaseTrainer.py`, and `dataset/data_loader/BaseLoader.py`. Model internals, loader algorithms, and metric/plot behavior are intentionally out of scope here.
