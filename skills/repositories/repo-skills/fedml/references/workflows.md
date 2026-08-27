# FedML Workflow Map

## Purpose

Use this map to choose the smallest sub-skill for a FedML task. It intentionally separates local/offline checks from remote platform actions that require credentials and may create/stop resources.

## Sub-skill routing matrix

| If the user asks to... | Read | Main commands/APIs | Source evidence anchors |
| --- | --- | --- | --- |
| install FedML, check import, login/logout, bind devices, inspect runs, storage, network/env diagnostics | `sub-skills/setup-and-cli/SKILL.md` | `fedml --help`, `fedml login`, `fedml run`, `fedml cluster`, `fedml device`, `fedml storage`, `fedml network`, `fedml env`; `fedml.api.run_*`, `cluster_*`, `upload/download` | `python/setup.py`, `python/fedml/cli/cli.py`, `python/fedml/api/__init__.py`, `installation/README.md` |
| package and launch platform jobs | `sub-skills/launch-and-packaging/SKILL.md` | `fedml build`, `fedml launch`, `fedml.api.launch_job`, `launch_job_on_cluster`, `train_build`, `federate_build` | `python/fedml/cli/modules/build.py`, `launch.py`, `python/examples/launch`, `python/tests/smoke_test/cli/build.sh` |
| run centralized, cross-cloud, or LLM training with FedML | `sub-skills/distributed-training/SKILL.md` | `fedml.init`, `load_arguments`, `FedMLRunner`, `data.load`, `model.create`, train scripts/job YAML | `python/examples/centralized`, `python/examples/cross_cloud`, `python/examples/train/llm_train`, `python/fedml/runner.py` |
| run simulation or cross-silo/cross-device federated learning | `sub-skills/federated-learning/SKILL.md` | `run_simulation`, `run_cross_silo_*`, `FedMLRunner`, `FedMLExecutor`, `FedMLAlgorithmFlow`, privacy/security helpers | `python/examples/federate`, `python/fedml/simulation`, `python/fedml/core`, `python/tests/smoke_test/simulation_mpi` |
| create model cards, deploy models, run local or remote inference, stream responses | `sub-skills/model-serving/SKILL.md` | `fedml model`, `fedml.api.model_*`, `FedMLPredictor`, `FedMLInferenceRunner`, `run_model_serving_*` | `python/examples/deploy`, `python/fedml/serving`, `python/fedml/model` |
| compose multi-job DAGs with dependent train/deploy/inference jobs | `sub-skills/workflow-orchestration/SKILL.md` | `Workflow`, `Job`, `WorkflowMLOpsApi`, `TrainJob`, `ModelDeployJob`, `ModelInferenceJob` | `python/fedml/workflow`, `python/fedml/workflow/driver_example` |

## Common task patterns

### 1. Local install or import check

1. Read `references/installation.md`.
2. Install from PyPI or from `python/` editable source.
3. Run:

```bash
python -c "import fedml; print(fedml.__version__)"
fedml --help
fedml version
```

4. If the import path or version is unexpected, run `scripts/check_install.py` and read `references/troubleshooting.md`.

### 2. Platform login and run inspection

1. Read `sub-skills/setup-and-cli/SKILL.md`.
2. Confirm the user wants remote account/device side effects.
3. Use `fedml login` or `fedml.api.fedml_login(api_key)`.
4. Inspect runs/clusters/storage with `fedml run`, `fedml cluster`, and `fedml storage`.
5. Use `fedml network` for connectivity probes. Do not use `fedml diagnosis`; that command name is not exposed in the current CLI.

### 3. Local package preflight before launch

1. Read `sub-skills/launch-and-packaging/SKILL.md`.
2. Validate the job YAML with `sub-skills/launch-and-packaging/scripts/validate_job_yaml.py`.
3. For package-only work, use `fedml build`, `fedml train build`, or `fedml federate build`.
4. For real platform launch, obtain the API key and ask before creating or stopping remote resources.

### 4. Training recipe selection

1. Read `sub-skills/distributed-training/SKILL.md`.
2. If the task is a small local training loop, use the centralized route and `FedMLRunner`.
3. If the task is cross-cloud or MLOps package launch, combine `distributed-training` with `launch-and-packaging`.
4. If the task is LLM training, inspect `python/examples/train/llm_train/job.yaml` patterns but treat full execution as GPU/network/model-data dependent.

### 5. Federated-learning route selection

1. Read `sub-skills/federated-learning/SKILL.md`.
2. Use `backend='sp'` for single-process simulation when possible.
3. Treat MPI/NCCL as optional backends that need separate runtime verification.
4. Do not use Android or IoT examples for this Python skill scope.

### 6. Model serving route selection

1. Read `sub-skills/model-serving/SKILL.md`.
2. Use local `FedMLPredictor`/`FedMLInferenceRunner` for fast, safe inference checks.
3. Use `fedml model create/push/deploy/run` only after clarifying account, endpoint, model-artifact, and remote side-effect requirements.
4. For streaming responses, adapt the streaming predictor pattern rather than treating it as a normal JSON-returning predictor.

### 7. Workflow orchestration route selection

1. Read `sub-skills/workflow-orchestration/SKILL.md`.
2. For local DAG shape checks, use custom `Job` subclasses and `Workflow.add_job`.
3. For real `TrainJob`, `ModelDeployJob`, or `ModelInferenceJob`, expect backend calls, API keys, storage, and remote job state.

## Source-script policy

- Do not run hardcoded smoke scripts with embedded API keys or personal paths.
- Treat Docker/AWS/PDSH scripts under `python/scripts/docker` and `python/scripts/source_code` as reference-only unless the user explicitly asks for that infrastructure setup.
- Treat `python/build_tools/setup_mpi/setup-mpi.sh` as documentation for host MPI requirements, not as a script to execute automatically.
- Prefer bundled safe helpers in this skill over running original repo scripts directly.
