---
name: cloud-deployment
description: "Guides OpenLLM BentoCloud deployment with `openllm deploy`,
  including contexts, instance types, environment variables, credential
  boundaries, and deployment troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cloud Deployment

Use this sub-skill when the task is about deploying an OpenLLM model Bento to BentoCloud.

## Typical triggers

- `openllm deploy MODEL[:VERSION]`
- `--instance-type`, `--context`, `--repo`, `--env`, or `--arg`
- BentoCloud login, API token, `.yatai.yaml`, or current context
- Instance type discovery or insufficient cloud resources
- Gated model deployment with `HF_TOKEN`

## What this route covers

- Deployment command construction and required flag choices.
- BentoCloud context and config prerequisites.
- How model-required environment variables are gathered.
- How local/cloud GPU resources are compared for recommended instance types.
- Credential-safe troubleshooting.

## Read next

- [references/deploy-workflows.md](references/deploy-workflows.md) for practical deployment runbooks.
- [references/cloud-api-reference.md](references/cloud-api-reference.md) for verified helper signatures and data flow.
- [references/troubleshooting.md](references/troubleshooting.md) for common deploy failures.
- [scripts/plan_deploy_command.py](scripts/plan_deploy_command.py) to build a credential-safe command preview.

## Boundaries

Do not route local serving or terminal chat here. Use `local-serving` for `serve` and `run`. Use `model-repositories` for catalog discovery before deploy. Use `environment-maintenance` for cache, install, and low-level resource diagnostics.
