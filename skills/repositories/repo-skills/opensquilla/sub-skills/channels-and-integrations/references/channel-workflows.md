# Channel configuration and validation workflows

This reference covers the operating flow for messaging adapters. For first-run install and gateway lifecycle, see [`../../setup-and-gateway/SKILL.md`](../../setup-and-gateway/SKILL.md). For provider/model/search credentials, see [`../../configuration-and-routing/SKILL.md`](../../configuration-and-routing/SKILL.md).

## Standard setup sequence

1. **Confirm gateway readiness.** A channel is loaded by the gateway process, so `opensquilla gateway status` and `opensquilla doctor` should be clean enough before channel debugging.
2. **Discover the exact schema.** Run `opensquilla channels describe <type> --json`. Treat that output as authoritative for required fields, secret fields, transport choices, optional extras, and restart behavior.
3. **Choose transport and exposure.** Prefer outbound websocket/polling transports when available. Webhooks require the gateway to be reachable by the provider and protected by the operator's chosen gateway auth/reverse-proxy boundary.
4. **Save configuration.** Use `opensquilla configure channels` or `opensquilla channels add|edit`.
5. **Restart the gateway process.** Config writes set restart-required state. `channels restart <name>` only applies to already-loaded adapters and cannot add new HTTP webhook routes to the running app.
6. **Check runtime status.** Use `opensquilla channels status <name> --json`. `channels list` only shows saved config; it does not prove runtime load or provider connection.
7. **Resolve pairing/admission.** If `pendingPairings` is nonzero or a DM sender reports a pairing notice, list and approve/revoke pairings deliberately.
8. **Run optional live proof only when credentialed.** Use `channels certify` for environment-only provider probes. Keep live delivery tests opt-in and side-effect-aware.

## Provider/transport notes

| Family | Typical transport | Public URL condition | Notes |
| --- | --- | --- | --- |
| `slack` | Socket Mode websocket or Events API webhook | Socket Mode: no. Webhook mode: yes. | Socket Mode needs bot token plus app-level token. Webhook mode needs bot token plus signing secret and reachable request URL. Leave default channel blank to reply to the incoming conversation. |
| `telegram` | Polling or webhook | Polling: no. Webhook mode: yes. | Safe certification avoids starting polling/webhook transport because startup can change webhook state. Use explicit live tests only with a target. |
| `feishu` | Websocket or webhook | Websocket: no. Webhook mode: yes. | Choose Feishu vs Lark domain correctly. Websocket connection can be open while provider-console event delivery is still misconfigured, so zero ingress is not proof by itself. |
| `wecom` | AI Bot websocket or corp-app webhook | Websocket: no. Webhook mode: yes. | AI Bot websocket live probing is intentionally unsupported; corp-app webhook needs callback secrets and reachable gateway. |
| `discord` | Gateway websocket | no | Uses gateway websocket; provider feature parity is not complete. |
| `dingtalk` | Stream websocket | no | Certification can fetch stream connection metadata but outbound test is unsupported without inbound `sessionWebhook` context. |
| `matrix` | HTTP sync | no | Requires the `matrix` optional extra and homeserver/user credentials. Encrypted-media/device-trust behavior is limited. |
| `qq` | Gateway websocket | no | Safe probe is unsupported in this build. Delivery targets for certification must use `c2c:<openid>` or `group:<group_openid>`. |

All public vendor adapters in this build are experimental. A `connected` status means the configured adapter reports runtime health; it does not certify every provider feature, permission scope, callback, rate-limit path, file/media path, or outbound mutation.

## Pairing and admission workflow

Default authenticated direct-message behavior is safe pairing:

1. An unknown authenticated DM sender is denied before session creation or tool side effects.
2. The sender receives a short pairing request code when a durable pairing row was created.
3. Operators inspect pending requests:

   ```sh
   opensquilla channels pairings list <channel-name> --status pending
   ```

4. Approve ordinary conversational access:

   ```sh
   opensquilla channels pairings approve <channel-name> <code> --yes
   ```

5. Approve the sender as a channel admin only when that sender is trusted with the channel's privileged host-facing control surface:

   ```sh
   opensquilla channels pairings approve <channel-name> <code> --admin --yes
   ```

6. Revoke access when needed:

   ```sh
   opensquilla channels pairings revoke <channel-name> <code> --yes
   ```

`dm_access=open` admits every authenticated DM sender. `dm_access=allowlist` admits only configured sender IDs. Group conversations default to per-sender session scope so room participants do not share transcript context unless `shared_room` is selected intentionally.

## Live certification workflow

Use certification when a maintainer or operator wants provider-auth evidence without writing channel config.

- Credentials come only from environment variables named like `OPENSQUILLA_CHANNEL_CERT_<PROVIDER>_<FIELD>`.
- The default mode is a safe, non-mutating authentication/network probe when the adapter implements one.
- Evidence is redacted and does not include credential values or target values.
- Missing credentials, invalid config, unsupported safe probe, timeout, provider failure, and delivery failure are all distinct statuses.
- Side-effecting delivery proof requires all of:
  - `--send-test-message`,
  - `--allow-side-effects`,
  - one `--target provider=destination` for each selected provider.

Do not use certification as a replacement for `channels status`: status explains what the running gateway loaded; certification tests an ephemeral adapter with environment credentials.

## Offline validation boundaries

Offline/local checks are enough to verify:

- CLI command wiring and JSON flags;
- channel schema discovery and local config validation;
- secret redaction and blank/masked keep-current semantics;
- pairing store behavior, admission reasons, and pairing RPC access;
- durable ingress/outbox logic and runtime status payload shape;
- MCP bridge command shape and FastMCP tool/resource registration.

They are not enough to prove:

- provider callback reachability;
- webhook signing configured correctly in a third-party console;
- all required provider scopes;
- actual outbound message delivery;
- provider rate-limit, replay, media upload/download, encrypted-media, or interactive-card behavior.

When the user asks for live proof, ask for explicit provider scope, test credentials, target destinations, and permission to perform side effects before running delivery tests.
