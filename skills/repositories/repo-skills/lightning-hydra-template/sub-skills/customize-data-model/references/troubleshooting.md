# Data and Model Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Error locating target 'src....'` | `_target_` still points to old package or moved module. | Run `check_hydra_targets.py --repo-root .` and update all stale target strings. |
| `TypeError: __init__() got an unexpected keyword` | Config key does not match constructor signature. | Compare config YAML against the class signature; remove/rename the key. |
| `TypeError` about missing required constructor args | New constructor parameter missing from YAML. | Add the parameter to the owning config group or provide it through CLI/experiment config. |
| Batch-size divisibility runtime error | `batch_size` not divisible by `trainer.world_size`. | Change `data.batch_size`, `trainer.devices`, or `trainer.num_nodes`; keep this check in custom datamodules if per-device batch sizing matters. |
| Dataloader returns wrong shape for `SimpleDenseNet` | The default net expects image tensors with 4 dimensions that flatten to `input_size`. | Replace the net or adjust `input_size`/forward logic for the new data shape. |
| Checkpoint monitor or Optuna metric missing | Custom model changed logged metric names. | Update `callbacks/default.yaml` monitor and `hparams_search/*` `optimized_metric`, or log the expected names. |
| `torch.compile` failure | Backend/compiler unsupported for the model or environment. | Set `model.compile=false`; verify ordinary training first; re-enable only on supported PyTorch/backend. |
| MNIST tests fail after replacing data | Native tests still assume MNIST size, download paths, classes, or dtypes. | Update tests to use custom fixtures and target assertions; see the maintenance sub-skill. |

## Validation order

1. Import target classes.
2. Compose train/eval configs.
3. Instantiate data/model/trainer without data download.
4. Run no-network config tests.
5. Run data-specific tests with tiny fixtures or cached data.
6. Run training only after data and metric contracts are aligned.
