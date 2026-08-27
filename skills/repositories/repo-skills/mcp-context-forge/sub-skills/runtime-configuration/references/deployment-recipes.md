# Deployment recipes

Use this reference to choose a deployment lane without mixing incompatible defaults.
It stays at the checklist level on purpose.

## 1) PyPI or editable checkout

Choose this when you want the smallest possible install surface.

- PyPI: `pip install mcp-contextforge-gateway`
- Checkout: `pip install -e .`
- Dev checkout: `make install-dev`
- Validate env: `make check-env`, `make check-env-dev`, or `python scripts/contextforge_env_audit.py .env --example-file .env.example`
- Start:
  - `mcpgateway` for packaged startup
  - `make serve` for production-style local service
  - `make dev` for live reload

## 2) Single container

Choose this when you want a single image with runtime env injection.

- Use `docker run` or `podman run`
- Mount or inject a real `.env` file
- Provide real `JWT_SECRET_KEY` and `AUTH_ENCRYPTION_SECRET`
- Do not commit default or placeholder secrets into the image or the manifest
- Prefer `make docker-run` / `make podman-run` when you want the repo-maintained wrapper

## 3) Compose stack

Choose this when you want the gateway plus supporting services in one local stack.

- `make compose-up` for the main stack
- `make compose-sso` when you need the Keycloak profile
- Expect the gateway to be fronted by the stack's reverse proxy rather than exposed directly
- Use PostgreSQL and Redis for a realistic shared-state setup
- Keep secrets in env files or Compose secrets, not committed values

## 4) Helm / Kubernetes

Choose this when you need a cluster-native deployment.

- Use the `charts/mcp-stack` chart
- Put real secrets in Kubernetes Secrets or an external secret manager
- Use ConfigMaps only for non-secret configuration
- Let the chart handle the higher-level pieces such as PostgreSQL, Redis, ingress, and migrations
- Treat values files as configuration, not secret storage

## 5) Declarative build/deploy with `cforge`

Choose this when you want a YAML-driven build and deploy flow.

- `cforge gateway validate <config>`
- `cforge gateway build <config>`
- `cforge gateway certs <config>`
- `cforge gateway deploy <config>`
- `cforge gateway verify <config>`

This lane is useful when the user wants one config file to generate Compose or
Kubernetes artifacts, especially for plugin-heavy deployments.

## Source script inventory decisions

- `scripts/contextforge-setup.sh` is reference-only. It installs Docker/system packages, changes user or service state, may clone repositories, and can start the Compose stack.
- Do not copy or run cleanup scripts by default. Cleanup utilities can remove containers, volumes, databases, or other operational state.
- The bundled helper for this sub-skill is the read-only env audit script, not a host setup wrapper.

## Decision hints

- Use checkout + `make dev` for iterative local edits.
- Use `make serve` or `mcpgateway` for production-style single-node startup.
- Use Compose when you need the full local service mesh around the gateway.
- Use Helm when the target is a Kubernetes or OpenShift cluster.
- Use `cforge` when the deployment should be generated from a declarative config file.

## Related references

- Runtime settings: [`configuration-and-runtime.md`](configuration-and-runtime.md)
- Entry points: [`../../../references/cli-entrypoints.md`](../../../references/cli-entrypoints.md)
- Package identity: [`../../../references/package-overview.md`](../../../references/package-overview.md)
