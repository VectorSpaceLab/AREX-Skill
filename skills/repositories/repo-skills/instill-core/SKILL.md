---
name: instill-core
description: "Guides Instill Core Docker Compose, Helm, integration-test, and
  release-maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Instill Core Repo Skill

Use this skill when a task involves the `instill-ai/instill-core` orchestration checkout: local Docker Compose startup, Kubernetes Helm deployment, integration tests and dummy model flows, or maintainer version and release automation.

This repository is an orchestration and deployment repo, not the backend service source tree. It composes prebuilt service images, Helm charts, configs, and test fixtures for the Instill Core platform.

## Before you start

- Confirm which workflow family the user wants: local Compose, Helm/Kubernetes, integration/model tests, or release/version maintenance.
- Work from the target `instill-core` checkout. If the user wants backend code changes, route them to the sibling service repository instead of this skill.
- Run the matching toolchain check before doing anything else: `scripts/check-toolchain.sh --mode <compose|helm|integration|release|all> --repo-root <checkout>`.
- There is no local Python package install step for this repo skill. Use the checkout directly with Docker, Docker Compose v2, Helm, kubectl, and the bundled helpers.

## Choose the route

- [local-compose](sub-skills/local-compose/SKILL.md) for `make run`, `compose-dev`, `compose-run`, service lifecycle, ports, logs, and GPU/observability overlays.
- [helm-deployment](sub-skills/helm-deployment/SKILL.md) for `helm-run`, `helm dependency update`, `helm template`, `kubectl`, and cluster deployment.
- [integration-tests](sub-skills/integration-tests/SKILL.md) for `make integration-test`, `compose-integration-test`, `model-integration-test`, `wait-models-deploy`, and dummy model registry flows.
- [release-maintenance](sub-skills/release-maintenance/SKILL.md) for service version bumps, chart image tag updates, release-please, and GitHub Actions release workflows.

## Quick route cues

- If the user says "start the stack", "bring up the services", or "show me the local ports", choose local-compose.
- If the user says "render the chart", "install on Kubernetes", "port-forward the API", or "explain the chart values", choose helm-deployment.
- If the user says "run the integration suite", "build and push dummy models", or "wait for models to deploy", choose integration-tests.
- If the user says "bump the image tag", "update release metadata", or "prepare a chart release", choose release-maintenance.
- When a request combines routes, start with the route that matches the target environment and then consult the shared configuration reference.

## Shared readiness checks

- Compose: Docker, Docker Compose v2, `make`, and `jq`; add `yq` if the host exposes NVIDIA GPUs.
- Helm: `helm`, `kubectl`, and `make`.
- Integration: Docker, `make`, `jq`, `python3`, and `instill` when you need to execute the dummy model helper.
- Release: `git` and `python3` for the local helper; CI release jobs still need their GitHub secrets and signing keys.

## Common mistakes

- Treating this repo as the backend source tree instead of the orchestration checkout.
- Forgetting `make down` before retrying a stale compose run.
- Assuming Helm chart values and Compose env values are interchangeable without checking the configuration map.
- Trying to run the CI release workflows directly instead of distilling their local-maintenance behavior.

## If the request is mixed or unclear

- Start with the runtime target, then read the shared configuration map.
- If the user mentions both Compose and Helm, identify which environment they want first.
- If the user mentions both runtime and release changes, split the task between the runtime route and release-maintenance.
- When in doubt, prefer the route that can answer the user's immediate question without touching the other environment.

## Confidence check

- If the task is still fuzzy, read the shared configuration and troubleshooting references first, then pick the route.

## Shared references

- Read [configuration](references/configuration.md) for service ports, environment knobs, compose overlays, and the main health endpoints.
- Read [troubleshooting](references/troubleshooting.md) for cross-cutting Docker, Compose, Helm, GPU, and model-run failures.
- Read [repo-provenance](references/repo-provenance.md) before deciding whether this skill matches the current checkout or needs a refresh.

## Shared scripts

- Run [check-toolchain.sh](scripts/check-toolchain.sh) first to confirm the required CLI tools for the workflow you chose.
- Use [build-and-push-models.py](scripts/build-and-push-models.py) when you need the dummy model build/push flow as a standalone helper.
- Use [update-service-version.py](scripts/update-service-version.py) when you need a local, reviewable helper for bumping `.env` and chart image tags.

## What this skill does not do

- It does not edit the service source code in sibling repositories.
- It does not replace Helm or Docker Compose with package installation instructions.
- It does not run the remote GitHub Actions workflows; it distills their local-equivalent commands and guardrails.

## Staleness check

If the checkout commit, branch, chart version, release metadata, or dirty paths differ from [repo-provenance](references/repo-provenance.md), refresh the skill before relying on it.
