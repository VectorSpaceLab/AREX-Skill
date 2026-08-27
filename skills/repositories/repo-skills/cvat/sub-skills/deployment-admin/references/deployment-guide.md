# CVAT deployment guide

## Prerequisites

For a typical self-hosted CVAT Community deployment, operators need:

- Docker Engine
- Docker Compose plugin
- Git or access to deployment files
- A Chromium-based browser for the UI
- Enough disk and network bandwidth for CVAT, PostgreSQL, Redis, Open Policy Agent, UI/server images, and optional components

## Quick Docker Compose deployment

```bash
# Optional for non-local access.
export CVAT_HOST=your-host-or-domain

docker compose up -d

docker exec -it cvat_server bash -ic 'python3 ~/manage.py createsuperuser'
```

Open `http://localhost:8080` or the configured host. Newly registered users may not have enough permissions until an admin assigns roles.

## Published images versus source builds

- Default `docker compose up -d` uses image tags controlled by `CVAT_VERSION` defaults in the compose file.
- On a development branch, default behavior may resolve to development images.
- Set `CVAT_VERSION=vX.Y.Z` to pin a published release image when appropriate.
- Use `docker-compose.dev.yml` and `--build` only when developing from source or testing unreleased changes.

## Serverless overlay

To run serverless infrastructure for automatic annotation models:

```bash
docker compose -f docker-compose.yml -f components/serverless/docker-compose.serverless.yml up -d
```

After infrastructure starts, individual model functions still need Nuclio deployment. See `../auto-annotation/references/serverless-models.md`.

## Development/test stack boundaries

Developer docs describe local Python/Node setup, service dependencies, migrations, and test commands. These are not needed for ordinary CVAT operation. Use development/test commands only when the user is modifying CVAT itself or running repo tests.

Common development requirements include Python 3.10+, Node.js 20, Yarn Modern/Corepack, Docker Compose, Redis/PostgreSQL/OPA services, and many Python/system build dependencies. Do not install these broad requirements for ordinary SDK/CLI automation.

## Helm/Kubernetes orientation

The repository includes a Helm chart for Kubernetes deployment. Use it when the user is operating in Kubernetes and needs chart values, image tags, ingress, storage, or service configuration. Prefer Docker Compose for small local/community deployments unless the user explicitly asks for Kubernetes.

## Edition choice

- CVAT Online: browser-only managed service for evaluation or managed workflows.
- CVAT Community: self-hosted open-source stack from this repository.
- CVAT Enterprise: commercial/self-hosted enterprise features and support.
- Labeling Services: outsourced annotation work.

Keep feature availability clear: some advanced analytics, QA, AI agents, SSO, or built-in models may depend on product tier or optional components.
