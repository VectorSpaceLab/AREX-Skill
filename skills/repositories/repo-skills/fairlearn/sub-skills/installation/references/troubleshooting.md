# Installation troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: fairlearn` | Package is not installed in the active environment. | `python -m pip install fairlearn`, or `python -m pip install -e .` in a checkout. |
| `pip check` reports dependency conflicts | Mixed package manager or stale environment. | Prefer a fresh environment with Python >=3.11 and reinstall only required packages. |
| Plotting error mentions `fairlearn[customplots]` | Matplotlib is missing; extra naming may vary. | Install `matplotlib` directly, then rerun the relevant plot smoke. |
| Adversarial error says to install backend | PyTorch/TensorFlow missing. | Install the backend selected by the user; do not install both unless needed. |
| CUDA requested but unavailable | PyTorch sees no CUDA device or wrong build. | Run CPU first; verify `torch.cuda.is_available()` before passing `cuda="cuda:0"`. |
| `show_versions()` reports `None` for a dependency that imports | Distribution metadata name mismatch. | Check the import directly, e.g. `python -c "import sklearn; print(sklearn.__version__)"`. |
| User asks for a CLI command | This source does not expose a Fairlearn-specific CLI. | Use Python APIs and bundled scripts. |
| A smoke script fails after package upgrade | Generated skill may be stale. | Compare with `../../references/repo-provenance.md` and refresh the repo skill. |

## Recovery order

1. Confirm `python --version` is at least 3.11.
2. Confirm `python -m pip show fairlearn` sees the intended environment.
3. Run `python scripts/check_install.py` from the root skill directory.
4. Install only the optional dependency required by the requested workflow.
5. Run the workflow-specific smoke script.
6. If signatures or errors differ from the provenance baseline, refresh the skill.
