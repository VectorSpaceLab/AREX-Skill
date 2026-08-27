# Tracking and Registry Workflows

## Local Tracking Smoke Pattern

Use this pattern when a user asks for a minimal, safe tracking example or when diagnosing whether MLflow can write runs locally.

```python
import tempfile
from pathlib import Path

import mlflow

with tempfile.TemporaryDirectory(prefix="mlflow-tracking-") as tmp:
    tracking_dir = Path(tmp) / "mlruns"
    mlflow.set_tracking_uri(tracking_dir.as_uri())
    experiment = mlflow.set_experiment("local-smoke")

    with mlflow.start_run(run_name="smoke") as run:
        mlflow.log_param("model", "baseline")
        mlflow.log_metric("accuracy", 0.91, step=1)
        out = Path(tmp) / "outputs"
        out.mkdir()
        (out / "note.txt").write_text("hello mlflow\n", encoding="utf-8")
        mlflow.log_artifacts(str(out), artifact_path="outputs")

    rows = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="params.model = 'baseline'",
        output_format="list",
    )
    assert rows[0].info.run_id == run.info.run_id
```

For an executable bundled version, use `scripts/tracking_smoke.py`.

## Fluent API vs Client API

Use fluent API when code is inside a training workflow:

```python
import mlflow

mlflow.set_experiment("fraud-detection")
with mlflow.start_run(run_name="rf-depth-8"):
    mlflow.log_params({"model": "RandomForest", "max_depth": 8})
    for step, score in enumerate([0.71, 0.78, 0.82]):
        mlflow.log_metric("val_auc", score, step=step)
    mlflow.set_tag("owner", "risk-team")
```

Use `MlflowClient` when operating on IDs, writing from service code, paging, or avoiding global active-run state:

```python
import mlflow
from mlflow import MlflowClient

client = MlflowClient(tracking_uri=mlflow.get_tracking_uri())
experiment = client.get_experiment_by_name("fraud-detection")
if experiment is None:
    experiment_id = client.create_experiment("fraud-detection")
else:
    experiment_id = experiment.experiment_id

run = client.create_run(experiment_id, run_name="service-eval")
client.log_param(run.info.run_id, "model", "candidate")
client.log_metric(run.info.run_id, "val_auc", 0.83, step=0, synchronous=True)
client.set_terminated(run.info.run_id, status="FINISHED")
```

Repair tip: if user code creates a run with `MlflowClient.create_run()` and then calls `mlflow.log_metric(...)`, the metric goes to the active fluent run or may create a different run. Use `client.log_metric(run.info.run_id, ...)` or wrap fluent logging in `with mlflow.start_run(run_id=run.info.run_id):`.

## Nested Run Pattern

Use nested runs for parent/child comparisons and hyperparameter sweeps.

```python
import mlflow

experiment = mlflow.set_experiment("nested-demo")
with mlflow.start_run(run_name="sweep", experiment_id=experiment.experiment_id) as parent:
    mlflow.log_param("search", "grid")
    for depth in [2, 4, 8]:
        with mlflow.start_run(run_name=f"depth-{depth}", nested=True):
            mlflow.log_param("max_depth", depth)
            mlflow.log_metric("score", depth / 10)

children = mlflow.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string=f"tags.mlflow.parentRunId = '{parent.info.run_id}'",
    output_format="list",
)
```

If MLflow says a run is already active, either exit the current context manager, call `mlflow.end_run()`, or pass `nested=True` for a child run.

## Search and Ranking Pattern

Use precise search strings and explicit output type.

```python
import mlflow
from mlflow.entities import ViewType

runs = mlflow.search_runs(
    experiment_names=["fraud-detection"],
    filter_string="metrics.val_auc >= 0.80 AND tags.owner = 'risk-team'",
    order_by=["metrics.val_auc DESC", "start_time DESC"],
    run_view_type=ViewType.ACTIVE_ONLY,
    output_format="list",
)
best_run = runs[0] if runs else None
```

For service code that may page:

```python
from mlflow import MlflowClient

client = MlflowClient()
page = client.search_runs(["0"], order_by=["metrics.loss ASC"], max_results=50)
while page:
    for run in page:
        process(run)
    token = getattr(page, "token", None)
    if not token:
        break
    page = client.search_runs(["0"], page_token=token, max_results=50)
```

## Artifact Debug Pattern

When users cannot find artifacts:

1. Confirm the run ID that logged the artifact.
2. Print `mlflow.get_artifact_uri()` inside the active run.
3. Remember that `artifact_path` is a logical subdirectory under the run artifact root.
4. Use `MlflowClient().list_artifacts(run_id, path)` to inspect actual logical paths.
5. Use `download_artifacts(run_id=run_id, artifact_path="...")` only after confirming the path.

```python
with mlflow.start_run() as run:
    mlflow.log_artifact("report.json", artifact_path="reports")
    print(mlflow.get_artifact_uri("reports/report.json"))

files = mlflow.MlflowClient().list_artifacts(run.info.run_id, "reports")
print([f.path for f in files])
```

## Dataset-Associated Metrics

Use dataset-aware metrics when comparing model performance across datasets. For fluent code, pass an MLflow dataset object or entity to `log_metric(dataset=...)`. For client code, pass `dataset_name` and `dataset_digest` together.

```python
from mlflow import MlflowClient

client = MlflowClient()
run = client.create_run("0")
client.log_metric(
    run.info.run_id,
    "accuracy",
    0.88,
    step=0,
    dataset_name="validation-2026-06",
    dataset_digest="sha256:example",
    synchronous=True,
)
client.set_terminated(run.info.run_id)
```

## Registry URI Setup Pattern

For local registry development, use SQLite when registry behavior matters:

```python
import tempfile
from pathlib import Path

import mlflow

root = Path(tempfile.mkdtemp(prefix="mlflow-registry-"))
mlflow.set_tracking_uri(f"sqlite:///{root / 'mlflow.db'}")
mlflow.set_registry_uri(f"sqlite:///{root / 'mlflow.db'}")
```

For a remote tracking server with a separate registry:

```python
import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri("https://tracking.example.internal")
mlflow.set_registry_uri("https://registry.example.internal")
client = MlflowClient()
```

For Databricks Unity Catalog:

```python
import mlflow

mlflow.set_tracking_uri("databricks")
mlflow.set_registry_uri("databricks-uc")
```

Do not hard-code credentials in code. Use environment variables, configured profiles, or the platform credential mechanism.

## Register a Logged Model

The model flavor call belongs to `models-and-flavors`; this sub-skill owns the registry step after a model URI exists.

```python
import mlflow
from mlflow import MlflowClient

model_uri = f"runs:/{run_id}/model"  # produced by a flavor log_model workflow
model_version = mlflow.register_model(model_uri, name="FraudRiskModel", tags={"team": "risk"})

client = MlflowClient()
client.set_model_version_tag(model_version.name, model_version.version, "validation", "passed")
client.set_registered_model_alias(model_version.name, "champion", model_version.version)
loaded_uri = f"models:/{model_version.name}@champion"
```

When `register_model` cannot decide which logged model to register from a run path, use the MLflow 3 logged model URI (`models:/<model_id>`) returned by the flavor logging call.

## Manual Registry Version Pattern

Use this when the registered model already exists or when you need explicit version metadata.

```python
from mlflow import MlflowClient

client = MlflowClient()
name = "FraudRiskModel"
try:
    client.create_registered_model(name, tags={"domain": "fraud"}, description="Fraud model")
except Exception as exc:
    if "RESOURCE_ALREADY_EXISTS" not in str(exc) and "already exists" not in str(exc):
        raise

version = client.create_model_version(
    name=name,
    source=f"runs:/{run_id}/model",
    run_id=run_id,
    tags={"validation": "pending"},
    description="Candidate from nightly training",
)
client.set_registered_model_alias(name, "candidate", version.version)
```

## Workspace-Aware Tracking Store Changes

When editing MLflow tracking or registry store code:

- Preserve `workspace_store_uri`, request workspace context, workspace headers, and workspace-aware SQLAlchemy classes.
- Add or update workspace-aware tests when touching SQLAlchemy tracking or registry behavior.
- Do not simplify filters, primary keys, or query paths in a way that drops workspace scoping.
- Check both single-tenant and workspace-aware variants if a change affects CRUD or search behavior.
