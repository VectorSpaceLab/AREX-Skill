---
name: cli-and-cloud
description: "Use BentoML CLI command families and BentoCloud workflows safely:
  login/context, deploy/deployment lifecycle, codespaces, secrets, API tokens,
  push/pull, and cloud troubleshooting. Use when a task asks for bentoml
  terminal commands or BentoCloud operations rather than Python service
  authoring, local serving/client calls, container builds, or observability
  setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BentoML CLI And BentoCloud

Use this sub-skill when the user needs a safe command plan or troubleshooting path for BentoML CLI and BentoCloud. Treat credentialed cloud commands as user-run operations unless the user explicitly asks you to execute them in an authenticated environment.

## Safe Operating Rules

- Prefer local, non-mutating checks first: `bentoml --help`, `bentoml <command> --help`, config-file linting, and command construction.
- Never print, store, or request raw API token values. `bentoml api-token create` shows the token once; tell the user to save it securely outside the transcript.
- Ask before running credentialed or mutating cloud operations such as `bentoml cloud login`, `bentoml deploy`, `bentoml deployment update/apply/start/terminate/delete`, `bentoml secret create/apply/delete`, `bentoml api-token create/delete`, `bentoml push`, and `bentoml pull`.
- Classify destructive operations clearly: `deployment delete` is irreversible, `deployment terminate` stops billing-capable workloads but can be restarted, and `secret delete`/`api-token delete` can break deployments or automation.
- Do not put secrets in command lines when avoidable. Use environment variables, files managed by the user, or BentoCloud secrets, and redact values in outputs.

## Workflow Routing

- For CLI command discovery and safe local checks, use `references/cli-catalog.md` and `scripts/inspect_bentoml_cli.py`.
- For BentoCloud login, context, deployment, codespace, secret, API-token, push/pull, and CI/CD command plans, use `references/bentocloud-workflows.md`.
- For errors such as not logged in, wrong context/cluster, missing tokens/secrets, invalid deployment config, wait timeout, quota, auth failures, or destructive-operation risk, use `references/troubleshooting.md`.
- For deployment YAML/JSON review before a cloud call, run `scripts/deployment_config_lint.py` locally.

## Common Command Plans

### Inspect CLI Without Cloud Access

```bash
python skills/bentoml/sub-skills/cli-and-cloud/scripts/inspect_bentoml_cli.py --commands "cloud" "deployment" "deploy" "secret" "api-token"
```

This helper only imports the local CLI and renders Click help through `CliRunner`; it does not log in or contact BentoCloud.

### Login And Verify Context

```bash
bentoml cloud login
bentoml cloud current-context
bentoml cloud list-context
```

Use `bentoml cloud login --api-token "$BENTOCLOUD_API_TOKEN"` only in user-controlled shells or CI logs with secret masking. The CLI also accepts `BENTO_CLOUD_API_ENDPOINT` and `BENTO_CLOUD_API_KEY` environment variables.

### Deploy From A Project Directory

```bash
bentoml deploy . -n my-deployment --cluster my-cluster --scaling-min 0 --scaling-max 3 --wait --timeout 3600
```

If configuration is complex or there are multiple services, prefer a YAML/JSON config and lint it first:

```bash
python skills/bentoml/sub-skills/cli-and-cloud/scripts/deployment_config_lint.py config-file.yaml
bentoml deploy -f config-file.yaml
```

### Manage A Deployment

```bash
bentoml deployment list --cluster my-cluster
bentoml deployment get my-deployment --cluster my-cluster -o yaml
bentoml deployment update my-deployment --cluster my-cluster --scaling-min 1 --scaling-max 5
bentoml deployment apply my-deployment --cluster my-cluster -f deployment.yaml
bentoml deployment terminate my-deployment --cluster my-cluster --wait
```

Use `update` for patch-only changes. Use `apply` when the config should become the desired full state; it can reset or remove unspecified fields.

## Cross-References

- CLI command catalog: `references/cli-catalog.md`
- BentoCloud workflows: `references/bentocloud-workflows.md`
- Troubleshooting guide: `references/troubleshooting.md`
- Local CLI help inspector: `scripts/inspect_bentoml_cli.py`
- Local deployment config linter: `scripts/deployment_config_lint.py`
