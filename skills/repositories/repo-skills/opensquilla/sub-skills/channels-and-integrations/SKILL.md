---
name: channels-and-integrations
description: "Operate OpenSquilla messaging channels, pairings, certification,
  adapter status, and the MCP server bridge."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Channels and Integrations

Use this sub-skill when the task is about OpenSquilla's ingress/egress integration layer on top of the gateway:

- messaging channel catalog, setup, CRUD, status, restart, logout, and live-vs-offline validation;
- channel admission, direct-message pairing, allowlists, group-session scope, approval-code delivery, and operator pairings;
- adapter capability/profile evidence, maturity, delivery diagnostics, transport leases, and certification probes;
- the stdio MCP server bridge launched by `opensquilla mcp-server run`.

This guidance targets OpenSquilla 0.5.3 behavior. Installed-package evidence for this surface included working OpenSquilla help, the channel catalog, and a successful `mcp` import; live provider credentials were not assumed.

## Route before acting

- Gateway installation, gateway lifecycle, bind/port, public exposure, Web UI basics, and `doctor` readiness checks: use [`../setup-and-gateway/SKILL.md`](../setup-and-gateway/SKILL.md).
- Provider API keys, model/router tiers, search providers, and general config precedence: use [`../configuration-and-routing/SKILL.md`](../configuration-and-routing/SKILL.md).
- Non-interactive `agent`/`chat` runs, sessions, diagnostics, sandbox commands, replay, cron, bundle, and automation flags: use [`../cli-and-automation/SKILL.md`](../cli-and-automation/SKILL.md).
- Terminal UI, desktop shell, Web UI presentation, or surface-specific UI failures: use [`../tui-and-desktop/SKILL.md`](../tui-and-desktop/SKILL.md).

Stay in this sub-skill for the integration boundary itself: a channel or MCP bridge may trigger agent turns, tool calls, approvals, and session updates, but those surfaces are reached through the same gateway-backed runtime.

## Fast operating map

1. **Discover the channel catalog.** Run `opensquilla channels types --json` and `opensquilla channels describe <type> --json`; do not assume provider fields from memory. See [`references/commands.md`](references/commands.md).
2. **Add or edit channel config.** Use `opensquilla configure channels` for interactive setup, or `opensquilla channels add|edit` for scripted changes. Config edits require a gateway process restart, not just `channels restart <name>`. See [`references/channel-workflows.md`](references/channel-workflows.md).
3. **Check runtime, not just saved config.** `opensquilla channels list` proves config exists; `opensquilla channels status <name> --json` proves whether the running gateway loaded it and exposes status/capability/diagnostic data. See [`references/runtime-contracts.md`](references/runtime-contracts.md).
4. **Handle pairings deliberately.** Unknown authenticated DMs default to pairing mode. Use `opensquilla channels pairings list|approve|revoke` and treat `--admin` as a host-trust decision for that channel sender. See [`references/runtime-contracts.md`](references/runtime-contracts.md).
5. **Separate offline validation from live certification.** Local schema validation and status are not end-to-end provider proof. `opensquilla channels certify` is environment-only and redacts evidence; outbound tests require explicit side-effect flags and targets. See [`references/channel-workflows.md`](references/channel-workflows.md).
6. **Run the MCP bridge as stdio.** Start a gateway first, then configure the MCP-capable client to launch `opensquilla mcp-server run` or `opensquilla mcp-server run --gateway ws://host:port/ws`. See [`references/mcp-server-bridge.md`](references/mcp-server-bridge.md).
7. **Troubleshoot from the boundary outward.** Start with config/schema, gateway restart state, runtime status, pairing/admission diagnostics, delivery ledger state, then provider credentials/network. See [`references/troubleshooting.md`](references/troubleshooting.md).

## Channel catalog scope

The public channel catalog for this build has eight families: `dingtalk`, `discord`, `feishu`, `matrix`, `qq`, `slack`, `telegram`, and `wecom`. Public vendor adapters are experimental; catalog presence means the adapter is registered and has a setup schema, not that every provider feature is certified.

Important catalog rules:

- `channels describe <type>` is the source of truth for current required fields, secret fields, mode choices, public-URL requirements, optional extras, and restart behavior.
- `matrix` declares the `matrix` optional extra. The MCP bridge separately requires the `mcp` extra.
- Microsoft Teams code exists only as a hidden legacy adapter in this version; do not present it as a supported public channel.

## Safe defaults

- Keep gateway-bound integration surfaces on loopback unless a webhook provider explicitly requires public reachability and the operator has configured a trusted reverse proxy/tunnel plus authentication.
- Prefer `dm_access=pairing` for DMs. Use `open` only for intentionally public bots; use `allowlist` when provider sender IDs are known.
- Keep group sessions in the default per-sender scope unless the room is intentionally collaborative.
- Use the narrowest OpenSquilla permissions and sandbox posture that can complete the task; channel approval or pairing does not bypass host-side tool policy.
- Never paste provider keys, bot tokens, signing secrets, or channel secrets into examples, issue text, source, or generated skill files.

## Bundled scripts

No runtime helper script is bundled for this sub-skill. The useful operations are already exposed as safe OpenSquilla CLI commands, while the repo-owned live smoke scripts require provider credentials, network side effects, or maintainer harness context and are reference-only or excluded from runtime use.
