# OpenLLM Cross-Cutting Troubleshooting

## When to read

Read this when an OpenLLM task fails before it clearly belongs to local serving, model repositories, cloud deployment, or environment maintenance.

## Install or import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `openllm: command not found` | Package not installed in the active environment, or scripts directory not on `PATH`. | Run `python -m pip install openllm` in the target environment, then `python -m pip show openllm` and `python -m openllm --help` if available. Use the root `scripts/check_openllm_install.py` helper to inspect import and CLI visibility. |
| `ModuleNotFoundError: openllm` | Python process is not using the environment where OpenLLM was installed. | Use `python -c "import sys; print(sys.executable)"`, reinstall into that Python with `python -m pip install openllm`, then rerun the import check. |
| Dependency conflict after install | Existing environment has incompatible packages. | Prefer a fresh virtual environment. Run `python -m pip check` and avoid broad upgrades in a user-owned environment without approval. |

## Model repository and network failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `The repo cache is never updated` | `openllm` has no cached model repository yet. | Run `openllm repo update` only when network access and disk writes are acceptable. For offline diagnostics, use the `model-repositories` local catalog helper instead. |
| `The repo cache is outdated` | Cache timestamp is older than OpenLLM's update interval. | Update when fresh model metadata is required. If running in noninteractive automation, treat the warning as a freshness signal rather than a fatal error unless no models are found. |
| Git clone failure while updating repos | Network, DNS, proxy, auth, or invalid custom repo URL. | Validate the URL first with `sub-skills/model-repositories/scripts/validate_repo_url.py`; retry with known network/proxy settings; confirm the custom repo is public because OpenLLM only documents public custom repositories. |

## Credentials and secrets

- Gated Hugging Face models require `HF_TOKEN`. Pass it as `--env HF_TOKEN` if the variable already exists or `--env HF_TOKEN=<value>` only in a private shell. Do not write token values into logs, scripts, or generated commands shown to other users.
- BentoCloud deployment requires `bentoml cloud login` and a BentoCloud context. Do not collect or echo API tokens in generated artifacts.
- If a Bento requires environment variables from its `bento.yaml`, OpenLLM may prompt interactively or fail in noninteractive mode when no value is available.

## Hardware and resource failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Warning about failing to get local GPU info | NVIDIA driver/NVML unavailable or not accessible. | Use `sub-skills/environment-maintenance/scripts/check_installation.py --check-gpu`. If no GPU is expected, proceed only with CPU-compatible models. |
| `does not appear to have sufficient resources` | `can_run` compared model Bento resources to local hardware and found insufficient GPU memory/count or unsupported platform. | Pick a smaller model/version with `openllm model list`, choose a cloud instance in `openllm deploy`, or use a CPU-compatible model only when the model's Bento supports it. |
| Server readiness timeout | Model download or dependency install is slow, model failed to load, port is blocked, or required env/credentials are missing. | Read `sub-skills/local-serving/references/troubleshooting.md`; check server logs, `/readyz`, credentials, and port conflicts before retrying. |

## Destructive operations

OpenLLM cleanup commands can delete caches and configuration. Before running `openllm clean model-cache`, `openllm clean venvs`, `openllm clean repos`, `openllm clean configs`, or `openllm clean all`, confirm the user wants those local files removed. Use the `environment-maintenance` sub-skill for safer inspection first.

## Where to continue

- Local server or terminal chat failure: [../sub-skills/local-serving/references/troubleshooting.md](../sub-skills/local-serving/references/troubleshooting.md)
- Missing models or custom repo issues: [../sub-skills/model-repositories/references/troubleshooting.md](../sub-skills/model-repositories/references/troubleshooting.md)
- BentoCloud deployment failure: [../sub-skills/cloud-deployment/references/troubleshooting.md](../sub-skills/cloud-deployment/references/troubleshooting.md)
- Cache, venv, GPU probe, or cleanup failure: [../sub-skills/environment-maintenance/references/troubleshooting.md](../sub-skills/environment-maintenance/references/troubleshooting.md)
