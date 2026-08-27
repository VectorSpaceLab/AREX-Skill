# Cross-Cutting Troubleshooting

Use this file for install/import/backend issues that appear before a task reaches a focused workflow. For training-specific issues, use [`../sub-skills/training-and-evaluation/references/troubleshooting.md`](../sub-skills/training-and-evaluation/references/troubleshooting.md). For custom CSV and prediction issues, use [`../sub-skills/custom-data-and-prediction/references/troubleshooting.md`](../sub-skills/custom-data-and-prediction/references/troubleshooting.md).

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `models`, `data`, `exp`, or `utils` | The repository is source-style and the checkout root is not on Python's import path | Run from the checkout or add the checkout root to `PYTHONPATH`; then repeat the minimal import check from [`install.md`](install.md). |
| Dependency installation fails with legacy pins | The documented stack targets an old Python / PyTorch era | Use a legacy environment for exact reproduction, or use a modern stack only after validating with [`../scripts/run_forecasting_smoke.py`](../scripts/run_forecasting_smoke.py). |
| `AttributeError: np.Inf was removed in the NumPy 2.0 release` | The early-stopping helper uses the legacy `np.Inf` alias | Use NumPy `<2` for this snapshot, or patch the code to use `np.inf` before running long jobs. |
| CUDA is selected unexpectedly | CUDA is visible and the launcher enables GPU mode when available | Use the smoke helper's `--backend cpu` option, or hide CUDA before launch. Do not rely on a string `False` value for the GPU flag. |
| Benchmark dataset file is missing | Built-in dataset names expect external CSVs under the data root | Validate a custom tiny CSV first. Only acquire benchmark data when reproduction-scale training is required. |
| A helper says it cannot find the repository launcher | `--repo-root` does not point at an Informer2020 checkout | Re-run the helper with `--repo-root` set to the checkout root. The helper should find the forecasting launcher there. |
| Helper dry-run looks correct but execution writes files in an unexpected place | The forecasting launcher writes `results/` relative to its current working directory; checkpoints use the supplied checkpoint base | Use the smoke helper's `--work-dir` so generated `data/`, `checkpoints/`, and `results/` stay together. |
| Tensor-size mismatch around convolution / circular padding | PyTorch version differences can affect the circular padding behavior used in embeddings and convolutional distillation | Validate with the tiny smoke path. If the mismatch persists, align to the documented PyTorch era or patch padding logic for the runtime version. |
| A long run is too slow or exhausts memory | Full benchmark presets are multi-epoch, multi-repeat research runs | Reduce `seq_len`, `label_len`, `pred_len`, `batch_size`, `d_model`, and `itr`; prefer `attn=prob` for long sequences. |

## Fast triage order

1. Import check: can Python see source modules?
2. Data check: does the CSV validate with the bundled checker?
3. Backend check: is CUDA visible or intentionally hidden?
4. Smoke dry-run: does the generated command match the intended target/feature mode/window sizes?
5. Execute tiny smoke only after the first four checks pass.
