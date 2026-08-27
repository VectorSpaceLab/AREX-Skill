# Integration Test Troubleshooting

## Missing `instill` CLI

**Symptoms**: `instill: command not found`, the dummy model build step fails immediately, or the helper cannot infer the SDK path.

**Likely cause**: The Instill SDK CLI is not installed in the current environment.

**Recovery**: Install or activate the environment that provides `instill`, then rerun the model helper or the model-integration Makefile target.

## Inventory file or model directory is missing

**Symptoms**: The build helper warns about skipped models, or the model-integration flow cannot find the inventory path.

**Likely cause**: The checkout is incomplete or the wrong inventory file is being used.

**Recovery**: Verify `integration-test/models/inventory.json` or `inventory-all.json`, confirm the model directories exist, and rerun.

## Local registry or Ray is not healthy

**Symptoms**: The model-integration run reaches the wait step but the models never report `RUNNING`, or the Ray dashboard never stabilizes.

**Likely cause**: The local registry, Ray, or one of the model backend dependencies is not healthy yet.

**Recovery**: Check `docker ps`, inspect the relevant logs, and rerun the workflow after the dependency becomes healthy. Use `make down` before retrying if the stack is stale.

## Model deployment times out

**Symptoms**: `wait-models-deploy` reaches its timeout, or the script prints the final Ray state plus `model-backend-init-model` logs.

**Likely cause**: One of the model deployments never started or the inventory does not match the model directories.

**Recovery**: Recheck the inventory, inspect the model-backend-init-model logs, and confirm the dummy model images were built and pushed to the local registry.

## Kubernetes integration is too slow or undersized

**Symptoms**: `make helm-integration-test` stalls before port-forwarding is ready, or the pods remain Pending.

**Likely cause**: The cluster lacks enough resources for the full platform stack.

**Recovery**: Free cluster resources, start a larger Minikube profile, or stop and ask for a better Kubernetes environment.
