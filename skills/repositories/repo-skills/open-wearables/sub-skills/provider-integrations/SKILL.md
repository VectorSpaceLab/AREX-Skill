---
name: provider-integrations
description: "Router for provider strategy, OAuth, workout, 24/7 data, webhook,
  coverage, and sync/backfill work."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Provider Integrations

Use this sub-skill for provider strategy changes, coverage declarations,
provider factory/enum updates, OAuth and webhook wiring, workout and 24/7 data
handlers, historical sync/backfill behavior, and provider-specific tests.

## Route here when the task touches

- `backend/app/services/providers/<provider>/...`
- `backend/app/services/providers/factory.py`
- `backend/app/schemas/enums/provider.py`
- `backend/app/api/routes/v1/meta.py` coverage output
- provider coverage constants or sync/backfill semantics
- provider factory, provider enum, or provider tests
- docs/coverage regeneration for provider inventory changes

## Route elsewhere when the task is mostly about

- generic backend routes, auth, repositories, or service-layer work → `../backend-core/`
- portal coverage UI, settings screens, or route presentation → `../frontend-portal/`

## Read first

1. [Provider strategies](references/provider-strategies.md)
2. [Add provider workflow](references/add-provider-workflow.md)
3. [Coverage and sync](references/coverage-and-sync.md)
4. [Troubleshooting](references/troubleshooting.md)

## Safe helper scripts

- [scripts/provider_inventory.py](scripts/provider_inventory.py) — prints the verified 12-provider inventory; `--help` is available.
- [scripts/generate_coverage_docs.py](scripts/generate_coverage_docs.py) — renders a skill-local coverage summary; safe by default, no network or credentials.

## Keep these aligned

- strategy class name
- component class names
- `ProviderCapabilities` flags
- `ProviderCoverage` constants
- factory match arms
- `ProviderName` enum
- coverage summary / docs regeneration
- provider-specific tests and integration coverage
