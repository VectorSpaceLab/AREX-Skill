# Backend and Runtime Matrix

## Purpose

Use this matrix before choosing examples, tests, or launch targets. FedML spans local Python workflows, remote MLOps services, GPU training, MPI/NCCL simulations, and separate mobile/IoT stacks. Do not assume one install verifies every surface.

## Verified preparation state for this skill

| Backend / resource | Status in the preparation environment | Skill posture |
| --- | --- | --- |
| CPU Python | Verified | Required for all core skill routes |
| CUDA / NVIDIA GPU | Available and smoke-tested with PyTorch | Optional for GPU training/serving variants |
| MPI (`mpirun`, `mpicc`, `mpi4py`) | Not present | Optional/unverified; do not make MPI examples required |
| Remote FedML/TensorOpera backend | Not credential-verified | Network/API-key-bound; commands may be documented or help-checked only |
| Docker/Kubernetes | Not selected for verification | Reference/troubleshooting only unless user requests deployment environment setup |
| Android / IoT / MNN | Out of scope | Separate toolchains; do not claim runtime coverage |

## Workflow backend requirements

| Workflow route | Required backend | Optional backend | Credential/network needs | Notes |
| --- | --- | --- | --- | --- |
| `setup-and-cli` | CPU Python | CUDA only for hardware diagnostics | login/device/run/storage need account/API key | `fedml --help`, `fedml version`, and import checks are safe offline |
| `launch-and-packaging` | CPU Python for YAML/package preflight | GPU/Docker depending on launched workload | `fedml launch` and Python `fedml.api.launch_job` need backend access | build/package can be local; launch is remote |
| `distributed-training` | CPU Python for central/small examples | CUDA, DDP, DeepSpeed, `llm` extra | dataset/model downloads and remote launch may need network | LLM examples are expensive and optional |
| `federated-learning` | CPU Python for SP simulation and algorithm-flow docs | MPI, NCCL, CUDA | cross-silo/cross-cloud roles often need network, MQTT/S3 config, or multiple nodes | Treat MPI/NCCL examples as optional unless the user prepares that runtime |
| `model-serving` | CPU Python for local predictor/server patterns | CUDA/Docker for real models and GPU endpoints | model-card push/deploy/run need account/API key; on-prem may need local platform | Local predictor smoke is safe; remote deployment is credential-bound |
| `workflow-orchestration` | CPU Python for DAG/API shape | backend services for real TrainJob/DeployJob execution | most concrete jobs call FedML MLOps APIs | Use local dummy jobs for structural DAG checks |

## Optional extras and when to use them

| Extra / dependency family | Use only when | Notes |
| --- | --- | --- |
| `fedml[MPI]` | user explicitly needs MPI simulation or multi-process examples | Requires host MPI runtime such as OpenMPI or MPICH; the prep env did not have `mpirun` |
| `fedml[deepspeed]` | user needs DeepSpeed LLM training scripts | Heavy GPU/training dependency |
| `fedml[llm]` | user needs full LLM training example stack | May download large models/data and install transformers/accelerate/peft-style tooling |
| `fedml[tensorflow]`, `fedml[jax]`, `fedml[mxnet]` | user selects those framework examples | Not part of the minimal PyTorch/CPU skill route |
| Docker/K8s packages | user asks for containerized deployment or cluster setup | Use platform-specific docs; do not run privileged scripts without approval |

## Practical routing rules

1. If the user asks for a fast local check, stay on CPU and use `scripts/check_install.py` or the model/workflow local smoke scripts.
2. If the user asks for real GPU training, verify `torch.cuda.is_available()` in their target environment and inspect memory/model size before launching.
3. If the user asks for MPI, first install and verify MPI independently; do not adapt MPI examples into a CPU-only run and call that equivalent.
4. If the user asks for platform launch, ask for or locate the API key/config and clarify whether remote side effects are allowed.
5. If the user asks for Android or IoT, state that this skill is Python-focused and that the mobile/embedded stack was excluded from the verified scope.
