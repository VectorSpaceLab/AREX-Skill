# HTTP Bot Workflow

HTTP Bot is a standalone server-to-server adapter. External systems POST signed
messages to LangBot and receive replies through a configured callback URL.

## Core Contract

- Inbound URL: `/bots/<bot_uuid>`.
- Optional convenience routes include sync and reset paths under the same bot
  webhook route, as implemented by the adapter.
- Inbound and outbound bodies are signed with HMAC-SHA256 over
  `"{timestamp}." + raw_body`.
- Headers include `X-LB-Timestamp`, `X-LB-Signature`, and optionally
  `X-LB-Idempotency-Key`.
- The adapter accepts a caller-defined `session_id`, preserving business
  session identity such as ticket IDs.
- N-to-1 aggregation and 1-to-many replies come from the normal pipeline and
  adapter reply calls, not from a WebSocket transport.

## Use the Bundled Helper

```bash
python sub-skills/platform-pipeline-provider/scripts/http_bot_hmac_helper.py sign --secret SHARED --body '{"session_id":"s1"}'
python sub-skills/platform-pipeline-provider/scripts/http_bot_hmac_helper.py payload --session ticket-1 --text hello
python sub-skills/platform-pipeline-provider/scripts/http_bot_hmac_helper.py post --url http://host/bots/BOT --secret SHARED --session ticket-1 --text hello
```

The `post` subcommand performs a network call only when explicitly requested.
The signing and payload subcommands are safe offline checks.

## Callback Debugging

When callbacks fail:

1. Verify the bot is an HTTP Bot and is bound to a working pipeline.
2. Confirm `callback_url` is reachable from LangBot, not just from the browser.
3. Verify inbound and outbound secrets; outbound may default to inbound when not
   separately configured.
4. Check timestamp skew and replay window.
5. Inspect whether pipeline aggregation delayed the turn.
6. Confirm multiple callbacks per turn are expected; use `sequence` and
   `is_final` to collapse or display replies.
