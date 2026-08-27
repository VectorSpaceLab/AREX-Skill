---
name: deployment-admin
description: "Deploy and administer self-hosted CVAT with Docker Compose,
  serverless overlays, Helm orientation, superusers, and service
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# CVAT deployment and administration

Use this sub-skill when the user asks how to start a self-hosted CVAT Community stack, choose Docker Compose overlays, set `CVAT_HOST` or `CVAT_VERSION`, create an admin account, enable serverless/analytics/cloud-related components, orient to Helm/Kubernetes deployment, or troubleshoot service startup and access problems.

## Route first

- Read `references/deployment-guide.md` for self-hosted Docker Compose and high-level Helm/Kubernetes orientation.
- Read `references/configuration.md` for environment variables, compose overlays, admin commands, and service boundaries.
- Read `references/troubleshooting.md` for Docker, port, browser, migration, version, serverless, and worker issues.
- Use `scripts/docker_compose_command_builder.py` to generate reviewable Compose commands without executing them.

## Minimal community stack

```bash
# Optional: expose through a host/domain rather than localhost.
export CVAT_HOST=your-host-or-domain

docker compose up -d

docker exec -it cvat_server bash -ic 'python3 ~/manage.py createsuperuser'
```

Open the web UI in a Chromium-based browser. CVAT primarily targets Chrome/Chromium; Safari/WebKit is not supported and Firefox may have caveats.

## Common overlays

```bash
# Development-style stack with source builds.
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Add serverless infrastructure for automatic annotation models.
docker compose -f docker-compose.yml -f components/serverless/docker-compose.serverless.yml up -d

# Use a specific published image tag instead of the default branch behavior.
CVAT_VERSION=v2.71.0 docker compose up -d
```

The exact overlay set must match the user's goal. Do not start or rebuild services unless the user explicitly approves those side effects.

## Boundaries

- Use `../sdk-automation/SKILL.md` for Python API automation against a running server.
- Use `../cli-automation/SKILL.md` for `cvat-cli` operations.
- Use `../dataset-ops/SKILL.md` for import/export/data-format issues.
- Use `../auto-annotation/SKILL.md` for AA function implementation and Nuclio model deployment details.

## Safety defaults

- Treat `docker compose down -v`, volume removal, database reset, and cleanup commands as destructive; ask before suggesting execution.
- Record whether a command builds images, downloads images, starts services, mutates a database, or opens a public network endpoint.
- For public access, require a deliberate `CVAT_HOST`, TLS/reverse proxy, and credential plan.
- Keep enterprise/online plan features distinct from CVAT Community self-hosted operations.
