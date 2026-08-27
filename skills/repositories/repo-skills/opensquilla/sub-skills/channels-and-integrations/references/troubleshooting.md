# Channels and integrations troubleshooting

Work from the local boundary outward: config schema, saved entry, gateway process, loaded adapter status, pairing/admission, delivery ledger, then live provider network.

## `opensquilla` command is missing

This sub-skill assumes an installed OpenSquilla runtime. Route to [`../../setup-and-gateway/SKILL.md`](../../setup-and-gateway/SKILL.md) for installation and first-run checks.

## Missing secrets or wrong channel type

Symptoms:

- `channels add` or `channels edit` exits with validation errors;
- `onboarding.channel.probe`/config save rejects a blank required secret;
- `channels describe <type>` shows fields that do not match the operator's provider-console mode;
- a redacted `***` value was copied into a config/edit workflow without a stored credential to keep.

Checks:

```sh
opensquilla channels types --json
opensquilla channels describe <type> --json
opensquilla channels list --json
```

Actions:

- Verify the channel family is one of the public catalog types.
- Re-run `describe` after choosing a transport mode; mode-dependent fields are easy to miss.
- For Slack, do not mix Socket Mode fields with webhook-only signing-secret expectations.
- For WeCom, choose websocket vs webhook and provide the matching credentials.
- For Matrix, make sure the `matrix` optional extra is installed.
- Never write literal `***` as a new secret; it is only a redacted keep-current mask when a stored credential already exists.

## Config saved but channel is not running

Symptoms:

- `channels list` shows the entry, but `channels status <name> --json` is empty, stopped, or reports adapter-not-loaded;
- `channels restart <name>` says the adapter is not loaded;
- webhook route edits appear ignored.

Checks/actions:

```sh
opensquilla gateway status
opensquilla gateway restart
opensquilla channels status <name> --json
```

Remember:

- `channels add|edit|enable|disable|remove` writes config and requires a gateway process restart.
- `channels restart <name>` restarts a currently loaded adapter only.
- Webhook routes are bound at gateway startup; adding/removing/repointing them needs a gateway restart.

## Pairing or admission failure

Symptoms:

- The sender receives a pairing code and no session response.
- `channels status` shows `pendingPairings`.
- Admission diagnostics show reasons such as `pairing_required`, `pairing_revoked`, `not_in_allowlist`, `not_mentioned_in_group`, or `principal_mismatch`.

Checks:

```sh
opensquilla channels status <channel-name> --json
opensquilla channels pairings list <channel-name> --status pending
```

Actions:

- Approve ordinary access only for recognized senders:

  ```sh
  opensquilla channels pairings approve <channel-name> <code> --yes
  ```

- Use `--admin` only for a sender you trust with channel-admin operations:

  ```sh
  opensquilla channels pairings approve <channel-name> <code> --admin --yes
  ```

- Revoke stale or mistaken access:

  ```sh
  opensquilla channels pairings revoke <channel-name> <code> --yes
  ```

- If no code was shown, the pending queue may be full or the request may not have produced a durable pairing row. Inspect status diagnostics and reduce stale pending requests.
- For groups, check mention requirements and whether the adapter supports mention detection. Missing mention hooks default to deny.
- For `allowlist`, confirm the provider sender ID exactly matches the configured sender ID.

## Restart required after channel edits

The channel CLI intentionally prints a restart notice after config edits. Use:

```sh
opensquilla gateway restart
```

Do not substitute:

```sh
opensquilla channels restart <name>
```

unless the adapter is already loaded and the task is to recover that live adapter from a runtime state such as `dead` or `exhausted`.

## Runtime status is `dead`, `exhausted`, or `restarting`

Checks/actions:

```sh
opensquilla channels status <name> --json
opensquilla channels restart <name> --yes
opensquilla doctor
```

Interpretation:

- `restarting` may be transient reconnect/backoff.
- `exhausted` means the dispatch loop exhausted its inner retry budget and may enter an automatic restart cycle.
- `dead` means automatic restart cycles are exhausted; operator `channels restart` is the recovery path.
- A start error diagnostic often points to invalid credentials, missing optional dependencies, wrong transport mode, provider rejection, or network failure.

## Delivery ledger shows `sent_unconfirmed` or `unknown`

`sent_unconfirmed` means the adapter returned no provider receipt. `unknown` means an exception happened after an outbound intent was persisted; the provider may still have delivered the message.

Do not blindly resend `unknown` messages. Inspect:

```sh
opensquilla channels status <name> --json
opensquilla doctor
```

Then decide whether to contact the provider console, notify the user, or retry a new message with explicit operator approval.

## Transport lease conflict

Symptoms:

- startup error says a channel transport lease is already held;
- status diagnostics include a live `transport_lease` for the same channel/account.

Actions:

- Stop duplicate gateway processes using the same OpenSquilla state/config.
- Restart a single owner gateway.
- Treat this as a local process/account ownership guard, not as a cluster lease.

## Webhook callback does not arrive

For Slack webhook mode, WeCom webhook mode, and webhook modes of Feishu or Telegram:

- the gateway must bind to a reachable interface;
- a trusted reverse proxy or tunnel must carry provider callbacks;
- gateway auth/network exposure must be intentionally configured;
- provider callback URL, signing secret, token, encryption key, and webhook path must match the saved entry.

Do not expose an unauthenticated gateway to the public internet. Route gateway bind/auth questions to [`../../setup-and-gateway/SKILL.md`](../../setup-and-gateway/SKILL.md).

## Certification result is missing, unsupported, or failed

Checks:

```sh
opensquilla channels certify --provider <type> --json
```

Interpretation:

- `missing_credentials`: required `OPENSQUILLA_CHANNEL_CERT_<PROVIDER>_<FIELD>` variables were absent.
- `invalid_environment` or `invalid_config`: field coercion or adapter construction failed.
- `unsupported`: the adapter has no safe non-mutating probe for that mode/provider.
- `timeout` or `failed`: the provider operation did not complete or rejected the credentials.
- `delivery_unsupported`: safe auth may work, but side-effecting delivery is intentionally not available for that provider context.

Side-effecting proof must include `--send-test-message`, `--allow-side-effects`, and explicit `--target provider=destination` values.

## MCP bridge missing extra or wrong gateway URL

Symptoms:

- `opensquilla mcp-server run` reports the optional dependency is missing;
- the MCP client launches but no tools can reach sessions;
- the client config uses an HTTP URL or expects a listening network port.

Checks/actions:

```sh
opensquilla gateway status
opensquilla doctor
opensquilla mcp-server run --gateway ws://localhost:18791/ws
```

Fixes:

- Install OpenSquilla with the `mcp` optional extra.
- Use the gateway websocket URL ending in `/ws`.
- Configure the MCP-capable client to launch the command as a stdio server.
- Do not add provider keys or channel secrets to the MCP client config.

## Credentialed live probe boundaries

Local validation and status are safe for routine diagnosis. Credentialed live probes and delivery checks are different:

- use dedicated test credentials and rotate them after use when appropriate;
- keep secrets in environment variables or a secret manager;
- avoid provider production rooms unless the operator explicitly chooses them;
- record that `channels status` does not perform a provider network probe;
- document which proof was obtained: local config validation, safe auth probe, or side-effecting delivery.
