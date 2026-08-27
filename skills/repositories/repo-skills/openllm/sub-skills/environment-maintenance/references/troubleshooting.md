# Environment Maintenance Troubleshooting

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: openllm` | Wrong Python environment. | Run `python -m pip show openllm` with the same Python used for the task. Reinstall in a fresh environment if needed. |
| `openllm --help` fails but import works | Console script is not on `PATH` or entry point installation is broken. | Try `python -m openllm --help`; reinstall the package if the console script is missing. |
| `pip check` reports broken requirements | Conflicting dependencies in the environment. | Prefer a fresh virtual environment rather than mutating a shared environment. |

## GPU and resources

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Failed to get local GPU info` | NVML/driver is unavailable or inaccessible. | Confirm the NVIDIA driver and `nvidia-smi`; use CPU-compatible workflows if no GPU is expected. |
| Resource score is `0.0` | Platform mismatch or insufficient GPU count/memory. | Select a smaller Bento, different platform, or BentoCloud target. |
| GPU exists but serving still fails | Model-specific dependency, runtime memory, or credential issue. | Inspect the per-Bento venv logs and local-serving troubleshooting; GPU visibility alone is not enough. |

## Cache and cleanup

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Per-Bento venv repeatedly reinstalls | Missing `DONE` marker or changed requirements/env hash. | Allow one clean reinstall; if it repeats, inspect requirements and disk permissions. |
| Model repository entries vanish | `openllm clean repos` or config reset removed cache/config. | Re-run `openllm repo update` and restore custom repo aliases. |
| Disk usage is high | Hugging Face model cache, cloned repos, or per-Bento venvs accumulated. | Use cleanup commands only after confirming which cache can be removed. |

## Safe helpers

- `scripts/check_installation.py` checks import/version/CLI/GPU state.
- `scripts/estimate_bento_resources.py` parses a Bento resource spec without starting a model.
