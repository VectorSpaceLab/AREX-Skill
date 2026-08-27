---
name: integration-tests
description: "Guides Instill Core compose, Helm, model-integration, and dummy
  model registry test workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Integration Tests

Use this route when the user wants to run the repo's integration suites or the dummy model build/push flow that feeds the model initialization path.

## Use this when the request mentions

- `make integration-test`, `make compose-integration-test`, `make model-integration-test`, or `make helm-integration-test`.
- `make build-and-push-models` or `make wait-models-deploy`.
- `integration-test/models`, `inventory.json`, `inventory-all.json`, or the dummy model fixtures.
- Ray Serve readiness, local registry population, or model initialization issues.

## What belongs here

- Compose integration checks that exercise mgmt, pipeline, and model backend tests inside the compose container image.
- Helm integration checks that run the same backend tests through Kubernetes port-forwarding.
- Dummy model inventory, build, push, and model initialization flows.
- Readiness and troubleshooting for the local registry, Ray, Temporal, PostgreSQL, Redis, and OpenFGA dependencies used by the model path.

## What does not belong here

- Generic local stack startup; use [local-compose](../local-compose/SKILL.md).
- Helm install/render operations that do not touch the integration suites; use [helm-deployment](../helm-deployment/SKILL.md).
- Version bumps and release PRs; use [release-maintenance](../release-maintenance/SKILL.md).

## Core workflow

1. Run `../../scripts/check-toolchain.sh --mode integration --repo-root <checkout>`.
2. Read the integration workflow reference and the model inventory reference.
3. Use `make compose-integration-test` when you want the compose-backed integration suite.
4. Use `make model-integration-test` when you need to build, push, and initialize the dummy models.
5. Use `make helm-integration-test` when you want the Kubernetes-backed integration suite.
6. Use `../../scripts/build-and-push-models.py` directly when you need a standalone helper for the inventory-driven model build/push stage.

## Quick decision cues

- Choose `make compose-integration-test` when you only need the backend service checks in Compose.
- Choose `make model-integration-test` when the task depends on the local registry, dummy model inventory, or init-model flow.
- Choose `make helm-integration-test` when the same backend checks need to run through Kubernetes port-forwarding.
- Use `../../scripts/build-and-push-models.py` in dry-run mode when you need to inspect the model build/push commands without executing them.
- Reach for `inventory-all.json` when you want the larger dummy model set instead of the tiny default inventory.

## Common mistakes

- Running the model helper in execute mode before the `instill` CLI or SDK environment exists.
- Forgetting that the default inventory is intentionally tiny and will not cover every dummy task.
- Treating a missing model directory warning as success instead of fixing the inventory or the fixture tree.
- Forgetting that Helm integration still needs a real cluster, not just the chart files.

## If the request is mixed or unclear

- Choose this route when the user wants the integration suites or the model-initialization path.
- If the user only needs the stack running, send them to the Compose route instead.
- If the user only needs chart rendering or install guidance, send them to the Helm route instead.
- Use the model inventory reference when the request is about dummy models or the local registry.

## Read these references

- [workflows](references/workflows.md) for the end-to-end integration command map.
- [model inventory](references/model-inventory.md) for the dummy model directories and inventory shape.
- [troubleshooting](references/troubleshooting.md) for registry, Ray, timeout, and missing-CLI failures.
- [check-toolchain.sh](../../scripts/check-toolchain.sh) before the first run.

## Useful commands

- `make compose-integration-test` runs the compose suite.
- `make model-integration-test` runs the model registry and initialization suite.
- `make helm-integration-test` runs the Kubernetes suite.
- `python ../../scripts/build-and-push-models.py --inventory-dir integration-test/models --registry-url localhost:5001 --execute` builds and pushes the dummy models when you truly want to execute the networked step.

## Exit criteria

A future agent should be able to explain which integration path is being exercised, identify the dummy model inventory in use, and understand what to inspect when a model deployment times out.
