# Platform Adapters

## Adapter Boundary

Adapters translate external platform APIs into LangBot's shared message/event
model. They should not own LLM-provider behavior, persistence policy, or
pipeline business logic.

Adapter evidence lives under platform sources and manifests. Each adapter has a
manifest/config schema and Python implementation; many have icon assets and
platform-specific helpers. Supported surfaces include Discord, Telegram, Slack,
LINE, QQ/OneBot, WeChat variants, WeCom, Lark, DingTalk, KOOK, Satori, Matrix,
WebSocket, Page Bot, and HTTP Bot.

## Webhook Routes

The public `/bots/<bot_uuid>` route delegates to the resolved runtime bot and
adapter. Security is adapter-specific: vendor signatures or HTTP Bot HMAC must
be verified inside the adapter, not by generic user-token auth.

## Adding or Updating an Adapter

Checklist:

1. Reuse shared SDK message/event entity types.
2. Keep native platform objects only for debugging or escape hatches.
3. Add/update adapter manifest config schema, labels, and icons/assets.
4. Handle secret redaction and webhook URL display consistently.
5. Add unit tests for conversion, limits, tenancy, and signatures.
6. Add docs or skill guidance if the adapter becomes agent-facing.
7. Keep user-facing strings localized.

## DingTalk Card Template Pitfall

The DingTalk human-input card template builder exists to preserve details that
are easy to lose: Markdown-bound variables need `varType: "markdown"`, and the
adapter updates the full card data instead of enabling streaming on the card
component. If editing this area, inspect the template and focused DingTalk tests
rather than rewriting the card JSON from memory.
