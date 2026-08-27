# Python API Reference

## Purpose

Read this when writing Python code against FedML instead of only using the CLI. Network-bound API calls still require a FedML/TensorOpera account and API key.

## Top-level package APIs

| API | Verified signature or shape | Use |
| --- | --- | --- |
| `fedml.__version__` | string, current snapshot `0.8.30` | confirm import/version |
| `fedml.init(args=None, check_env=True, should_init_logs=True)` | initializes global environment, multiprocessing, seeds, and MLOps setup | call before training/simulation/serving workflows when using FedML runtime args |
| `fedml.load_arguments(training_type=None, comm_backend=None)` | loads FedML YAML/CLI arguments | build the `args` object expected by examples |
| `fedml.get_env_version()` / `fedml.set_env_version(value)` | global backend version helper | align local/dev/test/release backend selection with CLI `-v` |
| `fedml.run_simulation(backend='sp')` | simulation launcher | use `sp` for single-process simulation; MPI/NCCL need matching runtime |
| `fedml.run_cross_silo_client()` / `fedml.run_cross_silo_server()` | cross-silo FL entry points | role-specific federated-learning processes |
| `fedml.run_model_serving_server()` / `fedml.run_model_serving_client()` | serving entry points | model-serving workflows |
| `fedml.device.get_device(args)` | returns target device from args | select CPU/GPU for training/serving |
| `fedml.data.load(args)` | dataset loader dispatcher | load datasets declared by FedML args |
| `fedml.model.create(args, output_dim)` | model factory dispatcher | create supported models from FedML args |
| `fedml.FedMLRunner(args, device, dataset, model, ...)` | runner object | orchestrates local or distributed training once args/data/model are ready |

## Public `fedml.api` helpers

These APIs generally mirror CLI operations and contact backend services unless stated otherwise.

| API | Signature shape | Use |
| --- | --- | --- |
| `fedml.api.fedml_login(api_key=None)` | returns login error code/message | login from Python |
| `fedml.api.launch_job(yaml_file, api_key=None, resource_id=None, device_server=None, device_edges=None, feature_entry_point=FeatureEntryPoint.FEATURE_ENTRYPOINT_API)` | returns `LaunchResult` with `result_code`, `result_msg`, `run_id`, `project_id`, optional `inner_id` | launch a job from a YAML file |
| `fedml.api.launch_job_on_cluster(yaml_file, cluster, api_key=None, resource_id=None, device_server=None, device_edges=None, feature_entry_point=...)` | launch on named cluster | cluster-targeted launch |
| `fedml.api.run_stop(run_id, platform='falcon', api_key=None)` | bool-like | stop a run |
| `fedml.api.run_list(run_name=None, run_id=None, platform='falcon', api_key=None)` | `FedMLRunModelList` | list runs |
| `fedml.api.run_status(run_name=None, run_id=None, platform='falcon', api_key=None)` | run list/status tuple | inspect a run |
| `fedml.api.run_logs(run_id, page_num=1, page_size=10, need_all_logs=False, platform='falcon', api_key=None)` | `RunLogResult` | fetch run logs |
| `fedml.api.cluster_list(cluster_names=(), api_key=None)` | `FedMLClusterModelList` | list clusters |
| `fedml.api.cluster_exists(cluster_name, api_key=None)` | bool | existence check |
| `fedml.api.cluster_status(cluster_name, api_key=None)` | status/model-list tuple | inspect cluster state |
| `fedml.api.cluster_start(...)`, `cluster_stop(...)`, `cluster_kill(...)`, `cluster_autostop(...)` | cluster management | start/stop/kill/autostop clusters |
| `fedml.api.upload(data_path, api_key=None, service='R2', name=None, description=None, metadata=None, show_progress=False, ...)` | `FedMLResponse` | upload data or artifacts |
| `fedml.api.download(data_name, api_key=None, service='R2', dest_path=None, show_progress=True)` | `FedMLResponse` | download data or artifacts |
| `fedml.api.list_storage_objects(api_key=None)` | `FedMLResponse` | list storage objects |
| `fedml.api.get_storage_metadata(data_name, api_key=None)` | `FedMLResponse` | inspect storage metadata |
| `fedml.api.delete(data_name, service, api_key=None)` | response/bool-like | delete stored object |
| `fedml.api.fedml_build(platform, type, source_folder, entry_point, config_folder, dest_folder, ignore)` | build result | build a FedML package programmatically |
| `fedml.api.model_create(name, model, model_config)` | CLI-equivalent | create a local model card |
| `fedml.api.model_package(name)` | package a local model card | package for deploy |
| `fedml.api.model_push(name, model_storage_url, api_key, tag_names, model_id, model_version)` | push a model card | remote model registry |
| `fedml.api.model_deploy(name, endpoint_name, endpoint_id, local, master_ids, worker_ids, use_remote)` | deploy model | local/on-prem/cloud deployment |
| `fedml.api.model_run(endpoint_id, json_string)` | run inference request | query endpoint |
| `fedml.api.train_build(job_yaml_file, dest_folder)` | build train package from job YAML | local package preparation |
| `fedml.api.federate_build(job_yaml_file, dest_folder)` | build federate package from job YAML | FL package preparation |

## Observability APIs

`fedml.mlops` is the runtime logging surface. Common patterns in examples/tests include:

```python
import fedml

fedml.mlops.log({"accuracy": 0.9, "loss": 0.1})
fedml.mlops.log_metric("accuracy", 0.9, step=1)
fedml.mlops.log_sys_perf(args)
```

Treat MLOps logging as backend-bound unless running in an isolated/offline test. Avoid hardcoding API keys in scripts.

## Serving APIs

| API | Use |
| --- | --- |
| `fedml.serving.FedMLPredictor` | subclass and implement `predict` for local or deployed inference |
| `fedml.serving.FedMLInferenceRunner` | wraps a `FedMLPredictor` and starts the FastAPI/serving process |
| `fedml.serving.FedMLClient` / `FedMLServer` | client/server serving helpers used internally by serving examples |

See `sub-skills/model-serving/SKILL.md` for local predictor and streaming patterns.

## Workflow APIs

| API | Use |
| --- | --- |
| `fedml.workflow.Job` | abstract base class for workflow nodes; implement `run`, `status`, and `kill` |
| `fedml.workflow.JobStatus` | enum: `PROVISIONING`, `RUNNING`, `FINISHED`, `FAILED`, `UNDETERMINED` |
| `fedml.workflow.Workflow(name, loop=False, api_key=None, workflow_type=...)` | dependency DAG runner for `Job` instances |
| `Workflow.add_job(job, dependencies=None)` | add a node and dependency list |
| `Workflow.run()` | runs jobs in topological order and updates backend workflow state |
| `fedml.workflow.WorkflowMLOpsApi` | backend workflow create/update/status APIs |
| `TrainJob`, `ModelDeployJob`, `ModelInferenceJob` | job wrappers that inject inputs/outputs and launch backend jobs |

For purely local smoke tests, use a custom `Job` subclass and avoid `Workflow.run()` unless backend calls are mocked or credentials are configured.

## Federated learning helper classes

Core FL examples use these public classes and concepts:

- `FedMLRunner` with custom `client_trainer` and `server_aggregator`.
- `FedMLExecutor` for executable algorithm steps.
- `FedMLAlgorithmFlow` for ordered/fedavg-like flow composition.
- `Params` for shared state across executor steps.
- `FedMLAttacker`, `FedMLDefender`, and differential privacy helpers for advanced privacy/security examples.

See `sub-skills/federated-learning/SKILL.md` before using these APIs; backend choice (`sp`, MPI, NCCL, cross-silo) changes initialization requirements.
