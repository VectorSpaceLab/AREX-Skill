# Streaming WebSocket contract

With `streaming` configured, connect to `WS /v1/stream`. Each connection owns a
session. The first client frame must be `session_init_v2`; invalid first frames
are rejected.

## Client messages

- `session_init_v2`: preset, curated prompts, optional initial image, toggles,
  and optional continuation state.
- `segment_prompt_source`: next prompt plus optional seed/steps/guidance/
  negative-prompt overrides.
- `seed_prompts_updated`, `enhancement_updated`, `auto_extension_updated`,
  `loop_generation_updated`, and `generation_paused_updated`: update session
  behavior for later segments.
- `snapshot_state`: request an exportable continuation snapshot.

## Server lifecycle

A session moves through `INITIALIZING`, `QUEUED`/`GPU_BINDING`, `ACTIVE`, and a
terminal state (`COMPLETE`, `ERROR`, `TIMEOUT`, or `REJECTED`). The server emits
queue and GPU assignment messages, stream/segment start, step completion,
media initialization, binary fMP4 fragments, segment completion, and stream
completion. A `media_init` message must precede binary frames.

`session_timeout_seconds` reaps idle sessions. `generation_segment_cap` ends a
session after the configured number of segments. Snapshot payloads are opaque;
clients should store and resend them without modifying fields.

Use `stream_mode: av_fmp4` for binary media when the client supports it;
`legacy_jpeg` is a compatibility mode. Keep message type changes versioned
rather than changing field semantics in place.
