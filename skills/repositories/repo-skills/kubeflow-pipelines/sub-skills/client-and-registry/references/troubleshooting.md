# Client And Registry Troubleshooting

Start with the safe configuration helper. It reports whether endpoint,
namespace, auth, UI host, TLS, and kubeconfig signals are present without making
a network request or printing secret values:

```bash
python skills/disco/kubeflow-pipelines/sub-skills/client-and-registry/scripts/check_client_configuration.py
```

Add `--probe-healthz` only when the user explicitly wants a live endpoint probe
and has supplied the correct endpoint/auth context.

## Symptom: localhost connection refused

Common error shape:

```text
HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /apis/v2beta1/healthz
```

Likely causes:

- No explicit KFP API endpoint was provided.
- The client fell back to in-cluster/kubeconfig logic outside a working cluster.
- A client-backed CLI help command instantiated `Client` before help completed.

Actions:

1. Do not tell the user to rerun the same client-backed command unchanged.
2. Ask for or validate the API endpoint and namespace.
3. Run the dry-run helper without `--probe-healthz`.
4. Set `KFP_ENDPOINT` for CLI or pass `host=`/`KF_PIPELINES_ENDPOINT` for Python.
5. Retry a small live call only after endpoint/auth are configured.

## Symptom: missing or invalid kubeconfig warning

Error shape:

```text
Failed to load kube config: Invalid kube-config file. No configuration found.
Proceeding without it; subsequent requests to the Kubeflow Pipelines API may fail.
```

Meaning:

- The SDK did not receive an explicit host/token path and attempted local
  kubeconfig fallback.
- Loading kubeconfig is best-effort and may not raise immediately; the next API
  call can still fail.

Actions:

- If the user is outside the cluster, prefer an explicit API endpoint.
- If kubeconfig proxying is intended, validate the selected kube context and
  namespace outside this skill without printing kubeconfig content.
- In multi-user deployments, pass the user namespace explicitly rather than
  relying on a default.

## Symptom: wrong namespace or missing resources

Likely causes:

- CLI default namespace is `kubeflow`, but the user is in a multi-user namespace.
- Python `Client` default namespace is also `"kubeflow"`, while single-user
  deployments may expect `None`.
- Experiment/run listing filtered by namespace does not match where resources
  were created.

Actions:

- Ask whether the deployment is single-user or multi-user.
- For multi-user: use `namespace=os.environ["KFP_NAMESPACE"]` in Python or
  `KFP_NAMESPACE=...` / `--namespace ...` in CLI.
- When creating and listing, use the same namespace and experiment ID/name.

## Symptom: UI link works but API calls fail

Likely causes:

- `ui_host` or a browser URL was used as the API `host`.
- The deployment exposes UI and API through different base URLs, paths, or
  proxies.

Actions:

- Separate `host`/`--endpoint` from `ui_host`/`KF_PIPELINES_UI_ENDPOINT`.
- Ask the user for the API endpoint from their deployment docs or port-forward.
- Do not use a UI-only URL as proof that `/apis/v2beta1/healthz` is reachable.

## Symptom: client-backed help command fails

Affected groups in this version:

- `kfp pipeline --help`
- `kfp run --help`
- `kfp experiment --help`
- `kfp recurring-run --help`

Reason:

The top-level CLI constructs `Client` for client-backed command groups. That can
trigger config loading and health checks before help text is printed.

Actions:

- Use `kfp --help` for top-level command discovery.
- Use bundled references for client-backed command flags.
- Configure endpoint/auth/namespace before rerunning client-backed help.
- Route compile-only help to `kfp dsl compile --help` and `compiler-and-cli`.

## Symptom: authentication, IAP, or token errors

Likely causes:

- Token not set or expired.
- IAP client ID/secret mismatch.
- Cookie or local context credential is stale.
- Registry token is being used for KFP API, or KFP API token is being used for
  registry.

Actions:

- Never ask the user to paste secret values into chat or logs.
- Ask which auth path is intended: existing bearer token, IAP OAuth, custom
  credentials object, cookies, or registry token.
- For Python examples, read tokens from environment variables:

  ```python
  existing_token=os.environ.get("KFP_EXISTING_TOKEN")
  ```

- For CLI, prefer `KFP_EXISTING_TOKEN` over `--existing-token` so shells and
  process listings are less likely to expose the value.
- If `wait_for_run_completion` receives a 401 after a previously valid token,
  the SDK attempts a token refresh when possible; otherwise the user must renew
  credentials.

## Symptom: TLS or proxy failures

Likely causes:

- Corporate proxy required.
- Custom certificate authority required.
- `verify_ssl` setting does not match endpoint certificates.

Actions:

- Prefer fixing CA/proxy settings over disabling verification.
- If `ssl_ca_cert` is used, do not print local certificate paths in diagnostics.
- Use `verify_ssl=False` only as a bounded troubleshooting step and call out the
  security trade-off.

## Symptom: registry upload did not create a KFP run

Reason:

`RegistryClient.upload_pipeline()` stores a package and returns a registry
`(package_name, version)`. It does not contact the KFP API and does not create an
experiment or run.

Actions:

1. Use `RegistryClient.download_pipeline(package_name, version=... or tag=...)`
   to materialize a package file, or use the local package file directly.
2. Construct `kfp.Client` for the KFP deployment.
3. Call `create_run_from_pipeline_package(...)` or `run_pipeline(...)`.
4. Use `RunPipelineResult.wait_for_run_completion(...)` or
   `Client.wait_for_run_completion(...)` to wait.

## Symptom: registry tag/version validation error

Rules:

- Versions must start with `sha256:`.
- Tags must not start with `sha256:`.
- If both version and tag are passed to `download_pipeline`, version takes
  precedence.

Actions:

- Ask whether the user has a digest version or a human-readable tag.
- Use `list_versions(package_name)` or `list_tags(package_name)` to inspect
  available choices, assuming registry auth is configured.

## Symptom: recurring run creation fails

Likely causes:

- Both `interval_second` and `cron_expression` were supplied.
- Neither schedule field was supplied.
- Experiment ID/name does not resolve in the selected namespace.

Actions:

- Choose exactly one schedule type.
- For CLI, choose exactly one of `--experiment-id` or `--experiment-name`.
- Prefer `no_catchup=True` or `--no-catchup` when duplicated backfill could be
  expensive or unsafe.

## Symptom: wait times out

Meaning:

`wait_for_run_completion` polls until the run reaches a terminal state
(`succeeded`, `failed`, `skipped`, or `error`) or until the timeout elapses.

Actions:

- Increase the timeout only after checking the run's current state and expected
  duration.
- Use `get_run(run_id)` or `kfp run get RUN_ID --watch` with a valid endpoint to
  inspect progress.
- Do not assume timeout means failure; it means the client stopped waiting.
