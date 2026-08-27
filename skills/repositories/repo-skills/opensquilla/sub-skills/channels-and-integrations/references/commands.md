# Channel and MCP command catalog

Assume `opensquilla` is installed and on `PATH`. If the command is missing or the gateway is not installed/runnable, route to [`../../setup-and-gateway/SKILL.md`](../../setup-and-gateway/SKILL.md) before continuing.

## Discover channel support

```sh
opensquilla channels types
opensquilla channels types --json
opensquilla channels describe slack
opensquilla channels describe slack --json
```

Current public families in OpenSquilla 0.5.3 are `dingtalk`, `discord`, `feishu`, `matrix`, `qq`, `slack`, `telegram`, and `wecom`. Always inspect `describe` for the selected type because visible required fields depend on transport mode and optional extras.

## Create or update channel config

Interactive setup:

```sh
opensquilla configure channels
```

Explicit add/update pattern:

```sh
opensquilla channels add <type> --name <entry-name> \
  --token '<secret-or-placeholder>' \
  --field key=value \
  --field another_key=value
```

Useful shared options:

```sh
--name <entry-name>          # required unique channel entry name
--token <secret>             # mapped to the provider's primary token/secret field when applicable
--field key=value            # repeatable provider-specific field
--enabled / --disabled       # save enabled state
--agent-id <agent-id>        # defaults to main
--config <path>              # override the OpenSquilla config file
```

Use placeholder values in documentation and test prompts. For real operations, prefer interactive setup or a secret manager so tokens are not left in shell history.

### Examples with placeholders only

Telegram polling:

```sh
opensquilla channels add telegram --name personal --token '<telegram-bot-token>'
opensquilla gateway restart
opensquilla channels status personal --json
```

Slack Socket Mode, which does not need a public request URL:

```sh
opensquilla channels add slack --name team \
  --field connection_mode=socket \
  --field app_token='<xapp-token>' \
  --token '<xoxb-token>'
opensquilla gateway restart
opensquilla channels status team --json
```

Slack Events API webhook, which needs a provider-reachable gateway URL and signing secret:

```sh
opensquilla channels add slack --name team-webhook \
  --field connection_mode=webhook \
  --field signing_secret='<signing-secret>' \
  --token '<xoxb-token>'
opensquilla gateway restart
opensquilla channels status team-webhook --json
```

Matrix requires the Matrix optional dependency in addition to its homeserver/user credentials:

```sh
opensquilla channels describe matrix
opensquilla channels add matrix --name matrix-main \
  --field homeserver_url='https://matrix.example' \
  --field user_id='@bot:matrix.example' \
  --token '<access-token>'
opensquilla gateway restart
opensquilla channels status matrix-main --json
```

## Manage saved channel entries

```sh
opensquilla channels list
opensquilla channels list --json
opensquilla channels edit <name> --field key=value
opensquilla channels enable <name>
opensquilla channels disable <name>
opensquilla channels remove <name>
```

After `add`, `edit`, `enable`, `disable`, or `remove`, restart the gateway process:

```sh
opensquilla gateway restart
```

`opensquilla channels restart <name>` is not a config reload for newly edited webhook routes. It restarts an already-loaded live adapter inside the current gateway process.

## Inspect and control runtime adapters

```sh
opensquilla channels status
opensquilla channels status <name>
opensquilla channels status <name> --json
opensquilla channels restart <name> --yes
opensquilla channels logout <name> --yes
```

`channels status` is gateway-backed. It reports what the running gateway knows, including loaded status, connection state, capability/profile evidence, platform manifest, pending pairings, restart attempts, delivery diagnostics, admission diagnostics, and transport-lease data when available. It does not perform a live provider network probe by itself.

## Pairings

```sh
opensquilla channels pairings list <channel-name>
opensquilla channels pairings list <channel-name> --status pending
opensquilla channels pairings approve <channel-name> <pairing-code-or-id> --yes
opensquilla channels pairings approve <channel-name> <pairing-code-or-id> --admin --yes
opensquilla channels pairings revoke <channel-name> <pairing-code-or-id> --yes
```

Pairing mutations require confirmation unless `--yes` is supplied. The sender sees an 8-character pairing code; the CLI also accepts the full pairing ID.

## Certification probes

Default safe auth probes, selected by provider:

```sh
export OPENSQUILLA_CHANNEL_CERT_TELEGRAM_TOKEN='<token>'
export OPENSQUILLA_CHANNEL_CERT_SLACK_TOKEN='<xoxb-token>'
export OPENSQUILLA_CHANNEL_CERT_SLACK_SIGNING_SECRET='<signing-secret>'
export OPENSQUILLA_CHANNEL_CERT_FEISHU_APP_ID='<app-id>'
export OPENSQUILLA_CHANNEL_CERT_FEISHU_APP_SECRET='<app-secret>'

opensquilla channels certify --provider telegram --provider slack --provider feishu --json
```

The certification runner reads `OPENSQUILLA_CHANNEL_CERT_<PROVIDER>_<FIELD>` variables, constructs ephemeral adapters, and emits redacted evidence. It does not write credentials into channel configuration.

Outbound delivery certification is intentionally harder to invoke:

```sh
opensquilla channels certify \
  --provider telegram \
  --send-test-message \
  --allow-side-effects \
  --target telegram='<chat-id>' \
  --json
```

Only run outbound certification with newly rotated test credentials and explicit provider destinations. QQ targets use `c2c:<openid>` or `group:<group_openid>`.

## MCP server bridge

Start or confirm the gateway first:

```sh
opensquilla gateway start --json
opensquilla gateway status
```

Run the stdio MCP bridge:

```sh
opensquilla mcp-server run
opensquilla mcp-server run --gateway ws://localhost:18792/ws
```

The default bridge URL is `ws://localhost:18791/ws`. `--gateway` can also be supplied through `OPENSQUILLA_GATEWAY_URL`. The CLI exposes a stdio server only; it does not expose `--host`, `--port`, or `--transport` flags.
