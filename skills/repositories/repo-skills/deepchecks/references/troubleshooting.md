# Deepchecks Root Troubleshooting

## When to read

Use this page for package-wide installation, import, optional dependency, display, and environment issues before debugging modality-specific data objects. For `Dataset`, `TextData`, or `VisionData` input errors, route to the relevant sub-skill troubleshooting page.

## Quick diagnostic

Run the bundled diagnostic in the target Python environment:

```bash
python scripts/check_deepchecks_install.py --include-nlp --include-vision --include-nlp-properties
```

The script prints JSON with import status, package version, optional dependency status, and torch CUDA visibility. It does not run suites, download data, or write files.

## Install or import failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `PackageNotFoundError: deepchecks` or `ModuleNotFoundError: deepchecks` | Deepchecks is not installed in the active Python environment. | Install `deepchecks` in the same Python used by the notebook, script, CI job, or agent. Then rerun the diagnostic. |
| Resolver rejects the package on a new Python version | This source snapshot declared support up to Python 3.10 and has older compiled/data-science dependencies. | Use a supported Python version for this package snapshot or upgrade Deepchecks if the project allows it. |
| Import is slow or prints a latest-version warning | Deepchecks checks for new versions on first import unless disabled. | Set `DISABLE_LATEST_VERSION_CHECK=True` in offline/CI environments. |
| Plotly/IPython/widget import errors | Base install is incomplete or notebook/display dependencies are inconsistent. | Reinstall/upgrade the base package in a clean environment. For CI, avoid widgets and save HTML/JSON instead. |
| `pkg_resources is deprecated` warning appears | Deepchecks uses a dependency path that imports `pkg_resources` under newer setuptools. | Treat as a warning unless it becomes an error in a pinned environment. Pin/adjust packaging tools only if the user's environment policy allows it. |

## Optional NLP failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `deepchecks.nlp` import fails | `deepchecks[nlp]` dependencies are missing. | Install `deepchecks[nlp]` in the active environment. |
| Text property calculation imports `fasttext` or similar optional dependency and fails | The heavier `nlp-properties` extra is not installed. | Install `deepchecks[nlp-properties]` only when the task needs those property calculators. Otherwise use precomputed properties. |
| A tokenizer/model-related check downloads data or hangs | Default NLP workflows can rely on tokenizer/model resources. | Use precomputed properties/embeddings or pass a local tokenizer/model. The NLP sub-skill's smoke helper is no-download by default. |

## Optional vision failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Importing `deepchecks.vision` says PyTorch is not installed | `deepchecks.vision` imports torch at import time. | Install `deepchecks[vision]` plus a compatible `torch`/`torchvision` build. |
| GPU is visible but `torch.cuda.is_available()` is false | CPU-only torch build, missing driver passthrough, or incompatible CUDA runtime. | Use CPU validation if acceptable. Install a CUDA torch build only when GPU-backed model execution is required. |
| Vision dataset examples try to download public image/model assets | Many public demos use external data/model downloads. | Use a local dataset, precomputed predictions, or the bundled vision smoke helper for diagnostics. |

## Display, HTML, JSON, and CI problems

Route to [results-and-integrations](../sub-skills/results-and-integrations/SKILL.md) when the package imports and suites run, but result handling fails.

Common fixes:

- In notebooks, `result.show()` may require widgets and an interactive frontend.
- In CI, prefer `result.save_as_html("deepchecks_report.html", connected=False)` and `result.to_json(with_display=False)`.
- Save artifacts before raising assertions or exiting non-zero.
- Use `suite_result.passed(...)` or `check_result.passed_conditions(...)` on live result objects when possible; JSON-only gating is less complete.

## Built-in data and model assets

Some package dataset loaders fetch data or pretrained models. If a task requires no network, avoid those loaders and build small local fixtures instead. The modality sub-skills include smoke helpers that avoid downloads and credentials.

## When to stop and ask

Ask the user before:

- Installing or changing packages in a user-owned environment.
- Downloading public datasets or model weights.
- Installing CUDA/ROCm/MPS/vendor-specific frameworks.
- Running Airflow/S3/H2O/Hugging Face integration examples that need credentials, external services, or large data.
