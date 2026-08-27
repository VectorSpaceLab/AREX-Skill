---
name: api-service
description: "Operate the apod-api Flask service locally or from an API client:
  start it safely, construct valid APOD queries, interpret responses and errors,
  and troubleshoot upstream, cache, CORS, and static-asset behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# APOD API service

Use this sub-skill when the task is to run `apod-api`, query `/v1/apod`, choose
`date`, `count`, `start_date`, or `end_date`, diagnose Flask 400/404 responses,
check the service version, or investigate NASA APOD availability.

## Route

1. Read [API reference](references/api-reference.md) before constructing a
   request. It is the authority for the implemented route, query combinations,
   boolean parsing, response fields, and error envelopes.
2. Follow [workflows](references/workflows.md) to install the public runtime,
   inspect routes without network access, run the bounded startup wrapper, and
   issue client requests.
3. Use [troubleshooting](references/troubleshooting.md) for malformed input,
   missing routes, APOD HTML/network failures, the volatile cache, static
   fallback assets, and missing concept-tag credentials.
4. Keep standalone JSON accessors and image conversion in
   [parser-and-media](../parser-and-media/SKILL.md). Keep Gunicorn, Docker,
   Compose, and Locust operations in
   [deployment-and-operations](../deployment-and-operations/SKILL.md).
5. For repository-wide issues, also consult the shared
   [troubleshooting guide](../../references/troubleshooting.md).

## Safe operating boundary

The service scrapes the live APOD website; a successful request is therefore a
network-dependent observation, not an offline fixture lookup. `concept_tags`
requires a credential-bound Alchemy integration and is deliberately documented
as degraded when that credential is absent. Do not put API keys or credentials
in commands, scripts, or skill files.

The distribution declares version `1.1.0` and Python `>=3.12`; the Flask service
itself returns `service_version: "v1"`. The current project metadata is not
safe to treat as a default editable setuptools install: flat-layout discovery
sees top-level `apod`, `apod_parser`, `static`, `templates`, and `skills` as
ambiguous. The workflow documents a non-editable runtime setup instead of
hiding this packaging limitation.

## Verification hooks

The bundled `scripts/run_service.py` must pass `--help` and
`--inspect-routes` without contacting APOD. Whole-skill integration should
later run the safe application-import and custom-404 candidates, then add
synthetic conflicting-query and upstream-outage cases before claiming native
service coverage.
