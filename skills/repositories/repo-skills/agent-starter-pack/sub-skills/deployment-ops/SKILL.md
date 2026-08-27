---
name: deployment-ops
description: "Guides CI/CD setup, deployment commands, observability, data
  ingestion, and Gemini Enterprise registration for Agent Starter Pack
  projects."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Deployment operations

Use this sub-skill when the user is turning an Agent Starter Pack project into a deployable, observable, or registered cloud asset.

## Covers
- `setup-cicd` and its Terraform/runner setup.
- Generated-project deployment commands such as `make setup-dev-env`, `make setup-datastore`, `make deploy`, `make data-ingestion`, `make sync-data`, `make register-gemini-enterprise`, `make inspector`, and the related local-development targets.
- Data ingestion, observability, and Gemini Enterprise registration guidance.
- Cloud-provider prerequisites such as GitHub CLI, gcloud, Terraform, repository ownership, and generated deployment metadata.

## Excludes
- New-project template selection belongs in `project-scaffolding`.
- In-place project edits and upgrades belong in `project-maintenance`.

## Read first
- `../../references/cli-reference.md` for command routing.
- `../../references/package-overview.md` for install and sanity-check guidance.
- `references/workflows.md` for the end-to-end deployment flow.
- `references/ci-cd-reference.md` for `setup-cicd` details.
- `references/generated-project-commands.md` for the generated Makefile command map.
- `references/data-ingestion.md` for RAG and datastore setup.
- `references/observability.md` for telemetry and BigQuery analytics.
- `references/gemini-enterprise.md` for registration flows.
- `references/troubleshooting.md` for cloud and auth failures.

## Common workflow
1. Confirm whether the user is asking about a generated project, not the source package itself.
2. Decide whether the task is CI/CD bootstrap, runtime deployment, data ingestion, observability, or Gemini Enterprise registration.
3. Check the relevant generated-project command or cloud prerequisite before suggesting a fix.
4. Use the sub-reference pages to explain the concrete command sequence and likely failure points.
5. Route project-generation questions back to `project-scaffolding` and project-maintenance questions back to `project-maintenance`.

## Useful signals
- `setup-cicd`, `Terraform`, `Cloud Build`, `GitHub Actions`, `gcloud`, `gh`, `local-state`
- `make deploy`, `make setup-dev-env`, `make data-ingestion`, `make sync-data`, `make inspector`, `make register-gemini-enterprise`
- `agent_engine`, `cloud_run`, `gke`, `deployment_metadata.json`, `agent card`, `Gemini Enterprise`
- `vertex_ai_search`, `vertex_ai_vector_search`, telemetry, Cloud Trace, BigQuery analytics, observability

## Validation mindset
- Do not claim cloud readiness from package importability alone.
- Distinguish local command discovery from live cloud provisioning.
- Keep destructive cleanup, live-deployment, and credentialed operations out of the default path unless the user explicitly asks for them.
