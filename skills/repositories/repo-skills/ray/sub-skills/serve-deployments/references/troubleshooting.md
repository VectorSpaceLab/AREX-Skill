# Ray Serve Troubleshooting

Use this guide to debug common Ray Serve development, YAML, CLI, update, HTTP, and gRPC failures. For generic cluster startup, node health, dashboard availability, or `ray start` issues, route to `../cluster-ops/SKILL.md`.

## Fast triage

1. Identify whether the user is using Python API (`serve.run`), CLI import path (`serve run module:app`), or YAML (`serve deploy config.yaml`).
2. Validate imports and config before contacting a cluster.
3. If a deploy request was sent successfully, check convergence with `serve status`; do not treat the submit message as a healthy deployment.
4. Compare intended config with live config using `serve config`.
5. Classify updates as lightweight or code updates before promising no restarts.

Useful commands:

```bash
python -c "import ray, ray.serve; print(ray.__version__)"
python scripts/serve_config_lint.py serve_config.yaml
serve status
serve config
serve status -n default
serve config -n default
```

## Missing Serve install extra

Symptoms:

- `ModuleNotFoundError` for Serve HTTP/gRPC dependencies.
- `serve` console command missing or incomplete.
- `import ray.serve` fails.

Fix:

```bash
pip install "ray[serve]"
```

Use a narrower extra for unrelated workflows (`ray[data]`, `ray[train]`, `ray[tune]`, or `ray[rllib]`) instead of installing `ray[all]` by default.

## Import path errors

Symptoms:

- `serve run app:app` cannot import the module.
- `serve build app:app` says the target is not an application.
- `serve deploy` fails after submitting because workers cannot import application code.

Checks:

```bash
python -c "import importlib; mod = importlib.import_module('app'); print(hasattr(mod, 'app'))"
serve run app:app --app-dir . --non-blocking
```

Fixes:

- Define the bound Serve application at module scope, for example `app = Model.bind()`.
- Do not call `serve.run(app)` at import time; guard it with `if __name__ == "__main__"`.
- Use `--app-dir .` for local development when the module is in the current project directory.
- For deployed YAML, package code in `runtime_env.working_dir` as a remote zip URI or install the module as a package available in the runtime environment.
- If the import target is a builder function, pass arguments as `key=value` in CLI import-path mode or with YAML `args` in config mode.

## YAML structure and schema errors

Symptoms:

- Validation errors mentioning duplicate app names or route prefixes.
- Config parses locally but Serve rejects it.
- Deployment override seems ignored.

Checks:

```bash
python scripts/serve_config_lint.py serve_config.yaml
serve config
```

Fixes:

- Make `applications` a list, even for one app.
- Give each app a unique `name` and unique `route_prefix`.
- Route prefixes must start with `/`, must not end with `/` unless exactly `/`, and must not contain wildcards like `{id}`.
- Every deployment override must have a `name` matching a deployment in the application code.
- Do not set fixed integer `num_replicas` and `autoscaling_config` together.
- If `external_scaler_enabled: true`, remove built-in deployment `autoscaling_config` entries in that application.

## `runtime_env` remote URI failures

Symptoms:

- Validation error says `working_dir` or `py_modules` must be remote URIs.
- Workers cannot import modules that import fine on the submitting machine.
- `serve deploy --working-dir .` or YAML `working_dir: .` fails.

Rules:

- YAML `runtime_env.working_dir` and `runtime_env.py_modules` must be remote URIs.
- `serve deploy --working-dir` from an import path must use a remote zip URI.
- `serve run --working-dir` may use a local directory for development.

Fixes:

- Upload the project as a `.zip` to a remote URI supported by Ray runtime environments.
- Or package and install the app so the module is importable without `working_dir`.
- Keep `pip` dependencies explicit in `runtime_env.pip` or the deployment image.
- Ensure the `import_path` resolves inside the runtime environment, not only in the submitter shell.

## `serve run` blocks or tears down apps

Symptoms:

- Terminal appears hung after `serve run`.
- `Ctrl-C` removes the app.
- `--reload` conflicts with non-blocking mode.

Explanation and fixes:

- `serve run` blocks by default and streams logs.
- Use `serve run module:app --non-blocking` for a dev command that returns after launching.
- Do not combine `--reload` with `--non-blocking`; reload mode must keep watching files.
- For production, prefer `serve deploy config.yaml` and inspect `serve status` separately.
- If a Python script calls `serve.run(app)` directly, pass `blocking=False` for tests or guard long-running calls behind command-line flags.

## Deploy idempotence and status confusion

Symptoms:

- `serve deploy` says the request was sent, but HTTP requests fail.
- Re-running `serve deploy` appears to remove apps not present in the latest config.
- User expects `serve deploy` to block until replicas are healthy.

Explanation and fixes:

- `serve deploy` is idempotent: the Serve instance converges to the latest successfully deployed config.
- A successful submit message means the config request reached the dashboard API; it does not mean replicas are healthy.
- Follow every deploy with `serve status` until the target app is `RUNNING` and deployments are `HEALTHY`.
- Use `serve config` to confirm the live config matches the intended YAML.
- If a multi-app config omits an existing app, Serve may delete that app to match the new config.

## Lightweight update versus code update

Symptoms:

- Replicas restarted unexpectedly after a config change.
- User expects `runtime_env` or `ray_actor_options` changes to be live.
- `user_config` changed but app behavior did not.

Lightweight deployment fields:

- `num_replicas`
- `autoscaling_config`
- `user_config`
- `max_ongoing_requests`
- `graceful_shutdown_timeout_s`
- `graceful_shutdown_wait_loop_s`
- `health_check_period_s`
- `health_check_timeout_s`

Code-update fields that restart replicas:

- Deployment `ray_actor_options`
- Deployment `placement_group_bundles`
- Deployment `placement_group_strategy`
- Application `import_path`
- Application `runtime_env`

Fixes:

- For `user_config`, implement `reconfigure(self, config)` in the deployment and store the updated values.
- For code or dependency changes, plan a rolling or blue/green style rollout instead of promising no restart.
- Use `serve status` during the update; deployments can show `UPDATING` before returning to `HEALTHY`.

## Autoscaling and batching issues

Symptoms:

- Deployment never scales as expected.
- Batching under-utilizes replicas.
- Config validation complains about replicas and autoscaling.

Fixes:

- Do not combine `num_replicas: 2` with `autoscaling_config`; use `num_replicas: auto`, `num_replicas: null`, or omit fixed replicas.
- Set `min_replicas`, `max_replicas`, and a target such as `target_ongoing_requests` deliberately.
- For `@serve.batch`, ensure `max_ongoing_requests >= max_batch_size * max_concurrent_batches`.
- If external scaling is enabled for an app, remove built-in `autoscaling_config` from deployments in that app.

## HTTP problems

Symptoms:

- Client cannot connect to `localhost:8000`.
- Endpoint works locally but not outside a container or cluster.
- Route returns 404.

Checks and fixes:

- Confirm the application `route_prefix` and request path. Route `/classify` is not the same as `/`.
- For local-only development, `127.0.0.1:8000` is expected.
- For external access, configure `http_options.host: 0.0.0.0` and ensure networking/firewall/proxy rules allow the port. Cluster networking belongs to `../cluster-ops/SKILL.md`.
- Confirm the app is `RUNNING` and deployments are `HEALTHY` in `serve status`.
- If using FastAPI ingress, confirm routes are defined in the FastAPI app and attached to the Serve deployment correctly.

## gRPC problems

Symptoms:

- gRPC port is open but service methods are unavailable.
- gRPC requests return not found or unavailable.

Checks and fixes:

- Configure `grpc_options.grpc_servicer_functions` with import paths for functions that add handlers to the gRPC server.
- Ensure those import paths are available inside the app `runtime_env` or image.
- Confirm `grpc_options.port` matches the client target.
- Use `serve status` to separate app/deployment health from client stub or protobuf issues.

## Shutdown and cleanup

- `serve shutdown` deletes Serve applications on the target cluster; use it only when the user intends cleanup.
- `serve run` with default blocking mode shuts down Serve on `Ctrl-C`.
- Generic `ray stop`, node cleanup, dashboard process issues, and autoscaler status are cluster operations, not Serve-specific troubleshooting.

## Safe verification candidates

Preferred low-risk checks:

- `serve --help`, `serve run --help`, `serve deploy --help`, `serve status --help`, and `serve config --help`.
- Bundled config linter on synthetic YAML.
- `serve_smoke_app.py --validate-only` to confirm Serve imports and app binding without starting a server.
- Optional `serve_smoke_app.py --run-local` only when it is safe to start a local Ray/Serve instance.
