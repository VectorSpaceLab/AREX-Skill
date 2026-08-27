# Helm Deployment Troubleshooting

## Missing Helm or kubectl

**Symptoms**: `helm: command not found`, `kubectl: command not found`, or the Helm workflow stops before any resources are created.

**Likely cause**: The local Kubernetes toolchain is incomplete.

**Recovery**: Install `helm` and `kubectl`, confirm the cluster context, and rerun `scripts/check-toolchain.sh --mode helm --repo-root <checkout>`.

## Chart dependencies are not ready

**Symptoms**: `helm template` or `helm install` complains about missing dependencies, unresolved subcharts, or a chart lock mismatch.

**Likely cause**: The chart dependencies have not been refreshed in the current checkout.

**Recovery**: Run `helm dependency update charts/core` before retrying the render or install.

## Minikube or another local cluster is undersized

**Symptoms**: Pods stay Pending, the install hangs, or `make helm-integration-test` never reaches the port-forward step.

**Likely cause**: The local cluster does not have enough CPU, memory, or disk for the platform stack.

**Recovery**: Use the larger cluster sizing from the workflow, free resources, or stop and ask for a better Kubernetes environment.

## Port-forwarding never comes up

**Symptoms**: `kubectl port-forward` fails, the test loop never sees a listening local port, or the integration test cannot reach the API gateway or database.

**Likely cause**: The target pod is not running yet or a local process already uses the forwarded port.

**Recovery**: Re-check pod status in the target namespace, clear any stale port-forward, and rerun the workflow.

## Observability or dependencies are inconsistent

**Symptoms**: Grafana, Tempo, Loki, or Prometheus fail to appear when `OBSERVE_ENABLED=true`, or the install references values that do not match the chart.

**Likely cause**: The values file and the selected profile are out of sync.

**Recovery**: Re-read the chart workflow reference, confirm the active values path, and retry with a clean namespace.
