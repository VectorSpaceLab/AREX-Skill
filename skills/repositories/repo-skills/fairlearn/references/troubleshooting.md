# Fairlearn cross-cutting troubleshooting

Use this file for package-wide failures before switching to a workflow-specific troubleshooting reference.

## Import or version failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'fairlearn'` | Package is not installed in the active Python environment. | Run `python -m pip install fairlearn` or, in a checkout, `python -m pip install -e .`; then rerun `python scripts/check_install.py`. |
| `ImportError` for `numpy`, `pandas`, `sklearn`, `scipy`, or `narwhals` | Core dependency set is incomplete or broken. | Reinstall Fairlearn in a clean environment; run `python -m pip check`. |
| API signature differs from this skill | Different Fairlearn version or stale skill. | Compare with `references/repo-provenance.md` and refresh the skill if public APIs changed. |
| `fairlearn.show_versions()` prints unexpected `None` values | The function uses package metadata lookup; some distribution names can differ from import names. | Verify the import directly, e.g. `python -c "import sklearn; print(sklearn.__version__)"`. |

## Optional plotting failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| RuntimeError says to install `fairlearn[customplots]` | Matplotlib is missing for Fairlearn plotting helpers. | Install `matplotlib` directly; if using package extras, check your Fairlearn release for the exact plotting extra name. |
| Plot works locally but fails in headless CI | Matplotlib selected an interactive backend. | Set `MPLBACKEND=Agg` or call `matplotlib.use('Agg')` before importing `pyplot`. |
| `plot_metric_frame` import fails | The helper is exposed through the experimental enable module in this source. | Import `from fairlearn.experimental.enable_metric_frame_plotting import plot_metric_frame` and treat the path as experimental. |

## Optional adversarial-backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| RuntimeError says to install `torch`, `tensorflow`, or `torch or tensorflow` | No supported adversarial backend is importable. | Install the backend selected by the user; for PyTorch run `python -c "import torch; print(torch.__version__)"`. |
| `ValueError: Cuda is not available` | `cuda` was requested but the active PyTorch runtime cannot see CUDA. | Use CPU by setting `cuda=None`/`False`, or fix the PyTorch/CUDA installation and rerun the adversarial smoke script with `--cuda`. |
| PyTorch BCE loss complains about inputs outside `[0, 1]` | A custom binary predictor/adversary ended without a sigmoid while the PyTorch engine uses `BCELoss`. | Add a final `torch.nn.Sigmoid()` for binary outputs or use Fairlearn's list model builder which appends the inferred binary activation. |

## Data-shape and alignment failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Length mismatch among `X`, `y`, predictions, and `sensitive_features` | Rows are not aligned after split, filtering, or prediction. | Build all arrays from the same index; split `X`, `y`, and sensitive features together. |
| Multi-column sensitive features behave unexpectedly | The workflow may use intersections or require a single sensitive feature. | Use a DataFrame with named columns for assessment; check the owning mitigation sub-skill for multi-feature support and limitations. |
| Metric functions return confusing group labels | Sensitive features are unlabeled arrays or mixed dtypes. | Prefer pandas Series/DataFrames with meaningful names when reporting results. |
| Dataset loader downloads hang or fail | OpenML/network/cache issue. | Use `data_home` to point at an approved cache, or run a no-download dataset-loader signature check first. |

## Fairness interpretation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| User asks whether the model is "fair" without a metric or context | Fairlearn cannot choose the harm model automatically. | Ask for target, sensitive features, harm type, metric family, utility metric, and acceptable trade-offs before choosing a mitigation algorithm. |
| Mitigation improved one disparity metric but harmed utility | Fairness/utility trade-off is algorithm- and metric-specific. | Report both subgroup metrics and overall utility; compare several mitigated models when possible. |
| User wants legal compliance advice | Package API knowledge is insufficient. | Explain the technical metrics and recommend domain/legal review; do not claim legal compliance from Fairlearn results alone. |

## Native validation recovery

If a bundled smoke script fails:

1. Rerun with `--help` to check command flags.
2. Run the root install check.
3. Confirm optional dependencies required by that sub-skill.
4. Reduce to a synthetic tiny-data example before using networked datasets.
5. If the failure is due to changed public API, compare with `references/repo-provenance.md` and refresh this skill.
