# Ray Serve Configuration

Serve config files are YAML documents used by `serve deploy`, `serve run <config.yaml>`, and RayService-style production workflows. They can configure Serve system components, one or more applications, and per-deployment overrides. This reference is self-contained and focuses on fields that agents commonly author or debug.

## Minimal config

The smallest useful config names an import path for a bound Serve application:

```yaml
applications:
- name: default
  route_prefix: /
  import_path: text_service:app
```

`import_path` must resolve to a `ray.serve.deployment.Application` object or a function that returns one. The import target must be available wherever Serve runs.

## Full structure

```yaml
proxy_location: EveryNode

target_capacity: 100

http_options:
  host: 0.0.0.0
  port: 8000
  request_timeout_s: 30
  keep_alive_timeout_s: 90

grpc_options:
  port: 9000
  grpc_servicer_functions: []
  request_timeout_s: 30

logging_config:
  encoding: TEXT
  log_level: INFO
  logs_dir: null
  enable_access_log: true

applications:
- name: default
  route_prefix: /
  import_path: text_service:app
  runtime_env:
    pip:
      - "ray[serve]"
      - scikit-learn
    working_dir: s3://example-bucket/text-service.zip
  args:
    model_name: baseline
  external_scaler_enabled: false
  deployments:
  - name: TextClassifier
    num_replicas: 2
    ray_actor_options:
      num_cpus: 0.5
    user_config:
      threshold: 0.7
  - name: Embedder
    autoscaling_config:
      min_replicas: 1
      max_replicas: 4
      target_ongoing_requests: 8
    max_ongoing_requests: 32
```

## Top-level fields

| Field | Meaning | Practical guidance |
| --- | --- | --- |
| `proxy_location` | Where Serve runs HTTP/gRPC proxies: `EveryNode`, `HeadOnly`, or `Disabled`. | Use `EveryNode` for cluster traffic; use `HeadOnly` or local defaults for simple local tests; use `Disabled` only for handle-only apps. |
| `target_capacity` | Percentage capacity modifier for replicas across the cluster. | Keep omitted or `100` unless deliberately reducing service capacity. |
| `http_options` | Global HTTP proxy config. | Not a runtime-updatable field; plan cluster/service restart or replacement for changes. |
| `grpc_options` | Global gRPC proxy config. | Include `grpc_servicer_functions` import paths when serving gRPC methods. |
| `logging_config` | Global controller/proxy/replica logging defaults. | App/deployment logging config can override global defaults. |
| `applications` | List of application configs. | Application names and route prefixes must be unique. |

## HTTP options

| Field | Meaning |
| --- | --- |
| `host` | Interface for HTTP proxies. Use `127.0.0.1` for local-only access and `0.0.0.0` to expose outside the host/container. |
| `port` | HTTP proxy port, commonly `8000`. |
| `request_timeout_s` | End-to-end request timeout before termination/retry. Omit for no request timeout. |
| `keep_alive_timeout_s` | HTTP keep-alive timeout, commonly `90`. |
| TLS fields | API-level HTTP options include TLS key/cert/CA fields; configure them only when the deployment environment supplies the files. |

HTTP config is global to the Ray cluster's Serve instance and is not designed for live update. If a user asks why a redeployed config did not move the HTTP port, treat it as a system/proxy change, not an app-level lightweight update.

## gRPC options

| Field | Meaning |
| --- | --- |
| `port` | gRPC proxy port, commonly `9000`. |
| `grpc_servicer_functions` | List of import paths for functions that add method handlers to the gRPC server. |
| `request_timeout_s` | gRPC request timeout. |

If `grpc_servicer_functions` is empty, user-defined gRPC service methods are not registered even if the port is configured.

## Application fields

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | Recommended | Unique app name. `serve build` auto-generates names for multi-app configs. |
| `route_prefix` | Optional | HTTP route prefix. Must start with `/`, cannot end with `/` unless exactly `/`, and cannot contain wildcards. Each app route must be unique. |
| `import_path` | Yes | `module:attribute` or equivalent import path for the Serve application or builder. |
| `runtime_env` | Optional | Environment for application code and dependencies. In config files, `working_dir` and `py_modules` must be remote URIs. |
| `args` | Optional | JSON/YAML-serializable arguments for an application builder function. |
| `external_scaler_enabled` | Optional | Enables external scaling API. Do not combine with built-in deployment `autoscaling_config` in the same app. |
| `deployments` | Optional | Per-deployment overrides matched by `name`; omitted deployments use code defaults. |

## Deployment fields

Every deployment override needs a `name` matching a deployment in the bound application graph. Common fields:

| Field | Meaning | Update behavior |
| --- | --- | --- |
| `num_replicas` | Fixed replica count; can also be `auto` for default autoscaling. | Lightweight. |
| `autoscaling_config` | Autoscaling bounds/target/policy. | Lightweight. |
| `user_config` | JSON-serializable data passed to `reconfigure`. | Lightweight if deployment implements live reconfiguration safely. |
| `max_ongoing_requests` | Max parallel requests per replica. | Lightweight. |
| `graceful_shutdown_timeout_s` | Max wait before force-killing a replica during shutdown. | Lightweight. |
| `graceful_shutdown_wait_loop_s` | Wait loop period for graceful shutdown. | Lightweight. |
| `health_check_period_s` | Health check frequency. | Lightweight. |
| `health_check_timeout_s` | Health check timeout. | Lightweight. |
| `ray_actor_options` | Per-replica Ray actor resources and runtime env. | Code update; restarts deployment replicas. |
| `placement_group_bundles` | Per-replica placement group bundles. | Code update; restarts deployment replicas. |
| `placement_group_strategy` | Placement group strategy such as `PACK`. | Code update; restarts deployment replicas. |
| `logging_config` | Deployment log settings. | Treat as deployment config; verify behavior with `serve status` and logs. |
| `request_router_config` | Router class and routing stats options. | Treat carefully; custom classes must be importable in the runtime env. |

Do not set fixed integer `num_replicas` and non-null `autoscaling_config` together. If autoscaling is enabled, set `num_replicas: auto`, `num_replicas: null`, or omit `num_replicas` depending on the desired defaults.

## `runtime_env` rules

Runtime environments package dependencies and application code for Serve. Important distinctions:

- `serve run --working-dir <local-dir>` accepts a local directory for development.
- `serve deploy --working-dir <uri>` from an import path requires a remote zip URI.
- Serve YAML `runtime_env.working_dir` and `runtime_env.py_modules` support only remote URIs, not local directories or local zip files.
- The `import_path` must be importable inside the `runtime_env` where Serve runs.
- `serve build` generates `runtime_env: {}`; fill dependencies and remote code packaging manually before production deploy.

Recommended pattern for production-style YAML:

```yaml
applications:
- name: default
  route_prefix: /classify
  import_path: classifier_service:app
  runtime_env:
    working_dir: s3://my-bucket/classifier_service.zip
    pip:
      - "ray[serve]"
      - scikit-learn==1.5.2
```

If the user's config points `working_dir` at `.` or a local path in YAML, explain that this is valid for local `serve run --working-dir` development but invalid for deployed Serve configs; package and upload the code as a remote zip or install it as a package.

## In-place update rules

`serve deploy` is idempotent: after a successful deploy request, Serve tries to make the running applications match the latest config. Reapplying the same config should be safe.

Lightweight deployment updates do not tear down running replicas for that deployment:

- `num_replicas`
- `autoscaling_config`
- `user_config`
- `max_ongoing_requests`
- `graceful_shutdown_timeout_s`
- `graceful_shutdown_wait_loop_s`
- `health_check_period_s`
- `health_check_timeout_s`

Code updates restart replicas:

- Deployment `ray_actor_options`
- Deployment `placement_group_bundles`
- Deployment `placement_group_strategy`
- Application `import_path`
- Application `runtime_env`

For large production code updates, prefer a new Ray cluster or Serve instance and switch traffic after validation rather than hot-swapping `import_path` or `runtime_env` in place.

Example lightweight update:

```yaml
applications:
- name: default
  route_prefix: /
  import_path: text_service:app
  deployments:
  - name: TextClassifier
    num_replicas: 3
    user_config:
      threshold: 0.82
```

Example code update:

```yaml
applications:
- name: default
  route_prefix: /
  import_path: text_service_v2:app
  runtime_env:
    working_dir: s3://example-bucket/text-service-v2.zip
```

## `serve build` workflow

Use `serve build` to bootstrap YAML from app code:

```bash
serve build text_service:app -o serve_config.yaml
```

Then edit the generated file:

1. Confirm every generated application has the intended `name` and `route_prefix`.
2. Add `runtime_env` manually; generated files leave it empty.
3. Tune `num_replicas`, `autoscaling_config`, `ray_actor_options`, `user_config`, and logging fields.
4. Lint the YAML with the bundled linter before contacting a cluster.
5. Deploy and poll status.

```bash
python scripts/serve_config_lint.py serve_config.yaml
serve deploy serve_config.yaml
serve status
serve config
```

## Config lint checklist

Before deploying, check:

- YAML parses to a mapping.
- `applications` is present and is a non-empty list.
- Application names are unique when provided.
- Route prefixes are unique and follow Serve route rules.
- Every app has an `import_path`.
- Config-file `runtime_env.working_dir` and `runtime_env.py_modules` use remote URIs if present.
- Deployment overrides have names.
- Deployment `num_replicas` is not a fixed integer when `autoscaling_config` is also set.
- `user_config`, `args`, logging config, router kwargs, and autoscaling policy kwargs are JSON/YAML-serializable.
- `external_scaler_enabled` is not combined with built-in deployment autoscaling.

The bundled linter catches many structural mistakes without importing the user app or contacting a cluster. It is not a substitute for `ServeDeploySchema` validation in the exact installed Ray version, but it is safer and faster for early review.
