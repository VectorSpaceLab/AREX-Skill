# Pipeline workflow troubleshooting

Use this guide after a user chooses a service-backed FATE-Client Pipeline route. If the failure is about installing or starting services, route to `deployment`; if it is about direct local `fate.ml` launchers, route to `local-launchers`; if it is about `python -m fate.components`, route to `component-runtime`.

## Service is not running or pipeline client is not initialized

Symptoms:

- Pipeline API calls fail before a job is submitted.
- Upload/transform cannot reach FateFlow.
- `pipeline show` or `pipeline site-info` does not report the expected endpoint.
- `fate_flow status` is stopped, missing, or pointed at the wrong home/ip/port.

Checks:

```bash
fate_flow status
pipeline show
pipeline site-info
```

Known command surfaces:

- `fate_flow init --ip <ip> --port <port> --home <workspace>`
- `pipeline init --ip <ip> --port <port> --path <optional-client-config-path>`
- `fate_flow start`, `fate_flow stop`, `fate_flow restart`, `fate_flow version`

Fix route:

1. If FateFlow is not initialized or not started, use `deployment`.
2. If FateFlow is running but `pipeline` points at the wrong IP/port/path, rerun `pipeline init` with the same service endpoint.
3. Do not run deployment shell scripts from this sub-skill; keep this sub-skill at Python pipeline usage level.

## Upload or transform fails

Symptoms:

- `transform_local_file_to_dataframe(...)` cannot find the local file.
- Upload succeeds for one party but not another.
- Later `Reader` says the table is missing.

Checks:

- Use absolute paths for `file=...` in runtime upload calls.
- Run the safe validator before service contact:

```bash
python skills/disco/fate/sub-skills/pipeline-workflows/scripts/validate_upload_config.py \
  path/to/upload_config.yaml
```

- Confirm each item has `file`, `meta`, `table_name`, `namespace`, and either `partitions` or `partition`.
- Confirm `table_name` is copied to Python as `name=...`.
- Confirm `namespace` is exactly the same string used by `Reader`.
- For dense CSV, confirm `delimiter`, `input_format`, `match_id_name`, `head`, and `extend_sid` are correct.

Likely fixes:

- Change relative `file` paths to absolute paths for ad-hoc scripts.
- Re-upload data if the wrong namespace/table name was used.
- Use `extend_sid=True` when the file only has one id column and a PSI workflow needs both sample id and match id.
- Use `sample_id_name` and `extend_sid=False` only when the file already contains a sample-id column.

## Reader namespace or table mismatch

Symptoms:

- `Reader` cannot resolve table.
- Training reaches `Reader`/`PSI` and fails with missing data.
- Prediction fails although training succeeded.

Checks:

```python
reader_0.guest.task_parameters(namespace="experiment", name="breast_hetero_guest")
reader_0.hosts[0].task_parameters(namespace="experiment", name="breast_hetero_host")
```

- `namespace` and `name` must match upload exactly.
- Some examples add a namespace suffix (`namespace=f"experiment{namespace}"`). If a script appends a suffix, upload must use the same suffix.
- `table_name` in YAML maps to `name` in `Reader.task_parameters(...)`.
- Multi-host readers need host indexes that exist in `set_parties(host=[...])`.

Fix:

- Correct the Reader mapping or re-upload with the intended table names.
- Keep a single table mapping record for train and predict flows. Most prediction failures are caused by using the training table names for upload but different names in the fresh prediction `Reader`.

## Party mismatch

Symptoms:

- `reader.hosts[0]` or `reader.hosts[[0, 1]]` mapping fails.
- A component complains about role/party availability.
- Evaluation metrics appear at the wrong role or not at all.

Checks:

- Single-host hetero example:

```python
pipeline = FateFlowPipeline().set_parties(guest="9999", host="10000")
reader_0.hosts[0].task_parameters(namespace="experiment", name="breast_hetero_host")
```

- Multi-host example:

```python
hosts = ["10000", "9999"]
pipeline = FateFlowPipeline().set_parties(guest="9999", host=hosts)
reader_0.hosts[[0, 1]].task_parameters(namespace="experiment", name="breast_hetero_host")
```

- Arbiter examples:

```python
pipeline = FateFlowPipeline().set_parties(guest="9999", host="10000", arbiter="10000")
```

Fix:

- Match `set_parties(...)` to every component's `runtime_parties` and Reader host indexing.
- Use `runtime_parties=dict(guest=guest, host=host)` when examples scope a component to only selected parties.
- For evaluation in hetero models, examples often set `runtime_parties=dict(guest=guest)` because labels/metrics live at guest.

## PSI or id alignment issues

Symptoms:

- PSI outputs too few/no rows.
- Hetero model trains with unexpected row counts.
- Data split/evaluation receives empty data.

Checks:

- Guest and host tables must share overlapping `match_id_name` values.
- FATE 2.x docs note uploaded data should have sample id and match id.
- If source files only contain one id column, use upload `extend_sid=True`.
- If files already contain a sample-id column, set `sample_id_name` and `extend_sid=False`.
- Avoid changing id/meta fields between training and prediction uploads.

Fix:

- Revalidate and re-upload both guest and host data with aligned `match_id_name`/SID settings.
- Re-run `Reader + PSI` as a small preflight pipeline before training expensive components.

## Component wiring and artifact-name errors

Symptoms:

- Component constructor accepts the object but compile/fit fails on missing input artifacts.
- Downstream component receives a model artifact instead of data, or train data instead of test data.

Checks:

- `Reader` output: `reader_0.outputs["output_data"]`.
- `PSI` output: `psi_0.outputs["output_data"]`.
- `DataSplit` outputs: `train_output_data`, `validate_output_data`, `test_output_data`.
- Many model components output `train_output_data` and `output_model`.
- `Evaluation` expects `input_datas=[...]`, not a single `input_data` argument.
- `FeatureScale` and selection/binnning often use one component to fit and a second with `input_model` to apply to test data.

Fix:

- Rebuild the DAG in the documented order: Reader -> PSI -> preprocessing -> model -> Evaluation.
- Use `component.outputs[...]` artifact names from the verified examples/catalog; do not invent aliases.
- When adding a model warm-start or prediction component, use `input_model` or `warm_start_model` as shown by the component catalog.

## Training is slow or expensive

Symptoms:

- Service-backed examples appear to hang or exceed the user's budget.
- NN/SecureBoost examples consume more resources than expected.

Guidance:

- Pipeline examples are service-backed and normally skipped during skill generation/env prep.
- Confirm user budget, dataset size, component choices, and service capacity before running full training.
- Prefer a minimal Reader+PSI or upload validator preflight first.
- CPU was the minimum verified backend for drafting; GPU/DeepSpeed remains optional and unverified here.

## Model dump/load/deploy problems

Symptoms:

- `FateFlowPipeline.load_model(...)` cannot find a model.
- `deploy(...)` fails because the named component is absent.
- Prediction pipeline compiles but fails at the deployed component input.

Checks:

- Call `pipeline.dump_model("./pipeline.pkl")` after a successful `fit()`.
- Reload with `FateFlowPipeline.load_model("./pipeline.pkl")`.
- Deploy component attributes that were present in the training pipeline, e.g. `pipeline.psi_0`, `pipeline.hetero_secureboost_0`, `pipeline.selection_0`, `pipeline.scale_0`, `pipeline.sshe_lr_0`, `pipeline.homo_nn_0`.
- Do not deploy the training `Reader`; create a new Reader for prediction.

Fix patterns:

- Hetero SecureBoost:

```python
trained.deploy([trained.psi_0, trained.hetero_secureboost_0])
deployed = trained.get_deployed_pipeline()
deployed.psi_0.input_data = reader_1.outputs["output_data"]
```

- Feature engineering + LR:

```python
trained.deploy([trained.psi_0, trained.selection_0, trained.scale_0, trained.sshe_lr_0])
deployed = trained.get_deployed_pipeline()
deployed.psi_0.input_data = reader_1.outputs["output_data"]
```

- Homo NN:

```python
trained.deploy([trained.homo_nn_0])
deployed = trained.get_deployed_pipeline()
deployed.homo_nn_0.test_data = reader_1.outputs["output_data"]
```

## Prediction table/schema mismatch

Symptoms:

- Training succeeds, but prediction fails after attaching a new Reader.
- Deployed preprocessing/model rejects prediction data.

Checks:

- Prediction table names and namespaces must exist in FateFlow.
- Prediction guest/host schema must match the schema expected by deployed preprocessing/model components.
- Hetero prediction still needs aligned match ids for `PSI` when deployed `psi_0` is reused.
- If training used `FeatureScale`, `HeteroFeatureSelection`, or `HeteroFeatureBinning`, deploy the trained preprocessing components and feed prediction data through them.

Fix:

- Re-upload prediction data with the same meta conventions as training.
- Attach the new Reader output to the first deployed component, not directly to the model unless the training deploy path does that.
- Keep the deployment list ordered from earliest reusable transform to final model.
