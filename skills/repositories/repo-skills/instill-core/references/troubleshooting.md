# Instill Core Troubleshooting

## Purpose

Read this before retrying a workflow when a Compose, Helm, integration, or release step fails. The goal is to identify the likely missing prerequisite quickly and decide whether to fix the environment, adjust the workflow, or stop for a bigger dependency.

## Cross-cutting failure surfaces

### Docker or Compose is missing

**Symptoms**: `docker: command not found`, `docker compose` errors, no containers start, or the Makefile stops before pulling images.

**Likely cause**: Docker Engine or the Compose v2 plugin is not installed or not reachable from the current shell.

**Recovery**: Install or start Docker, then rerun `scripts/check-toolchain.sh --mode compose --repo-root <checkout>` and retry the requested `make` target.

### GPU host selected the NVIDIA path but `yq` is missing

**Symptoms**: Compose startup fails only on GPU-capable hosts, often while the Makefile tries to rewrite `docker-compose-nvidia.yml`.

**Likely cause**: The Makefile detected `nvidia-smi`, selected the GPU Ray image path, and expected `yq` to patch the NVIDIA overlay.

**Recovery**: Install `yq` or move to a CPU-only environment where the GPU probe is absent. Then rerun the Compose command.

### Port collisions or stale containers

**Symptoms**: Bind failures on 8080, 3000, 8081-8084, 5432, 6379, 8086, 5001, 8265, or similar ports; health checks never become ready; a second run fails immediately.

**Likely cause**: A previous Compose or Helm run left containers, port-forwards, or volumes in place.

**Recovery**: Run `make down` for Compose workflows or the matching `helm uninstall` / namespace cleanup for Helm workflows, then retry.

### Secrets or `.env` mismatches

**Symptoms**: Missing OAuth or API-key settings, console startup warnings, or backend containers failing because an expected `CFG_...` variable is blank.

**Likely cause**: The checkout is missing the expected secret files, or the local `.env` does not match the deployment flavor you selected.

**Recovery**: Verify the active `.env` and secrets files for the chosen workflow, then rerun the matching toolchain check.

### Helm or kubectl is missing

**Symptoms**: `helm: command not found`, `kubectl: command not found`, cluster install failures, or port-forward commands fail.

**Likely cause**: The local Kubernetes toolchain is incomplete.

**Recovery**: Install `helm` and `kubectl`, confirm the cluster context, then rerun `scripts/check-toolchain.sh --mode helm --repo-root <checkout>`.

### Model build and push cannot find `instill`

**Symptoms**: `instill: command not found`, build steps fail before the dummy models are built, or the helper cannot determine the SDK path.

**Likely cause**: The Instill SDK CLI is not installed in the active environment.

**Recovery**: Install or activate the environment that provides `instill`, or pass an explicit SDK path to the bundled model helper before rerunning the model workflow.

### Integration model deployment times out

**Symptoms**: `wait-models-deploy` never sees all dummy models in `RUNNING`, Ray Serve remains unhealthy, or `model-backend-init-model` logs point to inventory or registry issues.

**Likely cause**: The local registry, Ray, Temporal, PostgreSQL, Redis, or OpenFGA dependency is not ready, or the model inventory does not match the dummy model directories.

**Recovery**: Inspect the helper output, verify the inventory file and model directories, check `docker logs model-backend-init-model --tail 100`, and rerun after the dependency that failed is healthy.

### Cluster deployment is too small

**Symptoms**: `make helm-integration-test` hangs, Minikube never becomes ready, or pods stay Pending.

**Likely cause**: The local Kubernetes cluster does not have enough CPU, memory, or disk for the chart stack.

**Recovery**: Use the Minikube sizing from the workflow, free resources, and retry. If the cluster still cannot support the stack, stop and ask for a larger Kubernetes environment.

## When to stop

Stop and ask for help when the failure depends on network access, registry credentials, a Kubernetes cluster, GPU hardware, or another external service that the current environment cannot provide.
