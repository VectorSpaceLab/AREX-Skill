---
name: opensquilla
description: "Route OpenSquilla installation, gateway, provider and
  SquillaRouter configuration, CLI automation, channels and MCP, Skills and
  MetaSkills, and TUI or desktop work to the right bundled sub-skill."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenSquilla Repo Skill

Use this skill when a task names OpenSquilla or its `opensquilla` CLI, gateway,
SquillaRouter, provider/search configuration, sessions and automation, messaging
channels, MCP bridge, Skill/MetaSkill catalog, terminal UI, Web UI, or desktop
runtime. This root is a router: load the narrowest sub-skill before prescribing
commands or changing state.

## Route Map

| User intent | Read |
| --- | --- |
| Install OpenSquilla, run onboarding, start or diagnose the gateway, open the Web UI, or choose release versus source installation | [`sub-skills/setup-and-gateway/SKILL.md`](sub-skills/setup-and-gateway/SKILL.md) |
| Configure providers, models, API-key environment variables, SquillaRouter modes, web search, or configuration precedence | [`sub-skills/configuration-and-routing/SKILL.md`](sub-skills/configuration-and-routing/SKILL.md) |
| Run or automate chat/agent/code tasks, sessions, memory, cron, cost, diagnostics, replay, migration, recovery, sandbox, reset, init, bundle, dist, or uninstall | [`sub-skills/cli-and-automation/SKILL.md`](sub-skills/cli-and-automation/SKILL.md) |
| Configure messaging channels, pairings, admission, certification, delivery diagnostics, or the stdio MCP server bridge | [`sub-skills/channels-and-integrations/SKILL.md`](sub-skills/channels-and-integrations/SKILL.md) |
| Discover, install, update, publish, inspect, or troubleshoot Skills and MetaSkills, taps, runs, or proposals | [`sub-skills/skills-and-meta/SKILL.md`](sub-skills/skills-and-meta/SKILL.md) |
| Diagnose terminal rendering, OpenTUI companion behavior, Web UI presentation/artifact previews, or desktop packaging and runtime | [`sub-skills/tui-and-desktop/SKILL.md`](sub-skills/tui-and-desktop/SKILL.md) |

When a request crosses boundaries, start with setup/gateway readiness, then load
each relevant specialist. Keep UI presentation separate from provider routing,
and keep channel transport separate from ordinary chat/session automation.

## Safe First Checks

Prefer read-only inspection before state changes:

```sh
opensquilla --help
opensquilla onboard status
opensquilla gateway status
opensquilla doctor
```

The bundled [`scripts/runtime-health.sh`](scripts/runtime-health.sh) performs a
safe local snapshot. It never starts a gateway, changes configuration, calls an
LLM/search provider, installs dependencies, or mutates the Skill catalog.

## Root References

- [`references/overview.md`](references/overview.md) — product model, quick path, and routing boundaries.
- [`references/cli-catalog.md`](references/cli-catalog.md) — command families mapped to sub-skills and gateway dependence.
- [`references/runtime-surfaces.md`](references/runtime-surfaces.md) — gateway, CLI, TUI, Web, desktop, channels, and MCP ownership.
- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting symptom-first triage.
- [`references/repo-provenance.md`](references/repo-provenance.md) — inspected revision, evidence, and verification limits.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) — machine-readable router placement metadata.

## Operating Rules

1. Treat provider keys, channel tokens, webhook secrets, exported sessions, raw
diagnostics, and content-bearing bundles as sensitive. Prefer environment
variable references and redacted output.
2. Distinguish local catalog/schema checks from live readiness. A listed
provider, search adapter, or channel type is not proof that credentials or
network access work.
3. Do not expose a gateway beyond loopback without an explicit operator request,
authentication, and a reviewed reverse-proxy or tunnel boundary.
4. Call out state-changing commands before use: configuration edits, gateway
restart/reload, Skill install/update/uninstall/reload/publish, proposal accept,
cron mutation, migration apply, reset, and uninstall purge options.
5. Use release-install guidance for ordinary users. Source-build, browser,
Electron, Bun/Node, and maintainer harness instructions apply only to a checkout.
6. This bundle targets OpenSquilla 0.5.3. Re-check current command help and the
provenance reference when operating a materially different release.

## Verification Boundary

The skill was built from source inspection and CPU-only installed-package checks.
CLI help, selected imports, and local catalogs were checked; no credentialed LLM,
search, channel, external MCP client, browser/Electron end-to-end, or public
gateway test is implied. Never turn those live checks on merely to validate this
skill bundle.
