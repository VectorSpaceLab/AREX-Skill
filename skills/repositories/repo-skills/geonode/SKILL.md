---
name: geonode
description: "Operate and extend GeoNode geospatial content-management
  deployments, resource APIs, uploads, metadata/catalogues, GeoServer security,
  harvesting, and administration with explicit service and safety gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# GeoNode

Use this skill when a task names GeoNode, asks about its Django/REST APIs,
geospatial resource catalogues, dataset/document/map uploads, GeoServer
publication, metadata/CSW, harvesting, or GeoNode deployment operations.
This graph covers the GeoNode 5.1-style package and service topology. It is
operating guidance for a later Researcher; it is not a claim that external
services are running.

## Route by task

- **Install, Docker/bare deployment, settings, environment files, startup,
  hardening:** read [setup-and-configuration](sub-skills/setup-and-configuration/SKILL.md).
- **Datasets, documents, maps, geoapps, REST v2, uploads, execution requests,
  downloads, or resource permissions:** read [resource-and-api](sub-skills/resource-and-api/SKILL.md).
- **Metadata schemas/handlers, localization, CSW/catalogue, search, facets,
  or metadata-driven discovery:** read [metadata-and-catalogue](sub-skills/metadata-and-catalogue/SKILL.md).
- **GeoServer, OGC URLs, OAuth2/OIDC, GeoFence, groups, permissions, remote
  services, or proxy failures:** read [geoserver-and-security](sub-skills/geoserver-and-security/SKILL.md).
- **Harvesting, indexing, Celery/Redis, management commands, migrations,
  thesauri, backup/restore, or operational recovery:** read [harvesting-and-admin](sub-skills/harvesting-and-admin/SKILL.md).
- For a request spanning routes, start here, identify the service boundary,
  then follow each linked sub-skill in dependency order rather than duplicating
  commands.

## Installation and inspection

For a released distribution, install the package in an isolated environment
using the project-supported Python version and geospatial prerequisites. A
source/development checkout commonly needs PostgreSQL client headers for
`psycopg2` and a matching GDAL native library for the Python `GDAL` binding.
Do not install into a shared production environment just to inspect APIs.

```bash
python -m pip install GeoNode
python -c "import geonode; print(geonode.__version_str__)"
```

For a repository checkout, use the repository's documented editable install
only in a disposable development environment, then confirm both the Python
package and native geospatial imports. A successful import does not validate
PostGIS, GeoServer, Redis/Celery, Nginx, remote OGC endpoints, credentials, or
browser behavior.

## Operating contract

1. State the GeoNode release/configuration shape and target topology before
   changing settings or sending API requests.
2. Separate the Django, database/PostGIS, GeoServer, broker/worker, catalogue,
   proxy, and browser planes. A green web process is not proof that uploads,
   publication, search, or harvesting will finish.
3. Prefer read-only inspection, `--help`, schema discovery, bounded API reads,
   and tiny local validators before mutation or network work.
4. Preserve resource identifiers, execution/job identifiers, response bodies,
   service logs, and exact configuration gates. Redact passwords, tokens,
   cookies, private URLs, and secret-bearing payloads.
5. For destructive or service-backed work, require a narrow target, tested
   backup/rollback, explicit prerequisites, and a post-change verification.
6. Report results as package-valid, settings-valid, service-ready, or
   production-reviewed; never collapse these states.

## Shared safeguards

- Use [troubleshooting](references/troubleshooting.md) for cross-cutting
  install, import, settings, database, service, authentication, and async
  failures.
- Run [check_service_urls.py](scripts/check_service_urls.py) only with explicit
  non-secret URLs or host/port checks; it never authenticates or changes state.
- Read [repository provenance](references/repo-provenance.md) before comparing
  this graph with a changed checkout. If the commit, package entry points, or
  major evidence paths differ, request a refresh rather than trusting stale
  instructions.

## Cross-route handoffs

- Setup establishes URLs, databases, workers, and service readiness; API and
  publication routes consume those facts.
- Resource operations may create asynchronous execution requests and metadata;
  route their state to harvesting/admin and their discovery state to
  metadata/catalogue.
- Metadata validity is independent of CSW/index availability. GeoServer style,
  OGC, and permission behavior belongs to the GeoServer/security route.
- Management commands can be destructive even when their parser is available;
  use the administration route's safety classification.
