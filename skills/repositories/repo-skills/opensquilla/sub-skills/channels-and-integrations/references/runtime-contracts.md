# Channel runtime contracts

This reference summarizes behavior that matters when debugging ingress, egress, pairings, approvals, and adapter status.

## Catalog, maturity, and capability evidence

The channel registry discovers public built-in adapters plus external `opensquilla.channels` entry points. In OpenSquilla 0.5.3 the public built-in families are `dingtalk`, `discord`, `feishu`, `matrix`, `qq`, `slack`, `telegram`, and `wecom`; the legacy Microsoft Teams adapter is hidden from catalog surfaces.

Adapter status can include:

- **low-level capability tags** such as webhooks, websockets, group chat, mentions, files, media, reactions, threads, edit/delete, cards, and artifact delivery;
- a **provider platform manifest** across chat, files, media, attachments, threads, cards, docs, drive, wiki, permissions, and scopes;
- **evidence kind** such as method-backed evidence or declaration evidence;
- **proof status**, which is `unverified` unless live proof has been recorded by a separate probe/certification flow.

Do not convert method/declaration evidence into a stronger certification claim. Use it to explain what the adapter is designed to expose and where the running gateway sees no implementation.

## Admission and pairing boundary

Admission is evaluated once before session creation, command handling, approval resolution, attachment download, or transcript mutation.

Authenticated ingress records provider, account, transport, verification method, native event ID, and principal. A provider principal must match the normalized `sender_id`; a mismatch is denied as `principal_mismatch`.

Direct-message policy modes:

- `pairing` — default for authenticated DMs. Unknown senders are held for operator approval.
- `open` — admits authenticated DM senders without pairing. Use only for intentionally public bots.
- `allowlist` — admits only configured `allowed_senders`.

Pairing facts:

- Pending requests store provider identity, sender ID/name, status, timestamps, request count, and reply route; they do not store rejected message content.
- Pending request codes are the first eight characters of the durable pairing ID.
- Pending requests are capped per channel and expire if never acted on; approved and revoked decisions persist.
- A full pending queue denies the sender with `pairing_required` but may not produce a code or notice.
- Approval can send a best-effort approved notice unless the channel entry disables it.
- `--admin` on approval is a channel-bound admin grant. Revoking a pairing also withdraws channel-admin standing for that sender when present.

Group behavior:

- Group messages require explicit mention/interaction when the policy requires mention. If an adapter has no mention hook, the gate defaults to deny rather than guessing.
- `group_session_scope=per_sender` keeps each participant's room transcript separate.
- `group_session_scope=shared_room` intentionally gives the room one shared transcript.
- `busy_input_mode` can be `followup`, `queue`, `steer`, or `interrupt`; unsupported runtime modes fall back to the safe/default behavior.

## Channel approvals and tool safety

When a channel turn reaches a gated tool, OpenSquilla sends a short approval code rather than exposing the raw approval ID. Resolution must come from the same admitted session/conversation and requester when authenticated identity is available.

Adapters with interactive cards may render buttons, but every adapter has plain-text fallbacks:

```text
/approve CODE
/deny CODE
```

A channel approval releases only that gated action. It does not enable session-wide elevated mode, bypass sandbox posture, or override protected-path/high-risk command policy. For host execution, workspace, permission-profile, and sandbox posture details, route to [`../../cli-and-automation/SKILL.md`](../../cli-and-automation/SKILL.md).

## Durable ingress and outbound delivery

Managed channels use a SQLite delivery store in the OpenSquilla state directory.

Ingress guarantees:

- Inbound events with stable native event IDs are committed before dispatch queue processing.
- Claimed events are returned to accepted state on restart if processing was interrupted.
- Events without stable provider IDs cannot receive durable deduplication.
- Storage faults degrade availability for an individual event instead of killing the adapter loop, but crash-durability for that event is weaker.

Outbound guarantees:

- Ordinary sends and supported mutations such as file upload, edit, delete, reactions, and streaming operations first persist an outbound intent with a delivery ID, target, content hash, and sanitized metadata.
- Confirmed results store provider message/file IDs when an adapter reports them.
- A legacy adapter that returns no receipt becomes `sent_unconfirmed`.
- An exception becomes `unknown`; do not blindly retry `unknown` because the provider may already have delivered the message.
- Error classes use the shared taxonomy: `transport_transient`, `rate_limited`, `channel_degraded`, `auth_invalid`, `payload_rejected`, `target_missing`, `contract_violation`, or `unknown`.

`channels status --json` can surface delivery counts, oldest pending records, unknown outcomes, admission reason tallies, and transport lease data.

## One active transport per account

Before starting an adapter, the manager acquires a renewable lease for the provider family plus derived account identity in the delivery store. The lease includes a fencing token and appears in health diagnostics. A second local gateway using the same state database should not start the same account transport while the lease is live.

This is a local SQLite ownership guard, not a distributed multi-region lease service. If status shows a live lease conflict, look for another gateway process using the same OpenSquilla state/config.

## Status semantics

`opensquilla channels status --json` returns a `channels` array plus a gateway `bootId`. Each channel row can include:

- `name`, `type`, `configured`, `enabled`;
- `connected` and coarse `status` such as `connected`, `stopped`, `disabled`, `restarting`, `exhausted`, or `dead`;
- `restart_attempts`, `connected_since`, and `bot_user_id` when known;
- `pendingPairings`;
- capability tags and `capability_profile`;
- provider-level `platform_manifest`;
- `diagnostics` with `network_probe: not_run`, last startup/adapter errors, delivery ledger stats, admission policy/reasons, and transport lease information.

Read `channels status` as the gateway's runtime view. It is not a provider certification and it does not initiate a fresh provider network probe.

## Restart and reconcile behavior

- Gateway start builds adapters from enabled channel entries.
- Disabled entries are skipped.
- Webhook-mode route changes require a gateway process restart because HTTP routes are bound when the gateway app starts.
- `channels.restart <name>` is for an already-loaded adapter, including recovering an adapter whose dispatch loop became `dead` after automatic retries.
- A configured but not loaded channel should produce a clear “adapter not loaded; restart the gateway” style failure for live restart. Use `opensquilla gateway restart`.
- Start failures are per-channel; one bad channel should not prevent other channels from running.
