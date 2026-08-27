# Deployment Workflows

## Purpose

Use this reference for Nexent Docker, Kubernetes, image, offline package, upgrade, and uninstall workflows. The original deployment scripts are live, checkout-bound operators; this skill distills their decision model and bundles only safe static helpers.

## Docker Compose deployment

Docker is the default local/self-hosted path. The deployment model includes infrastructure, application, data-process, and Supabase components. Infrastructure includes PostgreSQL/Supabase, Redis, Elasticsearch, MinIO, and related services; application/data-process run Nexent backend components.

Typical decisions before running a live Docker deployment:

- Component set: infrastructure is foundational; application, data-process, and Supabase are commonly selected together.
- Port policy: development versus production port exposure.
- Image source: general, mainland, or locally built images.
- Whether an existing env file should be reused or generated from examples.
- Whether persistent volumes must be preserved on uninstall.

Do not run deploy/uninstall from this skill without confirming the target host and data-preservation policy.

## Kubernetes/Helm deployment

Kubernetes deployment renders values from the shared env model into Helm ConfigMaps/Secrets and supports persistence choices such as local, dynamic, or existing claims.

Before changing K8s deployment:

- Identify the value in the shared env/config model first.
- Check Helm chart templates and values together.
- Preserve namespace, storage class, PVC, local-path, and node-name behavior.
- Treat namespace deletion and local PV deletion as destructive operations.

## Image builds and offline packages

Nexent has image build definitions for main, web/docs, data-process, MCP, sandbox, and terminal-style images. Offline packages collect image tar files, load/push helpers, deployment scripts, SQL files, manifests, and checksums.

Use safe static review for most code tasks. Real package build or image push requires Docker, network/registry access, enough disk, and user approval.

## Upgrade and uninstall

Upgrade/uninstall scripts can alter running services and persistent data. Always distinguish:

- Removing application containers/pods but preserving volumes/PVCs.
- Full deletion of volumes, namespaces, or local PV data.
- SQL-only migration changes versus image rebuild requirements.
- Saved deployment options versus explicit CLI flags.

## Monitoring deployment

Monitoring configs include OpenTelemetry collector and backend env flags. When changing telemetry behavior, coordinate:

- Backend constants and monitor SDK behavior.
- Env examples for OTLP endpoints, headers, provider selection, trace content mode, and sampling.
- Docker monitoring compose/assets or K8s chart values.

## Safe static checks

- Use `scripts/check_sql_migration_sync.py` for SQL/init/version presence.
- Use shell syntax checks only when they do not execute deployment logic.
- Use `--help`/argument inspection where a script supports it; many shell scripts are interactive and should not be run just to inspect behavior.
