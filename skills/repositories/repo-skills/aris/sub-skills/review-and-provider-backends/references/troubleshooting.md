# Provider Troubleshooting

## Missing API Key

Treat a missing key as a configuration error. Verify the exact variable for the selected bridge (`LLM_API_KEY`, `MINIMAX_API_KEY`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`, or provider-specific settings). Never paste a key into a prompt, SKILL.md, or committed config.

## Wrong Endpoint or Model

Check base URL protocol/path and whether the model is supported by that endpoint. A 200 response with an empty or malformed `choices` payload is a provider/schema failure, not a successful review.

## 504 or Timeout

Use the bridge's bounded retry/fallback behavior where available. Record which model actually answered. Do not silently downgrade a user-selected explicit model unless the bridge contract says fallback is allowed.

## MCP Server Missing From Host

Verify the registration command, executable path, environment, and server name. Restart the host agent after any MCP change. Test `initialize` and `tools/list` before invoking ARIS workflows.

## Protocol Negotiation Error

If a server reports an unsupported MCP protocol version, update the server/client pair or use a supported version. Do not suppress the error and continue to `tools/call`.

## Manual Review Stuck

Find the pending state directory, read the displayed URL/token or file instructions locally, check the configured port, and confirm that the reviewer submitted the response. Increase timeout only with user intent. Treat a closed browser/session as incomplete review, not acceptance.

## Feishu/Lark Failure

Check that `lark-oapi` is installed in the runtime serving the bridge, app credentials are valid, the user id is correct, and the port is reachable. Keep Feishu optional; use a local/manual or API reviewer if the bridge is unavailable.
