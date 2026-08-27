---
name: pipeline-workflows
description: "Service-backed FATE-Client Pipeline workflows for data upload,
  Reader/PSI, preprocessing, model training, evaluation, deploy/predict, and
  upload-config validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# pipeline-workflows

Use this sub-skill when a user wants to author, adapt, or debug a **service-backed FATE-Client Pipeline** workflow: upload local data into FATE storage, construct Reader/PSI and downstream components, train/evaluate a model, dump/deploy it, run prediction, or validate example upload configuration shape before contacting a service.

## Route here for

- Uploading CSV/example data with `FateFlowPipeline.transform_local_file_to_dataframe(...)` and mapping it to FATE table `namespace`/`name` pairs.
- Building pipeline DAGs with `Reader`, `PSI`, `DataSplit`, `FeatureScale`, `HeteroFeatureBinning`, `HeteroFeatureSelection`, `HeteroSecureBoost`, `HomoLR`, `HomoNN`, `HeteroNN`, `SSHELR`, `SSHELinR`, `CoordinatedLR`, `CoordinatedLinR`, `Evaluation`, `Union`, and example-backed statistics/sample/correlation components.
- Handling table naming, namespace conventions, guest/host/arbiter party ids, and multi-host `reader.hosts[...]` mapping.
- Saving and reusing trained pipelines with `dump_model`, `load_model`, `deploy`, `get_deployed_pipeline`, and `predict`.
- Safely checking upload-config YAML structure without contacting FateFlow.

## Route elsewhere

- FateFlow service installation/startup, Docker/host deployment, port conflicts, or `fate_flow`/`pipeline init` setup: use `../deployment/SKILL.md`.
- Service-free direct module execution with `fate.arch.launchers` or `fate.ml`: use `../local-launchers/SKILL.md`.
- Low-level `python -m fate.components` CLI descriptors, `task-schema`, custom component internals, or component execution configs: use `../component-runtime/SKILL.md`.

## Operating constraints

- These workflows require a running FateFlow service and initialized pipeline client. The verified CLI surfaces are `fate_flow init|restart|start|status|stop|version` and `pipeline init|show|site-info`; `fate_flow init` accepts `--ip`, `--port`, `--home`, and `pipeline init` accepts `--ip`, `--port`, `--path`.
- The inspected package set was `pyfate==2.2.0` (`import fate`), `fate_client==2.2.0`, `fate_flow==2.2.0`, and `fate_utils==0.1.0`. Treat GPU and DeepSpeed as optional and unverified here; the minimum verified drafting/inspection backend is CPU.
- Service-backed training and upload examples are normally **not run** during skill generation or environment preparation. Use them as recipes unless the user supplies a live FateFlow service, uploaded data, party ids, and an execution budget.
- Do not route deployment shell scripts or service mutation into this sub-skill. Keep runtime actions at the Python pipeline API level after service prerequisites are satisfied.

## Fast workflow map

1. **Service gate**: confirm FateFlow is initialized/running and pipeline is initialized. If not, route to `deployment`.
2. **Data gate**: validate upload configs with `scripts/validate_upload_config.py`; then upload/transform local files using `FateFlowPipeline().set_parties(local="0")` and `transform_local_file_to_dataframe(...)`.
3. **Reader/PSI gate**: construct `Reader` with exact `namespace`/`name` for each role; add `PSI` for hetero alignment when parties have overlapping match ids.
4. **Feature/model DAG**: choose preprocessing and model components from `references/component-catalog.md`, wire outputs by explicit artifact names, then `add_tasks`, `compile`, and `fit`.
5. **Inspect/save**: use `get_task_info(task_name)` for metrics/models and `dump_model(file_path)` for reuse.
6. **Deploy/predict**: reload with `FateFlowPipeline.load_model(file_path)`, call `deploy([...])` on the trained components that should be reused, attach a fresh `Reader`, then build a prediction pipeline and call `predict()`.

## Bundled references and helper

- `references/pipeline-workflows.md` — stepwise upload, Reader/PSI, train/evaluate, deploy/predict recipes.
- `references/component-catalog.md` — component cheat sheet with verified method/constructor call shapes and common use cases.
- `references/data-formats.md` — table naming, namespaces, role conventions, upload YAML fields, and sample/match id rules.
- `references/troubleshooting.md` — service, table/namespace, party, model, deploy, and predict diagnostics.
- `scripts/validate_upload_config.py` — local YAML parser/validator; it never contacts FateFlow.
