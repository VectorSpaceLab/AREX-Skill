# KFP Client API Reference

This reference covers `kfp.Client` resource-management flows. It assumes a
compiled pipeline package already exists or a pipeline function has already been
authored elsewhere. For authoring or compile-only help, route to the sibling
sub-skills.

## Constructor And Connection Inputs

Observed public constructor:

```python
kfp.Client(
    host=None,
    client_id=None,
    namespace="kubeflow",
    other_client_id=None,
    other_client_secret=None,
    existing_token=None,
    cookies=None,
    proxy=None,
    ssl_ca_cert=None,
    kube_context=None,
    credentials=None,
    ui_host=None,
    verify_ssl=None,
)
```

| Input | Use | Notes |
| --- | --- | --- |
| `host` | KFP API endpoint. | If omitted, the client tries in-cluster config and then kubeconfig proxying. If a host lacks `http://` or `https://`, this version warns and defaults to `https://`. Environment fallback: `KF_PIPELINES_ENDPOINT`. |
| `namespace` | KFP user namespace for multi-user deployments. | Constructor default is `"kubeflow"`; docs say single-user deployments should usually leave this as `None`. For multi-user deployments, pass the authorized user namespace explicitly. |
| `client_id` | IAP OAuth client id. | Environment fallback: `KF_PIPELINES_IAP_OAUTH2_CLIENT_ID`. Triggers the SDK IAP auth flow. |
| `other_client_id`, `other_client_secret` | Desktop-app OAuth client credentials for IAP. | Environment fallbacks: `KF_PIPELINES_APP_OAUTH2_CLIENT_ID`, `KF_PIPELINES_APP_OAUTH2_CLIENT_SECRET`. Never print the secret. |
| `existing_token` | Bearer token generated outside the SDK. | Prefer reading from an environment variable. Do not echo, log, or include the value in examples. |
| `credentials` | `TokenCredentialsBase` implementation. | Provides a refresh hook for API client auth. Use when the caller already has a credential object. |
| `cookies` | Authentication cookies. | If omitted, the client may load a local context cookie. Treat as secret. |
| `proxy`, `ssl_ca_cert`, `verify_ssl` | HTTP proxy/TLS settings. | `verify_ssl=False` is a troubleshooting workaround, not a default recommendation. Hide local CA paths in diagnostics. |
| `kube_context` | kubeconfig context. | Used only on the kubeconfig fallback path when no explicit host/token path is sufficient. |
| `ui_host` | Base URL for UI links printed by client methods. | Environment fallback: `KF_PIPELINES_UI_ENDPOINT`. This is not necessarily the API endpoint. |

Client resource methods print UI links for experiments, pipelines, and runs. In
notebooks they may render HTML links; in terminals they print links. Do not treat
those links as credentials.

## Environment Variables

`Client` itself reads these `KF_PIPELINES_*` variables:

- `KF_PIPELINES_ENDPOINT`
- `KF_PIPELINES_UI_ENDPOINT`
- `KF_PIPELINES_DEFAULT_EXPERIMENT_NAME`
- `KF_PIPELINES_OVERRIDE_EXPERIMENT_NAME`
- `KF_PIPELINES_IAP_OAUTH2_CLIENT_ID`
- `KF_PIPELINES_APP_OAUTH2_CLIENT_ID`
- `KF_PIPELINES_APP_OAUTH2_CLIENT_SECRET`

The `kfp` console entrypoint invokes Click with `auto_envvar_prefix="KFP"`, so CLI
options can also be provided as variables such as `KFP_ENDPOINT`,
`KFP_NAMESPACE`, `KFP_EXISTING_TOKEN`, `KFP_IAP_CLIENT_ID`,
`KFP_OTHER_CLIENT_ID`, `KFP_OTHER_CLIENT_SECRET`, and `KFP_OUTPUT`.

## Core Resource Methods

| Resource | Methods | Notes |
| --- | --- | --- |
| Experiments | `create_experiment`, `get_experiment`, `list_experiments`, `archive_experiment`, `unarchive_experiment`, `delete_experiment` | `get_experiment` requires either `experiment_id` or `experiment_name`. Name lookup filters by display name and can be namespace-sensitive. |
| Pipelines | `upload_pipeline`, `upload_pipeline_from_pipeline_func`, `get_pipeline`, `get_pipeline_id`, `list_pipelines`, `delete_pipeline` | `upload_pipeline` accepts a compiled package path and optional display name/description/namespace. If no name is passed, the SDK reads the name from the pipeline spec. |
| Pipeline versions | `upload_pipeline_version`, `upload_pipeline_version_from_pipeline_func`, `get_pipeline_version`, `list_pipeline_versions`, `delete_pipeline_version` | `upload_pipeline_version` requires exactly one of `pipeline_id` or `pipeline_name`; when using name, the SDK resolves it to an ID. |
| Runs | `run_pipeline`, `create_run_from_pipeline_package`, `create_run_from_pipeline_func`, `get_run`, `list_runs`, `archive_run`, `unarchive_run`, `delete_run`, `terminate_run`, `wait_for_run_completion` | `create_run_from_pipeline_package` can create/get an experiment by name unless `experiment_id` is supplied. `RunPipelineResult.wait_for_run_completion()` delegates to the client. |
| Recurring runs | `create_recurring_run`, `get_recurring_run`, `list_recurring_runs`, `enable_recurring_run`, `disable_recurring_run`, `delete_recurring_run` | `create_recurring_run` requires exactly one schedule form: `interval_second` or `cron_expression`. |
| Health/namespace | `get_kfp_healthz`, `get_user_namespace`, `set_user_namespace` | `get_kfp_healthz` is a live network call. `set_user_namespace` persists a local context setting. |

## Upload, Run, And Wait From A Compiled Package

```python
import os
import kfp

client = kfp.Client(
    host=os.environ["KFP_ENDPOINT"],
    namespace=os.environ.get("KFP_NAMESPACE", "kubeflow"),
    existing_token=os.environ.get("KFP_EXISTING_TOKEN"),
    ui_host=os.environ.get("KF_PIPELINES_UI_ENDPOINT"),
    verify_ssl=True,
)

pipeline = client.upload_pipeline(
    pipeline_package_path="pipeline.yaml",
    pipeline_name="example-pipeline",
    description="Compiled elsewhere",
    namespace=os.environ.get("KFP_NAMESPACE"),
)

version = client.upload_pipeline_version(
    pipeline_package_path="pipeline.yaml",
    pipeline_version_name="v1",
    pipeline_id=pipeline.pipeline_id,
)

experiment = client.create_experiment(
    name="example-experiment",
    namespace=os.environ.get("KFP_NAMESPACE"),
)

run = client.run_pipeline(
    experiment_id=experiment.experiment_id,
    job_name="example-run",
    pipeline_package_path="pipeline.yaml",
    params={"message": "hello"},
    pipeline_root=os.environ.get("KFP_PIPELINE_ROOT"),
)
completed = client.wait_for_run_completion(
    run_id=run.run_id,
    timeout=600,
    sleep_duration=5,
)
```

`run_pipeline` can run from a package file or an existing pipeline/version
reference. In this checked revision, the existing-template path validates that
both `pipeline_id` and `version_id` are supplied.

## Create Run Convenience Methods

Use `create_run_from_pipeline_package` when the local package is already
compiled and the SDK should create/get the experiment:

```python
result = client.create_run_from_pipeline_package(
    pipeline_file="pipeline.yaml",
    arguments={"message": "hello"},
    run_name="example-run",
    experiment_name="example-experiment",
    namespace=os.environ.get("KFP_NAMESPACE"),
)
result.wait_for_run_completion(timeout=600)
```

Use `create_run_from_pipeline_func` only when the pipeline function already
exists in the current Python process. It compiles to a temporary YAML and then
uses the package path flow. If the user needs help writing or compiling the
function, route to `pipeline-authoring` or `compiler-and-cli`.

`create_run_from_pipeline_package` rejects simultaneous `experiment_name` and
`experiment_id`. If neither is provided, it consults
`KF_PIPELINES_DEFAULT_EXPERIMENT_NAME`, then
`KF_PIPELINES_OVERRIDE_EXPERIMENT_NAME`, and finally falls back to `Default`.

## Recurring Runs

```python
recurring = client.create_recurring_run(
    experiment_id=experiment.experiment_id,
    job_name="weekday-morning-run",
    pipeline_package_path="pipeline.yaml",
    params={"message": "hello"},
    cron_expression="0 0 9 ? * 2-6",
    max_concurrency=1,
    no_catchup=True,
    enabled=True,
)
```

Rules to preserve:

- Use exactly one of `interval_second` or `cron_expression`.
- `no_catchup=True` avoids scheduler backfill; use it when the pipeline handles
  backfill internally or duplicate catch-up work is unsafe.
- `enable_caching` and `cache_key` are submission-time overrides; when omitted,
  compile-time settings remain in effect.

## Listing, Filtering, Archiving, And Getting

Pagination methods accept `page_token`, `page_size`, `sort_by`, and sometimes
`filter`. Filters are URL-encoded JSON-serialized API filter objects. A display
name filter pattern is:

```python
import json

filter_json = json.dumps({
    "predicates": [{
        "operation": "EQUALS",
        "key": "display_name",
        "stringValue": "example-run",
    }]
})
response = client.list_runs(namespace=os.environ.get("KFP_NAMESPACE"), filter=filter_json)
```

Archive/unarchive methods are available for experiments and runs. Delete methods
exist for experiments, runs, recurring runs, pipelines, and pipeline versions;
ask the user to confirm destructive intent before proposing deletion commands.

## Evidence Notes

This reference was distilled from the KFP Python client implementation, client
unit tests, service-bound client tests, SDK docs stubs, and installed API-surface
facts for `kfp==2.15.2`. Live endpoint behavior remains service-bound and should
be verified in the user's target deployment before treating run/upload actions as
proven.
