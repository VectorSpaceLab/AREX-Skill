# OpenSquilla Overview

OpenSquilla 0.5.3 is a Python 3.12 microkernel agent runtime. A local gateway owns durable runtime state and exposes the Web UI, sessions, memory, scheduling, channels, cost, and diagnostics surfaces. The CLI also provides local or standalone workflows, including one-shot agents, guarded code tasks, replay, migration, recovery, distribution inventories, bundles, initialization, and uninstall.

## Ordinary User Path

1. Install an official release with the needed extras; use a source checkout only for development.
2. Run `opensquilla onboard` (or the idempotent `opensquilla onboard --if-needed`).
3. Start the gateway with `opensquilla gateway run` or `opensquilla gateway start --json`.
4. Check `opensquilla onboard status`, `opensquilla gateway status`, and `opensquilla doctor`.
5. Open the local control UI at `http://127.0.0.1:18791/control/` or use `opensquilla chat`.
6. Configure only the provider, router, search, channel, permission, and optional integration surfaces the user needs.

## Capability Boundaries

- **Setup and gateway** owns installation, onboarding, lifecycle, bind/port, readiness, and basic Web UI access.
- **Configuration and routing** owns provider/model catalogs, credentials, model/base URL precedence, SquillaRouter modes, and search providers.
- **CLI and automation** owns ordinary agent/chat workflows plus sessions, memory, cron, diagnostics, cost, replay, migration, recovery, sandbox, and cleanup.
- **Channels and integrations** owns messaging transports, admission/pairing, adapter status/certification, delivery diagnostics, and the MCP stdio bridge.
- **Skills and MetaSkills** owns the managed catalog, routing eligibility, taps, installs/updates, MetaSkill runs and proposals, and authoring workflow.
- **TUI and desktop** owns renderer selection, companion-host behavior, visual presentation, artifact previews, and packaged desktop runtime.

## Safety Defaults

Keep the gateway on loopback unless public exposure is explicitly designed and authenticated. Store secrets in environment variables or protected configuration, never in examples or logs. Start with read-only list/status/doctor commands. Treat diagnostic bundles and session exports as potentially sensitive even when default redaction is enabled.

OpenSquilla's local catalogs describe registered capability, not live readiness. Live provider, search, channel, browser, or Electron tests require the corresponding dependencies, credentials, network, and explicit user intent.
