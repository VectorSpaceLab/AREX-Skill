# KFP Client-Backed CLI Reference

The `kfp` console script starts the Click CLI with `auto_envvar_prefix="KFP"`.
This matters because top-level connection options can be set through environment
variables instead of passing secret-bearing command-line flags.

## Command Families

| Family | Client constructed? | Scope |
| --- | --- | --- |
| `kfp experiment` | Yes | Create, list, get, delete, archive, and unarchive experiments. |
| `kfp pipeline` | Yes | Upload pipeline packages, upload versions, list/get/delete pipelines and versions. |
| `kfp run` | Yes | Create/submit runs, list/get/watch/archive/unarchive/delete runs. |
| `kfp recurring-run` | Yes | Create schedules, list/get/delete/enable/disable recurring runs. |
| `kfp dsl` | No | Compile DSL files; route to `compiler-and-cli`. |
| `kfp component` | No | Component build CLI; route to `compiler-and-cli`. |
| `kfp diagnose-me` | No | Environment/cluster diagnostics; use cautiously because diagnostics can inspect local/cloud state. |

Plural aliases can be accepted for client groups because the top-level CLI treats
client command names and their plural forms as client-backed commands.

## Top-Level Options And Environment Variables

| CLI option | Environment variable | Notes |
| --- | --- | --- |
| `--endpoint` | `KFP_ENDPOINT` | KFP API endpoint. This is not the UI host unless the deployment exposes both at the same base URL. |
| `-n`, `--namespace` | `KFP_NAMESPACE` | Defaults to `kubeflow` in the CLI. Use the user's authorized namespace in multi-user deployments. |
| `--iap-client-id` | `KFP_IAP_CLIENT_ID` | IAP OAuth client id. |
| `--other-client-id` | `KFP_OTHER_CLIENT_ID` | Desktop-app OAuth client id for IAP. |
| `--other-client-secret` | `KFP_OTHER_CLIENT_SECRET` | Secret; prefer environment variable and never echo it. |
| `--existing-token` | `KFP_EXISTING_TOKEN` | Bearer token; prefer environment variable and never echo it. |
| `--output` | `KFP_OUTPUT` | `table` or `json`. |

The Python client also reads `KF_PIPELINES_ENDPOINT` and related
`KF_PIPELINES_*` variables. If both CLI and client variables are present, be
explicit about which interface is being used.

## Help Caveat For Client-Backed Commands

In this checked KFP version, `kfp pipeline --help`, `kfp run --help`,
`kfp experiment --help`, and `kfp recurring-run --help` can instantiate
`kfp.Client` before help text finishes. Without a valid endpoint, kubeconfig, or
in-cluster context, help can fail with kubeconfig warnings and localhost
connection-refused errors.

Safe alternatives:

```bash
kfp --help
kfp dsl compile --help
kfp component --help
python skills/disco/kubeflow-pipelines/sub-skills/client-and-registry/scripts/check_client_configuration.py
```

If the user specifically needs help for a client-backed group, first resolve
`KFP_ENDPOINT`, `KFP_NAMESPACE`, and auth, then retry the help command in that
configured environment.

## `kfp experiment`

| Command | Purpose | Important inputs |
| --- | --- | --- |
| `kfp experiment create NAME` | Create or get an experiment. | `--description`. Namespace comes from top-level `--namespace`. |
| `kfp experiment list` | List experiments. | `--page-token`, `--max-size`, `--sort-by`, `--filter`. |
| `kfp experiment get EXPERIMENT_ID` | Get an experiment by ID. | ID required. |
| `kfp experiment archive` | Archive by ID or name. | Exactly one of `--experiment-id` or `--experiment-name`. |
| `kfp experiment unarchive` | Restore by ID or name. | Exactly one of `--experiment-id` or `--experiment-name`. |
| `kfp experiment delete EXPERIMENT_ID` | Delete an experiment. | Destructive; CLI asks for confirmation. |

## `kfp pipeline`

| Command | Purpose | Important inputs |
| --- | --- | --- |
| `kfp pipeline create PACKAGE_FILE` | Upload a compiled pipeline package. | `--pipeline-name`, `--description`. Alias: `upload`. |
| `kfp pipeline create-version PACKAGE_FILE` | Upload a version for an existing pipeline. | Required `--pipeline-version`; exactly one of `--pipeline-id` or `--pipeline-name`; optional `--description`. Alias: `upload-version`. |
| `kfp pipeline list` | List pipelines. | `--page-token`, `--max-size`, `--sort-by`, `--filter`. |
| `kfp pipeline list-versions PIPELINE_ID` | List versions. | `--page-token`, `--max-size`, `--sort-by`, `--filter`. |
| `kfp pipeline get PIPELINE_ID` | Get pipeline metadata. | ID required. |
| `kfp pipeline get-version PIPELINE_ID VERSION_ID` | Get version metadata. | Both IDs required. |
| `kfp pipeline delete PIPELINE_ID` | Delete a pipeline. | Destructive; CLI asks for confirmation. |
| `kfp pipeline delete-version PIPELINE_ID VERSION_ID` | Delete a version. | Destructive; CLI asks for confirmation. |

Example:

```bash
KFP_ENDPOINT="https://kfp-api.example.com" \
KFP_NAMESPACE="kubeflow-user-example" \
kfp pipeline create pipeline.yaml \
  --pipeline-name example-pipeline \
  --description "Compiled package uploaded by CI"
```

## `kfp run`

| Command | Purpose | Important inputs |
| --- | --- | --- |
| `kfp run create` | Submit a run. | Required `--experiment-name`; optional `--run-name`, `--package-file`, `--pipeline-id`, `--pipeline-name`, `--version`, `--watch`, `--timeout`, and trailing `key=value` params. Alias: `submit`. |
| `kfp run list` | List runs. | `--experiment-id`, `--page-token`, `--max-size`, `--sort-by`, `--filter`. |
| `kfp run get RUN_ID` | Get a run. | `--watch` polls until terminal state; `--detail` is deprecated in favor of `--output=json`. |
| `kfp run archive RUN_ID` | Archive a run. | ID required. |
| `kfp run unarchive RUN_ID` | Restore an archived run. | ID required. |
| `kfp run delete RUN_ID` | Delete a run. | Destructive; CLI asks for confirmation. |

`run create` requires one runnable source among package file, pipeline id, or
version. In practice, if using an existing pipeline template, pass both pipeline
and version IDs to avoid client-side validation ambiguity.

Example:

```bash
KFP_ENDPOINT="https://kfp-api.example.com" \
KFP_NAMESPACE="kubeflow-user-example" \
kfp --output json run create \
  --experiment-name example-experiment \
  --run-name example-run \
  --package-file pipeline.yaml \
  --timeout 600 \
  message=hello retries=3
```

## `kfp recurring-run`

| Command | Purpose | Important inputs |
| --- | --- | --- |
| `kfp recurring-run create` | Create a scheduled run. | Required `--job-name`; exactly one of `--experiment-id` or `--experiment-name`; exactly one of `--interval-second` or `--cron-expression`; package/template inputs; trailing `key=value` params. |
| `kfp recurring-run list` | List schedules. | `--experiment-id`, `--page-token`, `--max-size`, `--sort-by`, `--filter`. |
| `kfp recurring-run get RECURRING_RUN_ID` | Get schedule metadata. | ID required. |
| `kfp recurring-run delete RECURRING_RUN_ID` | Delete a schedule. | Destructive; CLI asks for confirmation. |
| `kfp recurring-run enable RECURRING_RUN_ID` | Enable a schedule. | Follow-up get is performed. |
| `kfp recurring-run disable RECURRING_RUN_ID` | Disable a schedule. | Follow-up get is performed. |

Example:

```bash
KFP_ENDPOINT="https://kfp-api.example.com" \
KFP_NAMESPACE="kubeflow-user-example" \
kfp recurring-run create \
  --experiment-name example-experiment \
  --job-name weekday-morning-run \
  --pipeline-package-path pipeline.yaml \
  --cron-expression "0 0 9 ? * 2-6" \
  --no-catchup
```

## When To Prefer Python API Over CLI

Prefer `kfp.Client` when the user needs typed return objects, programmatic
polling, custom auth credentials, or a workflow that combines upload, run,
listing, and cleanup. Prefer CLI examples when the user is operating manually or
inside CI and already has endpoint/auth variables configured.
