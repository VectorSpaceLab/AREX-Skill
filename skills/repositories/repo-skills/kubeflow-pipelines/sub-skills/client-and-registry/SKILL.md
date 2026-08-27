---
name: client-and-registry
description: "Use Kubeflow Pipelines Client, client-backed CLI, and
  RegistryClient flows safely without confusing them with compile-only pipeline
  authoring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Client And Registry

Use this sub-skill when the task is about connecting to a Kubeflow Pipelines
(KFP) deployment, submitting or managing runs through `kfp.Client`, managing
experiments/recurring runs/pipeline uploads, using client-backed KFP CLI command
families, or using `kfp.registry.RegistryClient` to upload, download, tag, and
list registry packages.

## Route First

Use this skill for:

- Constructing `kfp.Client(host=..., namespace=..., existing_token=..., ui_host=..., verify_ssl=...)` and explaining endpoint/auth/namespace behavior.
- Uploading compiled pipeline packages or versions with the KFP API.
- Creating experiments, runs, recurring runs, and waiting for run completion.
- Listing, getting, archiving, unarchiving, deleting, enabling, or disabling KFP resources through client APIs or client-backed CLI commands.
- Uploading, downloading, tagging, listing, or deleting registry packages through `RegistryClient`.

Route away when the user needs:

- Pipeline or component authoring, DSL control flow, task modifiers, or local execution: `pipeline-authoring`.
- Compile-only output, `kfp dsl compile`, `dsl-compile`, PipelineSpec YAML, or Kubernetes-native manifest output: `compiler-and-cli`.
- Kubernetes task configuration helpers such as secrets, PVCs, tolerations, node selectors, or platform specs: `kubernetes-platform`.
- Source checkout maintenance, generated code, deployment internals, CI, or backend/frontend development: `repo-development`.

## Safety Defaults

1. Treat KFP API calls as service-bound. Do not suggest a live call until the
   API endpoint, namespace mode, auth method, and credential source are clear.
2. Do not print or ask the user to paste token values, IAP client secrets,
   cookies, kubeconfig contents, or registry credentials. Prefer environment
   variable names in examples.
3. Distinguish the API endpoint (`host`/`--endpoint`) from the UI host
   (`ui_host`/`KF_PIPELINES_UI_ENDPOINT`). UI links are not proof that the API
   endpoint is reachable.
4. Use the bundled dry-run helper first when debugging configuration:

   ```bash
   python skills/disco/kubeflow-pipelines/sub-skills/client-and-registry/scripts/check_client_configuration.py
   ```

   It does not contact the service unless `--probe-healthz` is explicitly set.
5. Registry upload is not run submission. A registry package/version/tag must be
   downloaded or otherwise supplied to `Client` before it creates a run.

## Operating Procedure

1. **Classify the desired operation.** Decide whether the user needs the KFP API
   (`Client`), KFP CLI client-backed resource commands, or a registry package
   operation (`RegistryClient`).
2. **Validate connection inputs.** Resolve `host`, namespace, UI host, auth mode,
   TLS settings, and whether an endpoint is API or UI. If no explicit host is
   provided, explain that `Client` may try in-cluster configuration or local
   kubeconfig proxying and can fail with localhost connection refused.
3. **Choose the smallest flow.** Use package upload/run APIs for KFP execution;
   use registry APIs only for package distribution; use compile/authoring
   sub-skills if the package does not exist yet.
4. **Show secret-safe examples.** Load tokens/secrets from environment variables
   and redact values in any diagnostic output.
5. **Confirm service-bound uncertainty.** If no live KFP/registry endpoint is
   available, provide a dry-run plan and identify exactly which call remains
   unverified.

## Common Client Patterns

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
```

Upload a compiled package, create or reuse an experiment, submit a run, and wait:

```python
experiment = client.create_experiment(
    name="example-experiment",
    namespace=os.environ.get("KFP_NAMESPACE"),
)
run_result = client.create_run_from_pipeline_package(
    pipeline_file="pipeline.yaml",
    arguments={"message": "hello"},
    run_name="example-run",
    experiment_id=experiment.experiment_id,
)
completed_run = run_result.wait_for_run_completion(timeout=600)
```

Create a recurring run only after deciding one schedule type:

```python
recurring_run = client.create_recurring_run(
    experiment_id=experiment.experiment_id,
    job_name="nightly-example",
    pipeline_package_path="pipeline.yaml",
    cron_expression="0 0 9 ? * 2-6",
    no_catchup=True,
)
```

For deeper method signatures, filters, and edge cases, open
`references/api-reference.md`.

## CLI Patterns

The top-level `kfp` command uses Click `auto_envvar_prefix="KFP"`; for example,
`--endpoint`, `--namespace`, and `--existing-token` can be supplied as
`KFP_ENDPOINT`, `KFP_NAMESPACE`, and `KFP_EXISTING_TOKEN`.

Client-backed command groups are `experiment`, `pipeline`, `run`, and
`recurring-run`. In this KFP version, invoking help under one of those groups may
instantiate `Client` before help finishes, so a missing endpoint/kubeconfig can
turn `kfp pipeline --help` into a localhost connection error. See
`references/cli-reference.md` before advising users to rerun those help commands.

Example service-bound CLI run submission:

```bash
KFP_ENDPOINT="https://kfp-api.example.com" \
KFP_NAMESPACE="kubeflow-user-example" \
kfp --output json run create \
  --experiment-name example-experiment \
  --run-name example-run \
  --package-file pipeline.yaml \
  message=hello
```

## Registry Patterns

```python
import os
from kfp.registry import ApiAuth, RegistryClient

registry = RegistryClient(
    host=os.environ["KFP_REGISTRY_HOST"],
    auth=ApiAuth(os.environ["KFP_REGISTRY_TOKEN"]),
)
package_name, version = registry.upload_pipeline(
    file_name="pipeline.yaml",
    tags=["latest", "dev"],
)
registry.create_tag(package_name=package_name, version=version, tag="prod")
```

Use `RegistryClient.download_pipeline(...)` to materialize a package before
submitting it through `kfp.Client`. See `references/registry-workflows.md` for
version/tag rules and separation from run creation.

## References

- `references/api-reference.md` - constructor args, env vars, resource methods,
  upload/run/wait/recurring-run patterns.
- `references/cli-reference.md` - client-backed CLI groups, flags, environment
  variables, and help-instantiation caveat.
- `references/registry-workflows.md` - registry client constructor, upload,
  download, list, tag, and cleanup workflows.
- `references/troubleshooting.md` - endpoint, kubeconfig, namespace, auth, UI/API,
  help, wait, and registry confusion symptoms.
- `scripts/check_client_configuration.py` - safe configuration checker; optional
  explicit healthz probe.
