# Helm Deployment Workflows

## When to read

Read this when the user wants the Instill Core chart rendered or installed on Kubernetes, or when Helm-specific dependency and port-forwarding problems appear.

## Chart shape

- `charts/core/Chart.yaml` names the chart `core` and carries the chart version and `appVersion`.
- The chart depends on `openfga`, `influxdb2`, and `opentelemetry-collector`; `helm dependency update charts/core` is the normal way to refresh those dependencies.
- `charts/core/values.yaml` holds the service image tags and the deployment knobs for API gateway, console, backends, database, Redis, InfluxDB, OpenFGA, and the optional observability stack.

## Install and render commands

- `make helm-run` installs the chart stack using the default Kubernetes edition.
- `make helm-run CI=true` matches the CI test profile.
- `helm dependency update charts/core` refreshes the lockfile-backed chart dependencies.
- `helm template core charts/core` renders the chart without installing it.
- `helm uninstall core` removes the release.

## CI and test profile notes

- `make helm-integration-test` starts Minikube, installs the supporting charts, port-forwards the API gateway and PostgreSQL, and then runs the same service integration checks the compose flow uses.
- The CI profile uses `k8s-ce:test`, disables the observability collector, and zeroes some Ray resources so the chart can run in smaller test clusters.
- The chart install still depends on a Kubernetes cluster that can schedule the platform's database, cache, registry, model, and workflow dependencies.

## Port-forwarding and debugging

- `kubectl port-forward` is used to reach the API gateway and PostgreSQL during the Helm integration test.
- If the port-forward does not bind, the cluster is not ready or another local process already occupies the forwarded port.
- `make down` or `helm uninstall` should be used before a retry so the namespace does not keep stale objects.

## Values and dependencies to remember

- `OBSERVE_ENABLED=true` enables the extra observability stack in the Helm path.
- The chart pulls in external dependencies rather than bundling them in the repo tree, so a fresh clone often needs `helm dependency update charts/core` before the first render or install.
- The chart values align with the service image tags in `.env`; release-maintenance updates both sides when the repo bumps versions.
