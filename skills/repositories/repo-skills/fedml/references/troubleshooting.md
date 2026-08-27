# Troubleshooting

## Purpose

Use this file when an install, CLI call, API call, backend selection, or workflow route fails. It covers the failure modes observed during skill preparation plus repo-specific command mismatches.

## Import and dependency failures

### `ModuleNotFoundError: No module named 'pkg_resources'`

Current FedML imports still pass through `pkg_resources`. If the target environment uses a future setuptools that removed it, install a compatible setuptools:

```bash
python -m pip install "setuptools<81"
python -c "import fedml; print(fedml.__version__)"
```

### NumPy 2 / older `wandb` failures

The source checkout resolved `wandb==0.13.2`, which is not compatible with NumPy 2.x in the verified environment. If import errors mention removed NumPy aliases, use:

```bash
python -m pip install "numpy<2"
python -m pip check
```

Then retry the import.

### Wrong `fedml` executable

If `fedml --help` points to a different environment than `python -c 'import fedml'`, run:

```bash
which fedml
python -c "import sys, fedml; print(sys.executable); print(fedml.__file__)"
```

Reinstall in the active environment or invoke the environment-specific binary.

## CLI surface mismatches

### `fedml diagnosis` is not available

The current CLI exposes backend diagnostics as:

```bash
fedml network --help
```

Some docs/source comments still use `diagnosis`. Use `network` for command-line diagnostics. The Python API helper is still named `fedml.api.fedml_diagnosis(...)`.

### `fedml jobs start` is not available

Older docs mention `fedml jobs start`, but the verified CLI root does not expose `fedml jobs` or any top-level `jobs` command. Prefer:

```bash
fedml launch job.yaml
fedml run list
fedml run status <run-id-or-options>
```

or the Python API:

```python
import fedml.api
result = fedml.api.launch_job("job.yaml", api_key="...")
```

## Authentication, platform, and network issues

- `login`, `launch`, `run`, `cluster`, `storage`, and most `model` remote operations require backend connectivity and often an API key.
- Ask before creating, stopping, killing, or deploying remote resources.
- Check backend version alignment: CLI `-v local|dev|test|release`, YAML `env_version` / `config_version`, and `fedml.set_env_version(...)` should not conflict.
- If networking fails, check proxy/firewall settings and retry only after the user confirms external access is allowed.

## GPU and CUDA issues

For optional GPU routes, first check:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
print(torch.cuda.device_count())
PY
```

If `torch.cuda.is_available()` is false:

- confirm the host exposes GPUs;
- confirm the installed PyTorch build has CUDA support;
- confirm driver/CUDA compatibility;
- do not run LLM, DDP, DeepSpeed, or GPU deployment examples until repaired.

## MPI / NCCL simulation issues

MPI examples need more than the Python package. They need host MPI tools and usually `mpi4py`:

```bash
mpirun --version
python -c "import mpi4py; print('mpi4py ok')"
```

If either check fails, keep MPI examples optional. Do not run `python/build_tools/setup_mpi/setup-mpi.sh` automatically; it mutates the host and may use `sudo`/package managers.

NCCL simulation requires compatible GPUs, CUDA/NCCL libraries, and multi-process launch setup. Treat it as optional until explicitly requested.

## Launch and job YAML failures

- Validate that the YAML has a `job` section, `job_type` or equivalent launch intent, and a workspace/entry point that exists relative to the YAML file.
- Local package building can succeed even when remote launch will fail due missing credentials or resources.
- Resource matching failures usually mean requested GPUs/memory/provider do not match available cluster resources.
- Use `fedml run logs` or `fedml.api.run_logs(...)` after a remote launch failure.

## Training failures

- Dataset loaders may download datasets; confirm network and cache location.
- `fedml.init` may collect environment and configure multiprocessing; call it from guarded Python entry points (`if __name__ == '__main__':`) when multiprocessing is involved.
- Cross-cloud and cross-silo examples are multi-process and often require MQTT/S3/backend configuration.
- LLM training scripts are expensive and may require optional extras, GPUs, model access, and distributed launch configuration.

## Federated-learning failures

- Prefer `backend='sp'` for a first local simulation.
- MPI failures usually mean missing `mpirun`, missing `mpi4py`, or launching with the wrong number of ranks.
- Cross-silo client/server role mismatches are usually caused by inconsistent YAML, rank, run id, backend env, or API credentials.
- Privacy/security/analytics examples are advanced variants; confirm datasets, parameters, and compute before running.

## Model serving failures

- Local serving needs a predictor class with a compatible `predict` method and JSON-serializable outputs.
- Streaming predictors must yield or stream chunks; do not wrap them as ordinary one-shot JSON predictors.
- Remote deployment requires model card state, endpoint id/name, workers/masters or provider resources, backend access, and sometimes Docker.
- For local endpoint checks, test readiness and a tiny prediction before registering or deploying remotely.

## Workflow orchestration failures

- `Workflow.add_job` accepts only `Job` instances; custom local jobs must subclass `fedml.workflow.Job` and implement `run`, `status`, and `kill`.
- Duplicate job names are rejected.
- Cyclic dependencies fail when the workflow computes topological order.
- Real `TrainJob`, `ModelDeployJob`, and `ModelInferenceJob` wrappers upload/download state and call backend APIs; do not use them for offline smoke tests unless backend calls are mocked.
