# DeepCTR-Torch troubleshooting

Use this root troubleshooting reference for install/import, shared training API, device, and package-wide failures. For data-shape details, read `sub-skills/feature-column-inputs/references/troubleshooting.md`; for DIN/DIEN sequence issues, read `sub-skills/sequence-and-interest-models/references/troubleshooting.md`; for multi-task target/loss issues, read `sub-skills/multitask-modeling/references/troubleshooting.md`.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'deepctr_torch'` | Package not installed in the active Python environment. | Install with `python -m pip install -U deepctr-torch`, then run `python scripts/check_deepctr_torch_env.py --quick`. |
| `ModuleNotFoundError: No module named 'requests'` during `import deepctr_torch` | `deepctr_torch.utils` imports `requests` for a background version check, but the distribution metadata may not declare it. | `python -m pip install requests`; then retry the import. |
| Import prints `Please check the latest version manually...` | The package starts a best-effort PyPI version check in a background thread and could not reach PyPI. | Usually safe to ignore offline; verify the installed version with `import deepctr_torch; print(deepctr_torch.__version__)`. |
| `NotImplementedError` from `compile` | Unsupported optimizer/loss/metric string. | Use only supported strings in `references/training-api-and-persistence.md`, or pass a PyTorch optimizer/callable loss directly where supported. |
| `roc_auc_score` error about one class | Tiny validation/test slice contains only positive or only negative labels. | Use a stratified split, larger batch/test data, disable `auc` for tiny smoke runs, or compute AUC only on a slice with both classes. |
| `KeyError` when calling `fit` or `predict` with a dict | `model_input` is missing a key from `get_feature_names(...)`, or feature names changed after model construction. | Rebuild `feature_names` from the exact feature columns used to construct the model and validate with `sub-skills/feature-column-inputs/scripts/validate_feature_input.py`. |
| Tensor size mismatch or concatenation error | Dense vector width, VarLen maxlen, sequence length, or target/history embedding dimensions do not match declarations. | Run the feature-input validator, then use the owning sub-skill troubleshooting page for the specific feature type. |
| `ValueError: gpus[0] should be the same gpu with device` | Constructor received `device='cuda:k'` but `gpus[0] != k`. | Use `device='cuda:0', gpus=[0, 1]` or set `gpus=None` for single-device execution. |
| CUDA requested but unavailable | CPU-only torch wheel, missing container GPU passthrough, incompatible driver/wheel, or no visible device. | First run `python scripts/check_deepctr_torch_env.py --cuda`. If it fails, use `device='cpu'` or install a torch build compatible with the host CUDA driver. |
| `EarlyStopping` or `ModelCheckpoint` does nothing | Monitored metric key is absent from logs, `patience`/`period` behavior misunderstood, or validation disabled. | Ensure `metrics` includes the monitored metric and `validation_split`/`validation_data` is active for `val_*` monitors. |
| Checkpoint path not created | Parent directory absent or save permissions denied. | `ModelCheckpoint` creates parent directories when possible; choose a writable path and avoid protected system directories. |
| Full model load fails after package/Python upgrade | `torch.save(model)` pickles class paths and environment details. | Prefer `state_dict` weights plus reconstructed feature columns; use `map_location='cpu'` when loading on CPU. |
| Multi-task predictions hard to interpret | `predict` returns columns in `task_names` order. | Use `sub-skills/multitask-modeling/references/mtl-models-and-training.md` and compute per-task metrics with explicit column indexing. |
| Slow or unstable smoke tests | Tiny examples still run PyTorch training loops; CUDA initialization and thread pools can dominate. | Use CPU, one epoch, small batch, and set torch threads to one in bundled smoke helpers where available. |

## Environment checker

Run:

```bash
python scripts/check_deepctr_torch_env.py --quick
```

Use `--cuda` only when the user explicitly wants to verify CUDA. CPU verification is sufficient for the default package workflows in this skill.
