# Integration troubleshooting

## Wrong scope or missing resource

**Symptom:** a read or write returns 404, an empty result, or a scope error.

**Likely cause:** the workspace, peer, or session id does not match the target
resource.

**Recovery:**

- Confirm the ids.
- Confirm the workspace boundary.
- Re-run the request with the same scope used to create the resource.

## Session context looks stale

**Symptom:** `session.context()` or the dialectic answer does not reflect the
latest turn.

**Likely cause:** the message has been stored, but background reasoning has not
finished yet.

**Recovery:**

- Verify the message was written.
- Wait for the background pipeline.
- Read the session context again.

## `peer.chat()` is slower than expected

**Likely cause:** live reasoning is happening.

**Recovery:**

- Use `peer.representation()` or `session.context()` if the question can be
  answered from a read.
- Lower the reasoning level if the request does not need deep synthesis.

## Unexpected response shapes

**Likely cause:** the request or the SDK call is using the wrong return type
expectation, especially for JSON vs text output.

**Recovery:**

- Inspect the SDK signature.
- Compare the route family with the API map.
- Check whether the call is returning a message object, a representation, or a
  plain string.

## Messages never seem to accumulate memory

**Likely cause:** the application is not storing turns, or it is storing them in
inconsistent sessions.

**Recovery:**

- Confirm every exchange is recorded.
- Reuse the same peer ids.
- Keep the session scope coherent.

## Webhook confusion

**Likely cause:** the webhook endpoint or payload does not match the current
server route family.

**Recovery:**

- Re-check the `/webhooks` route family.
- Confirm the workspace id.
- Validate the registration payload before assuming the handler is broken.
