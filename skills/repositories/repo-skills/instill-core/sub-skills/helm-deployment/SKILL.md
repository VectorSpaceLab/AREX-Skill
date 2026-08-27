---
name: helm-deployment
description: "Guides Instill Core Helm rendering, Kubernetes deployment, chart
  dependency, and kubectl port-forward workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Helm Deployment

Use this route when the user wants the Instill Core chart rendered, installed, port-forwarded, or debugged on Kubernetes.

## Use this when the request mentions

- `make helm-run`, `make helm-integration-test`, or `make helm-run CI=true`.
- `helm repo add`, `helm dependency update`, `helm template`, `helm install`, or `helm uninstall`.
- `kubectl`, Minikube, namespace cleanup, or Helm chart values under `charts/core`.
- Observability-enabled chart installs or chart dependency troubleshooting.

## What belongs here

- Rendering and installing the chart in `charts/core`.
- Understanding the chart dependencies, values, and service mappings.
- Managing port-forwards and Helm cleanup.
- Reading chart-specific troubleshooting and versioning guidance.

## What does not belong here

- Local Docker Compose startup or container lifecycle; use [local-compose](../local-compose/SKILL.md).
- Dummy model build/push or inventory-driven model initialization; use [integration-tests](../integration-tests/SKILL.md).
- Service version bump PRs and release automation; use [release-maintenance](../release-maintenance/SKILL.md).

## Core workflow

1. Run `../../scripts/check-toolchain.sh --mode helm --repo-root <checkout>`.
2. Read the chart workflow reference before changing values or installing the chart.
3. Use `make helm-run` for the default install path or `make helm-run CI=true` when you need the test profile used by CI.
4. Use `make helm-integration-test` when you want the chart plus service integration checks in a Minikube-style environment.
5. Use `helm uninstall` or `make down` to clean up after the deployment.

## Quick decision cues

- Choose `make helm-run` when you want the default Kubernetes deployment path.
- Choose `make helm-run CI=true` when you need the smaller CI-style profile that the repository uses in tests.
- Choose `make helm-integration-test` when the task is really about the chart plus the backend service checks, not just a render.
- Choose `helm dependency update charts/core` before the first install or render if the chart dependencies are not already resolved.
- Use `helm uninstall` or `make down` before retrying a stale namespace.

## Common mistakes

- Treating `helm-run` as a pure render step when it actually installs the stack.
- Forgetting that the chart depends on external subcharts and may need dependency refresh on a fresh clone.
- Trying to debug Compose-specific issues from the Helm route.
- Forgetting to free Minikube or namespace resources after an interrupted integration run.

## If the request is mixed or unclear

- Choose this route if the user wants the chart rendered or installed, even when they also mention ports or service names.
- If the user only wants a local container stack, send them to the Compose route instead.
- If the user mentions the model inventory or dummy models, send them to the integration-tests route instead.
- When the user asks about chart values, use the chart workflow reference before editing anything.

## Confidence check

- If the install target still looks ambiguous, read the chart workflow reference and the troubleshooting page before making changes.

## Read these references

- [workflows](references/workflows.md) for the chart install and render sequence.
- [troubleshooting](references/troubleshooting.md) for dependency, cluster, and resource failures.
- [configuration](../../references/configuration.md) for ports, overlays, and service mapping.
- [check-toolchain.sh](../../scripts/check-toolchain.sh) before the first install attempt.

## Useful commands

- `helm dependency update charts/core` refreshes the chart dependencies.
- `helm template core charts/core` renders the chart locally.
- `helm install core charts/core` installs the release into the current namespace.
- `make helm-run` orchestrates the full dependency stack and the chart install.

## Exit criteria

A future agent should be able to render the chart, explain the main values, and cleanly install or uninstall the platform without reopening the original chart README.
