---
name: deploy
description: "Use this sub-skill when deploying agents-cli projects to Agent
  Runtime, Cloud Run, or GKE; provisioning infrastructure; setting up CI/CD;
  running deployed smoke tests; or troubleshooting production deployment
  failures."
metadata:
  disco-role: operating
  author: Google
  license: Apache-2.0
  version: 1.3.1
  requires:
    bins:
      - agents-cli
    install: "uv tool install google-agents-cli"
disable-model-invocation: true
license: Apache 2.0
---

# Deployment and Infrastructure

Use this sub-skill inside the `google-agents-cli` repo skill. It is a router plus operating checklist; move into the bundled references for full command flags, schemas, and examples.

## When to Use

- The user wants to deploy to Agent Runtime, Cloud Run, or GKE.
- The task mentions Terraform, CI/CD, Cloud Build, GitHub Actions, IAP, PSC, load tests, or remote `run --url`.
- You need to troubleshoot deployment target, IAM, network, timeout, or endpoint issues.

## Workflow

1. Confirm target, project, region, credentials, IAM, cost, and whether Terraform/CI-CD is desired.
2. Use scaffold/enhance first if deployment files are missing.
3. Deploy with `agents-cli deploy` or provision infra with the documented `infra` commands.
4. Smoke-test the deployed URL with `agents-cli run --url` before publishing or load testing.

## Read These References

- `references/deploy-guide.md` — read for deploy guide details.
- `references/agent-runtime.md` — read for agent runtime details.
- `references/batch-inference.md` — read for batch inference details.
- `references/cicd-pipeline.md` — read for cicd pipeline details.
- `references/cloud-run.md` — read for cloud run details.
- `references/gke.md` — read for gke details.
- `references/terraform-patterns.md` — read for terraform patterns details.
- `references/testing-deployed-agents.md` — read for testing deployed agents details.

## Verification and Safety

Safe checks: `agents-cli deploy --help`; live deploy/infra/load tests need cloud credentials and cost approval.

## Boundaries

- Does not publish to Gemini Enterprise; use publish after deployment.
- Does not execute cloud/Terraform/GitHub mutations without explicit approval.

## Related Sub-Skills

- `../workflow/SKILL.md` — lifecycle routing and approval gates.
- `../scaffold/SKILL.md` — project creation/enhancement.
- `../adk-code/SKILL.md` — ADK Python implementation patterns.
- `../eval/SKILL.md` — evaluation loops and metrics.
- `../deploy/SKILL.md` — deployment and infrastructure.
- `../publish/SKILL.md` — Gemini Enterprise registration.
- `../observability/SKILL.md` — logging, tracing, and analytics.
