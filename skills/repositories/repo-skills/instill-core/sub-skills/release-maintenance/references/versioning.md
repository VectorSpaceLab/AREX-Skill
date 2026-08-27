# Instill Core Versioning Map

## Purpose

Read this when you need to change a service image tag, inspect the chart image tag, or preview how the repo keeps version numbers aligned.

## Service to version mapping

| Service input | `.env` variable | Helm values path | Notes |
| --- | --- | --- | --- |
| `api-gateway` | `API_GATEWAY_VERSION` | `apiGateway.image.tag` | Public API gateway image. |
| `mgmt` | `MGMT_BACKEND_VERSION` | `mgmtBackend.image.tag` | User and usage backend. |
| `pipeline` | `PIPELINE_BACKEND_VERSION` | `pipelineBackend.image.tag` | Pipeline backend and worker image. |
| `artifact` | `ARTIFACT_BACKEND_VERSION` | `artifactBackend.image.tag` | Artifact backend and worker image. |
| `model` | `MODEL_BACKEND_VERSION` | `modelBackend.image.tag` | Model backend, worker, and init-model image. |
| `console` | `CONSOLE_VERSION` | `console.image.tag` | Console UI image. |
| `ray` | `RAY_VERSION` | none in the current chart tree | Local Compose only unless the chart later adds a Ray values block. |

## Repo-wide release numbers

- `release-please/manifest.json` currently records the repository release version used by the release-please action.
- `charts/core/Chart.yaml` carries the chart version and `appVersion` used by the Helm release workflow.
- `README.md` includes the release badge that the release-please configuration keeps in sync.

## Practical rule

If the user asks for a local version bump, update the matching `.env` variable and the chart tag when the chart actually defines one. If the user asks for a release action, treat the GitHub Actions workflows as the source of truth and keep the change reviewable in a PR.
