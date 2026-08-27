---
name: services-and-extensions
description: "Routes ODS service manifests, Docker Compose layering, extension
  catalog behavior, install/update/rollback semantics, compose security
  scanning, and the service registry."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Services And Extensions

## Purpose

Use this sub-skill for ODS work that touches service manifests, compose overlays,
extension catalog entries, extension enable/disable/install/update/rollback
semantics, security-scanned compose resolution, or the service registry view of
enabled services.

This sub-skill is router-like. The detailed contracts live in:

- `references/compose-and-extensions.md`
- `references/service-catalog.md`
- `references/troubleshooting.md`
- `scripts/extension_manifest_summary.py`

## Covers

- `extensions/services/*/manifest.yaml` and extension compose overlays
- bundled extension library / installable catalog semantics
- category, dependency, alias, port, GPU backend, and `service.llm` contracts
- compose layering and security scan behavior
- enable/disable/install/update/rollback state rules
- service registry behavior and manifest-driven discovery

## Route elsewhere

- Dashboard Extensions page implementation -> `dashboard-and-api`
- Exact `ods enable/disable/list/audit` command behavior and other host CLI details -> `ops-cli-and-host-tools`
- Installer phase ordering / platform install behavior -> `installers-and-platforms`
- Model selection, tier mapping, and backend capability decisions -> `hardware-and-models`

## Fast path

1. Run the bundled read-only summary helper on the relevant catalog root.
2. Read `references/compose-and-extensions.md` for the manifest and compose contract.
3. Read `references/service-catalog.md` for the current bundled service snapshot.
4. Use `references/troubleshooting.md` when a manifest, overlay, or lifecycle action fails.
5. Only then edit manifests, compose fragments, or library entries.

## Working rules

- Prefer read-only inspection first; the summary helper is safe by default and supports `--help`.
- Keep ports loopback-bound unless the manifest explicitly opts into host networking.
- Keep new service ids and aliases unique; do not shadow core service ids.
- For LLM-consuming services, declare `service.llm` and default to the gateway route instead of pinning a concrete model name.
- When a service is enabled or disabled, the compose file marker is the source of truth: `compose.yaml` means enabled, `compose.yaml.disabled` means disabled.

## What to check before changing a service

- The manifest schema version and required fields
- The category (`core`, `recommended`, `optional`)
- The compose file location and overlay naming
- GPU backend compatibility
- Alias collisions and dependency references
- Security scan failure modes for any new compose content
- Whether the service is installable from the bundled library or is only a bundled runtime service

If the task is about portal UI behavior or host command syntax, switch
sub-skills instead of expanding this one.
