# Execution modes

PocketFlow supports three launch paths: local, Docker, and Seven. Use the bundled helpers to preview the resolved arguments before running anything expensive.

## Local mode

Source launcher: `scripts/run_local.sh`

What the source launcher does:
- parses `-n` / `--nb_gpus`
- resolves path arguments from `path.conf`
- copies the selected run script to `main.py`
- queries `nvidia-smi` for idle GPUs
- uses `mpirun` when more than one GPU is requested

Safe checks:
- `python scripts/validate_path_conf.py --mode local --script nets/resnet_at_cifar10_run.py --conf path.conf`
- `python scripts/check_runtime.py`

Notes:
- the launcher selects GPUs with memory use below 50%
- if Horovod and TF-Plus are both unavailable, multi-GPU training is unsupported and the wrapper only reports a warning

## Docker mode

Source launcher: `scripts/run_docker.sh`

What the source launcher does:
- stages a minimal copy of the checkout
- resolves Docker-specific path arguments from `path.conf`
- starts a container with mounted code, log, model, and data directories

Safe checks:
- `python scripts/validate_path_conf.py --mode docker --script nets/resnet_at_cifar10_run.py --conf path.conf`
- `bash scripts/create_minimal_copy.sh . /tmp/pocketflow-minimal --dry-run`

Notes:
- use Docker mode only when the container runtime is already available
- do not rely on the source launcher to edit the working tree in place

## Seven mode

Source launcher: `scripts/run_seven.sh`

What the source launcher does:
- stages a minimal copy
- rewrites the Seven job spec with the requested GPU count
- submits the job to Tencent Seven

Safe checks:
- `python scripts/validate_path_conf.py --mode seven --script nets/resnet_at_cifar10_run.py --conf path.conf`
- `python scripts/check_runtime.py`

Notes:
- Seven is Tencent-specific infrastructure
- treat the original Seven launcher and `main.sh` / `run.sh` as reference-only unless you already have that environment

## Practical order

1. Validate `path.conf`.
2. Probe TensorFlow and optional GPU backends.
3. Choose the execution mode.
4. Stage a minimal copy only if the chosen mode needs packaging.

If you only need a non-destructive preview, stop after the validator output.
