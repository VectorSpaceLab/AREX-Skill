# Platform, Pipeline, and Provider Troubleshooting

## Bot Receives Messages but Does Not Reply

- Check routing rules and whether the message was discarded before aggregation.
- Confirm the bot is bound to the expected pipeline.
- Inspect pipeline concurrency/session limits and pending query counters.
- Use fake-flow or pipeline integration tests to isolate provider credentials
  from pipeline logic.

## HTTP Bot Signature Fails

- Sign exact raw bytes, not a reserialized JSON body.
- Use `sha256=` prefix on the hex HMAC.
- Include timestamp in the signed prefix and keep clocks within the replay
  window.
- Verify inbound and outbound secrets separately when configured.

## Provider Call Fails

- Determine whether the failure is configuration, credentials, model ability,
  requester implementation, network, or runner/tool behavior.
- Check secret redaction when surfacing errors through HTTP/API logs.
- Prefer fakes/mocks for wiring; use real provider calls only for live-provider
  tasks.

## Pipeline Stage Not Running

- Confirm the stage family is registered through the existing mechanism.
- Confirm pipeline config materialization includes the stage.
- Check whether a previous stage used `prevent_default` or raised an exception.
- Use focused stage tests before full pipeline integration.

## Tool Not Available to Runner

- Check tool source: native, plugin, external MCP, MCP stdio, or skill.
- If the selected source is Plugin Runtime or Box-backed, route to
  `plugin-box-skills` for runtime-level diagnosis.
