# FATE package overview

This skill targets FATE 2.2.x, a federated-learning platform with both service-backed workflows and service-free local module APIs. Use this reference to choose the correct installed surface before routing into a sub-skill.

## Installed package surfaces

| Surface | Import / command | Primary owner | Notes |
| --- | --- | --- | --- |
| Core Python package | `import fate` from `pyfate==2.2.0` | root, local launchers, component runtime | Verified package version is 2.2.0. Provides `fate.arch`, `fate.ml`, and `python -m fate.components`. |
| Rust-backed utilities | `import fate_utils` from `fate_utils==0.1.0` | root, local launchers, component runtime | Required by the package. If it is missing, fix the install before debugging higher-level APIs. |
| Component CLI | `python -m fate.components` | `sub-skills/component-runtime/` | Safe inspection commands include `component list`, `component desc`, `component task-schema`, and `component artifact-type`. The schema command is hyphenated: `task-schema`, not `task_schema`. |
| FateFlow service CLI | `fate_flow` | `sub-skills/deployment/` | Verified command group includes `init`, `restart`, `start`, `status`, `stop`, and `version`. It manages or checks services and is not needed for local launchers. |
| Pipeline client CLI | `pipeline` | `sub-skills/deployment/`, `sub-skills/pipeline-workflows/` | Verified command group includes `init`, `show`, and `site-info`. It is used after the FateFlow client endpoint is known. |
| Pipeline Python API | `fate_client.pipeline.FateFlowPipeline` | `sub-skills/pipeline-workflows/` | Verified methods include `set_parties`, `transform_local_file_to_dataframe`, `add_tasks`, `compile`, `fit`, `predict`, `dump_model`, `deploy`, `get_deployed_pipeline`, `get_task_info`, and `load_model`. |
| Local launcher API | `fate.arch.launchers`, `fate.arch.dataframe`, `fate.ml` | `sub-skills/local-launchers/` | Service-free local simulation. Uses local multiprocessing and direct module APIs instead of FateFlow tables/jobs. |

## Install footprint guidance

- For component inspection and local launcher authoring, start with `pyfate==2.2.0` and its dependency `fate_utils==0.1.0`.
- For service-backed Pipeline workflows or deployment checks, include the client/service packages, for example `fate_client[fate,fate_flow]==2.2.0` when resolving from PyPI.
- If component listing fails with `pkg_resources` missing, install or pin a `setuptools` release that still provides `pkg_resources`; construction was verified with `setuptools==80.9.0`.
- Use `scripts/check_fate_install.py` from the root skill to summarize the current environment before running workflow-specific commands.

## Backend and service boundaries

- The verified construction baseline was CPU-only. CPU imports, CPU PyTorch patterns, local component CLI probes, and non-training helper checks are in scope.
- GPUs were visible on the construction host, but GPU/DeepSpeed behavior was not verified. Do not present GPU, DeepSpeed-on-Eggroll, Spark, Eggroll cluster, RabbitMQ, Pulsar, or vendor accelerator flows as verified defaults.
- FateFlow-backed Pipeline jobs require a live service, initialized client, uploaded/registered data tables, party ids, and execution budget.
- Local launchers do not require FateFlow or Docker, but they may spawn one process per party and can become heavy once actual training is launched.
- Component CLI descriptor/schema probes do not require FateFlow and are the right first check for component names, stages, role support, and artifact shapes.

## Capability ownership

- `sub-skills/deployment/` owns install/deployment paths, FateFlow service startup/status, Docker/Compose, host package deployment, ports, SSH, and service smoke checks.
- `sub-skills/pipeline-workflows/` owns service-backed `FateFlowPipeline` recipes: upload, Reader/PSI, preprocessing, model DAGs, evaluation, deploy/predict, and upload-config validation.
- `sub-skills/local-launchers/` owns service-free direct `fate.ml` launchers, `launch(run_fn)`, `create_context`, `CSVReader`/`PandasReader`/`TableReader`, and local party layouts.
- `sub-skills/component-runtime/` owns `python -m fate.components` command spellings, descriptors, task schema, artifact type introspection, and custom component discovery.

## Source evidence boundaries

The source snapshot used for this skill included the top-level docs, `python/fate`, `rust/fate_utils`, examples, deployment docs/scripts, package metadata, and requirements. Repository submodules such as `fate_client`, `fate_flow`, `fate_board`, `fate_test`, `eggroll`, and `fate_client`-adjacent service packages were uninitialized in the checkout and are treated as installed external dependencies rather than local source evidence.
