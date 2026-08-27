# FATE-Client pipeline workflow recipes

This reference covers **service-backed** FATE-Client Pipeline usage. It assumes `fate_client==2.2.0` and a running FateFlow service. If a service is not initialized or reachable, use the `deployment` sub-skill before trying any recipe here. If the user wants to run FATE modules without FateFlow, use `local-launchers` instead.

## 1. Service and package preflight

Minimum verified package facts for this skill:

- `pyfate==2.2.0` provides the import package `fate`.
- `fate_client==2.2.0` and `fate_flow==2.2.0` provide the service-backed client surfaces.
- `fate_utils==0.1.0` is present in the inspection environment.
- The checked torch build was CPU-only (`torch==2.3.1+cpu`, `torch.cuda.is_available() == False`); do not promise GPU/DeepSpeed behavior from this sub-skill.

Documented service setup shape:

```bash
python -m pip install -U pip
python -m pip install 'fate_client[fate,fate_flow]==2.2.0'

mkdir -p fate_workspace
fate_flow init --ip 127.0.0.1 --port 9380 --home "$(pwd)/fate_workspace"
pipeline init --ip 127.0.0.1 --port 9380
fate_flow start
fate_flow status
```

Verified command surfaces:

- `fate_flow --help` commands: `init`, `restart`, `start`, `status`, `stop`, `version`.
- `pipeline --help` commands: `init`, `show`, `site-info`.
- `fate_flow init --help` options: `--ip`, `--port`, `--home`.
- `pipeline init --help` options: `--ip`, `--port`, `--path`.

Pipeline examples are service-backed and are normally skipped during skill generation/environment prep. Run them only after the user confirms a live service, party ids, uploaded tables, and an execution budget.

## 2. Upload or transform local files into FATE tables

Use `FateFlowPipeline.transform_local_file_to_dataframe(...)` after selecting the local site. The quick starts and upload examples use `local="0"`, `set_site_role("local")`, and `set_site_party_id("0")` for local file transformation.

```python
from pathlib import Path
from fate_client.pipeline import FateFlowPipeline

base = Path("/abs/path/to/data")

data_pipeline = FateFlowPipeline().set_parties(local="0")
data_pipeline.set_site_role("local")
data_pipeline.set_site_party_id("0")

guest_meta = {
    "delimiter": ",",
    "dtype": "float64",
    "input_format": "dense",
    "label_type": "int64",
    "label_name": "y",
    "match_id_name": "id",
    "match_id_range": 0,
    "tag_value_delimiter": ":",
    "tag_with_value": False,
    "weight_type": "float64",
}
host_meta = {
    "delimiter": ",",
    "dtype": "float64",
    "input_format": "dense",
    "match_id_name": "id",
    "match_id_range": 0,
    "tag_value_delimiter": ":",
    "tag_with_value": False,
    "weight_type": "float64",
}

data_pipeline.transform_local_file_to_dataframe(
    file=str(base / "breast_hetero_guest.csv"),
    namespace="experiment",
    name="breast_hetero_guest",
    meta=guest_meta,
    head=True,
    extend_sid=True,
)
data_pipeline.transform_local_file_to_dataframe(
    file=str(base / "breast_hetero_host.csv"),
    namespace="experiment",
    name="breast_hetero_host",
    meta=host_meta,
    head=True,
    extend_sid=True,
)
```

Upload notes:

- FATE 2.x PSI workflows expect both sample id and match id. If source data only has one id column, the examples set `extend_sid=True`. If a file already has a sample-id column, the SID example uses `sample_id_name="id"` and `extend_sid=False`.
- The examples use namespace `experiment` and table names matching file stems, such as `breast_hetero_guest` and `breast_hetero_host`.
- Before a service upload, run the bundled safe validator on YAML upload configs:

```bash
python skills/disco/fate/sub-skills/pipeline-workflows/scripts/validate_upload_config.py \
  path/to/upload_config.yaml
```

The validator only parses files and summarizes shape; it does not contact FateFlow.

## 3. Reader + PSI alignment

A `Reader` maps uploaded FATE tables into the pipeline DAG. For hetero tasks, add `PSI` to align samples by match id.

```python
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import Reader, PSI

guest = "9999"
host = "10000"

pipeline = FateFlowPipeline().set_parties(guest=guest, host=host)

reader_0 = Reader("reader_0")
reader_0.guest.task_parameters(namespace="experiment", name="breast_hetero_guest")
reader_0.hosts[0].task_parameters(namespace="experiment", name="breast_hetero_host")

psi_0 = PSI("psi_0", input_data=reader_0.outputs["output_data"])

pipeline.add_tasks([reader_0, psi_0])
pipeline.compile()
pipeline.fit()
```

Multi-host pattern:

```python
hosts = ["10000", "9999"]
pipeline = FateFlowPipeline().set_parties(guest="9999", host=hosts)
reader_0 = Reader("reader_0")
reader_0.guest.task_parameters(namespace="experiment", name="breast_hetero_guest")
reader_0.hosts[[0, 1]].task_parameters(namespace="experiment", name="breast_hetero_host")
psi_0 = PSI("psi_0", input_data=reader_0.outputs["output_data"])
```

Use a host list whenever the workflow references `reader.hosts[1]` or `reader.hosts[[0, 1]]`. A single string host id only supports `reader.hosts[0]`.

## 4. Add preprocessing and feature engineering

Common service-backed DAG order:

1. `Reader` for uploaded tables.
2. `PSI` for hetero sample alignment.
3. Optional split/sample/statistics/feature-engineering components.
4. Model component.
5. `Evaluation` for metrics.

Example feature-engineering chain from the model-building quick start:

```python
from fate_client.pipeline.components.fate import (
    DataSplit,
    FeatureScale,
    HeteroFeatureBinning,
    HeteroFeatureSelection,
    PSI,
    Reader,
    SSHELR,
    Evaluation,
    Statistics,
)

reader_0 = Reader("reader_0")
reader_0.guest.task_parameters(namespace="experiment", name="breast_hetero_guest")
reader_0.hosts[0].task_parameters(namespace="experiment", name="breast_hetero_host")

psi_0 = PSI("psi_0", input_data=reader_0.outputs["output_data"])

data_split_0 = DataSplit(
    "data_split_0",
    input_data=psi_0.outputs["output_data"],
    train_size=0.7,
    validate_size=0.3,
    test_size=None,
    stratified=True,
)

binning_0 = HeteroFeatureBinning(
    "binning_0",
    train_data=data_split_0.outputs["train_output_data"],
    method="bucket",
    n_bins=10,
)
statistics_0 = Statistics(
    "statistics_0",
    input_data=data_split_0.outputs["train_output_data"],
    metrics=["min", "max", "25%", "mean", "median"],
)
selection_0 = HeteroFeatureSelection(
    "selection_0",
    method=["iv", "statistics", "manual"],
    train_data=data_split_0.outputs["train_output_data"],
    input_models=[binning_0.outputs["output_model"], statistics_0.outputs["output_model"]],
    iv_param={"metrics": "iv", "filter_type": "top_k", "threshold": 6, "select_federated": True},
    statistic_param={"metrics": ["max", "mean"], "filter_type": "top_k", "threshold": 5, "take_high": False},
    manual_param={"keep_col": ["x0", "x1"]},
)
selection_1 = HeteroFeatureSelection(
    "selection_1",
    test_data=data_split_0.outputs["validate_output_data"],
    input_model=selection_0.outputs["train_output_model"],
)
scale_0 = FeatureScale("scale_0", train_data=selection_0.outputs["train_output_data"], method="min_max")
scale_1 = FeatureScale(
    "scale_1",
    test_data=selection_1.outputs["test_output_data"],
    input_model=scale_0.outputs["output_model"],
)

sshe_lr_0 = SSHELR(
    "sshe_lr_0",
    train_data=selection_0.outputs["train_output_data"],
    validate_data=scale_0.outputs["test_output_data"],
    epochs=3,
)
evaluation_0 = Evaluation(
    "evaluation_0",
    input_datas=[sshe_lr_0.outputs["train_output_data"]],
    default_eval_setting="binary",
    runtime_parties=dict(guest="9999"),
)
```

Do not invent output names. Use the names shown by the component catalog or by the component object already in the DAG, e.g. `reader_0.outputs["output_data"]`, `data_split_0.outputs["train_output_data"]`, and model `outputs["train_output_data"]`/`outputs["output_model"]` where available.

## 5. Train and evaluate hetero SecureBoost

The quick-start SecureBoost flow is compact and useful for binary hetero classification:

```python
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import Evaluation, HeteroSecureBoost, PSI, Reader

pipeline = FateFlowPipeline().set_parties(guest="9999", host="10000")

reader_0 = Reader("reader_0")
reader_0.guest.task_parameters(namespace="experiment", name="breast_hetero_guest")
reader_0.hosts[0].task_parameters(namespace="experiment", name="breast_hetero_host")

psi_0 = PSI("psi_0", input_data=reader_0.outputs["output_data"])
hetero_secureboost_0 = HeteroSecureBoost(
    "hetero_secureboost_0",
    num_trees=1,
    max_depth=5,
    train_data=psi_0.outputs["output_data"],
    validate_data=psi_0.outputs["output_data"],
)
evaluation_0 = Evaluation(
    "evaluation_0",
    runtime_parties=dict(guest="9999"),
    metrics=["auc"],
    input_datas=[hetero_secureboost_0.outputs["train_output_data"]],
)

pipeline.add_tasks([reader_0, psi_0, hetero_secureboost_0, evaluation_0])
pipeline.compile()
pipeline.fit()

print(pipeline.get_task_info("hetero_secureboost_0").get_output_model())
print(pipeline.get_task_info("evaluation_0").get_output_metric())
pipeline.dump_model("./pipeline.pkl")
```

SecureBoost variants seen in examples:

- Binary classification: default `objective="binary:bce"`, `metrics=["auc"]`.
- Multi-class: `objective="multi:ce"`, set `num_class` to the class count.
- Regression: `objective="regression:l2"`, use regression evaluation metrics/settings.
- Optional encrypted training parameters appear in examples as `he_param={"kind": "paillier", "key_length": 1024}`.

## 6. Homo NN pipeline shape

Homo NN is still service-backed in this sub-skill. It uses pipeline NN configuration helpers and PyTorch modules, but it is not the same as service-free local launcher execution.

```python
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import Evaluation, Reader
from fate_client.pipeline.components.fate.homo_nn import HomoNN, get_config_of_default_runner
from fate_client.pipeline.components.fate.nn.algo_params import FedAVGArguments, TrainingArguments
from fate_client.pipeline.components.fate.nn.torch import nn, optim
from fate_client.pipeline.components.fate.nn.torch.base import Sequential

pipeline = FateFlowPipeline().set_parties(guest="9999", host="10000", arbiter="10000")

reader_0 = Reader("reader_0", runtime_parties=dict(guest="9999", host="10000"))
reader_0.guest.task_parameters(namespace="experiment", name="breast_homo_guest")
reader_0.hosts[0].task_parameters(namespace="experiment", name="breast_homo_host")

conf = get_config_of_default_runner(
    algo="fedavg",
    model=Sequential(nn.Linear(30, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid()),
    loss=nn.BCELoss(),
    optimizer=optim.Adam(lr=0.01),
    training_args=TrainingArguments(num_train_epochs=5, per_device_train_batch_size=64),
    fed_args=FedAVGArguments(),
    task_type="binary",
)

homo_nn_0 = HomoNN("homo_nn_0", runner_conf=conf, train_data=reader_0.outputs["output_data"])
evaluation_0 = Evaluation(
    "evaluation_0",
    runtime_parties=dict(guest="9999", host="10000"),
    metrics=["auc"],
    input_datas=[homo_nn_0.outputs["train_output_data"]],
)
pipeline.add_tasks([reader_0, homo_nn_0, evaluation_0])
pipeline.compile()
pipeline.fit()
```

The inspection environment only verified CPU torch. Treat GPU and DeepSpeed as optional advanced topics until separately verified.

## 7. Dump, deploy, and predict

Use the trained pipeline object to choose which components become inference-time reusable tasks. Then attach a fresh Reader to a prediction pipeline.

Hetero SecureBoost predict shape:

```python
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import Reader

predict_pipeline = FateFlowPipeline()
trained = FateFlowPipeline.load_model("./pipeline.pkl")

trained.deploy([trained.psi_0, trained.hetero_secureboost_0])
deployed_pipeline = trained.get_deployed_pipeline()

reader_1 = Reader("reader_1")
reader_1.guest.task_parameters(namespace="experiment", name="breast_hetero_guest")
reader_1.hosts[0].task_parameters(namespace="experiment", name="breast_hetero_host")

deployed_pipeline.psi_0.input_data = reader_1.outputs["output_data"]

predict_pipeline.add_tasks([reader_1, deployed_pipeline])
predict_pipeline.compile()
predict_pipeline.predict()
```

Feature-engineering predict shape:

```python
trained = FateFlowPipeline.load_model("./pipeline.pkl")
trained.deploy([trained.psi_0, trained.selection_0, trained.scale_0, trained.sshe_lr_0])
deployed_pipeline = trained.get_deployed_pipeline()
# attach reader_1 as above, then:
deployed_pipeline.psi_0.input_data = reader_1.outputs["output_data"]
```

Homo NN predict shape:

```python
trained = FateFlowPipeline.load_model("./pipeline.pkl")
trained.deploy([trained.homo_nn_0])
deployed_pipeline = trained.get_deployed_pipeline()
# attach reader_1 as above, then:
deployed_pipeline.homo_nn_0.test_data = reader_1.outputs["output_data"]
```

Deploy/predict checks:

- Use the same model file produced by `dump_model`.
- Deploy every preprocessing component that must run again at inference time; do not deploy `Reader` itself.
- Wire the fresh Reader output to the first deployed component input (`input_data` for PSI, `test_data` for HomoNN examples).
- Keep table namespace/name and party ids consistent with the uploaded prediction data.
