# Cross-Cutting Troubleshooting

Start with read-only evidence:

```sh
opensquilla --help
opensquilla onboard status
opensquilla gateway status
opensquilla doctor --json
```

## Symptom Routing

| Symptom | First route |
| --- | --- |
| Command not found, onboarding incomplete, gateway stopped, port collision, missing Web assets | setup-and-gateway |
| Provider auth/base URL/model failure, router fallback, missing search key or unexpected config value | configuration-and-routing |
| Session/memory/cron/diagnostics/replay/migration/recovery/sandbox/uninstall issue | cli-and-automation |
| Channel saved but offline, pairing/admission failure, adapter delivery/certification issue, MCP startup failure | channels-and-integrations |
| Skill absent/disabled/shadowed, install identity conflict, MetaSkill compile/run/proposal failure | skills-and-meta |
| TUI render/resize/host crash, plain fallback, artifact preview, desktop startup/packaging issue | tui-and-desktop |

## Common Cross-Cutting Checks

1. Confirm the installed version and inspect current command help; this bundle targets 0.5.3.
2. Separate saved configuration from running state. Many changes need `opensquilla gateway restart` before status reflects them.
3. Check whether the command is gateway-backed. A stopped or differently configured gateway can look like a provider, session, channel, or UI failure.
4. Resolve configuration precedence rather than overwriting values blindly. Prefer environment-variable references for secrets.
5. Separate catalog/schema success from live readiness. Provider, search, and channel catalogs work without proving credentials or network access.
6. Use `opensquilla bundle` for a shareable diagnostic zip even if the gateway cannot start. Review it before sharing; opt-in content and raw diagnostics may expose prompts, tool output, identifiers, or paths.
7. If the source checkout reports missing/stale control UI assets, rebuild the frontend or use an official release wheel. Direct VCS installs do not include generated assets.
8. For router native dependency failures, direct routing can remain usable while the router is disabled. Do not represent that fallback as a live provider success.

## Destructive Recovery

Do not jump from diagnosis to deletion. Preview migration and uninstall operations, preserve session exports where requested, verify process ownership before breaking migration locks, and explain all `reset` or `--purge-*` consequences. Skill catalog mutation and MetaSkill proposal acceptance also require an explicit target and user intent.

## Network and Secrets

Keep the gateway on loopback while troubleshooting unless remote access itself is the task. Never paste provider keys, bot tokens, webhook secrets, exported conversation content, or raw diagnostic payloads into skill files, issues, or command examples.
