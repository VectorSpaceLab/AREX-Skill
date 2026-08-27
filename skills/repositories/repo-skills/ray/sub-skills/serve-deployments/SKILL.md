---
name: serve-deployments
description: "Develop, run, deploy, configure, update, lint, and troubleshoot
  Ray Serve applications and deployments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ray Serve Deployments

Use this sub-skill when the task mentions `ray.serve`, `@serve.deployment`, `serve.run`, `Deployment.bind`, Serve YAML, `serve run`, `serve deploy`, `serve build`, `serve status`, `serve config`, HTTP/gRPC endpoints, `autoscaling_config`, `runtime_env`, `user_config`, or in-place Serve updates.

Ray Serve is Ray's Python serving layer for online inference APIs and general Python web services. Default to the narrow install extra `ray[serve]`; avoid recommending `ray[all]` unless the user explicitly needs many unrelated Ray libraries.

## Route the task

- For Python application code, deployment decorators, handles, batching, FastAPI ingress, or local `serve.run`, use `references/api-reference.md`.
- For Serve YAML, `serve build`, `serve deploy`, `serve run <config.yaml>`, `runtime_env`, HTTP/gRPC/proxy/logging fields, or in-place update planning, use `references/configuration.md`.
- For import errors, config validation, blocked `serve run`, idempotent deploy confusion, remote URI failures, HTTP/gRPC symptoms, and status/config debugging, use `references/troubleshooting.md`.
- For config linting without contacting a Ray cluster, run `scripts/serve_config_lint.py`.
- For a tiny self-contained deployment pattern or optional local smoke check, use `scripts/serve_smoke_app.py`.
- For generic Ray cluster lifecycle, dashboard, node resources, `ray start`, or `ray status`, route to `../cluster-ops/SKILL.md`.
- For training, tuning, or model development workflows before serving, route to `../train-tune/SKILL.md`.

## Default workflow

1. Confirm the user is working on Serve rather than generic Ray cluster operations.
2. For new apps, write a Python module with `@serve.deployment`, bind an application object, then test importability before starting Serve.
3. For local development, use `serve run module:app --app-dir .` or a small guarded script; remember the CLI blocks by default.
4. For production-style deployment, generate or maintain a Serve YAML and use `serve deploy config.yaml` against an already running Ray cluster.
5. After deploys or updates, inspect `serve status` and `serve config`; do not assume `serve deploy` blocks until replicas are healthy.
6. Use lightweight in-place updates only for deployment options that Serve can apply without replica restarts; plan code updates separately.

## Bundled helpers

```bash
python scripts/serve_config_lint.py serve_config.yaml
python scripts/serve_smoke_app.py --validate-only
```

The helpers are safe by default: the linter only parses YAML, and the smoke app only validates imports/configuration unless `--run-local` is explicitly passed.
