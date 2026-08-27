# Integration Test Workflows

## When to read

Read this when the user wants one of the repo's test suites or when the dummy model registry flow is part of the task.

## Compose integration flow

`make compose-integration-test` does three things:

1. Builds the development image.
2. Launches the compose stack in the test edition with `ENV_SECRETS_COMPONENT_TEST`.
3. Runs the backend integration tests for `mgmt-backend`, `pipeline-backend`, and `model-backend` inside the platform container.

This flow is the best choice when the user wants the backend service checks but does not need Kubernetes.

## Model integration flow

`make model-integration-test` does three things:

1. Starts a local registry.
2. Builds and pushes the dummy models listed in `integration-test/models/inventory.json`.
3. Starts the compose-dev stack with `INITMODEL_ENABLED=true` and waits for the model backend to report that every dummy model is running.

The default inventory is intentionally small; `integration-test/models/inventory-all.json` holds the larger CPU-only fixture set.

## Helm integration flow

`make helm-integration-test` does the same backend checks through a Kubernetes cluster instead of local Docker Compose.

The workflow used by the Makefile:

- starts Minikube,
- installs the supporting charts,
- port-forwards the API gateway and PostgreSQL,
- waits for the ports to open,
- and then runs the backend integration tests from a container attached to the host network or host.docker.internal path.

## Dummy model build helper

`build-and-push-models.py` mirrors the repository's dummy model build/push logic but adds a safe dry-run mode and explicit error handling for missing inventory directories or missing `instill` CLI support.

Use it when you need to inspect or reproduce the model build commands without immediately pushing artifacts.
