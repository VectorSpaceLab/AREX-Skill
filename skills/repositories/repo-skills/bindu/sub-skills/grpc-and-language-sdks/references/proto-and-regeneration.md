# Proto Contract and Regeneration

The source of truth is `proto/agent_handler.proto` in a Bindu checkout. Generated files under Python and TypeScript generated trees are not source.

## Message highlights

- `RegisterAgentRequest.config_json`: full config as JSON.
- `RegisterAgentRequest.skills`: repeated skill definitions.
- `RegisterAgentRequest.grpc_callback_address`: SDK callback endpoint.
- `RegisterAgentResponse.success`, `agent_id`, `did`, `agent_url`, `error`.
- `HandleRequest.messages`: chat history.
- `HandleResponse.content`, `state`, `prompt`, `is_final`, `metadata`.
- `HeartbeatRequest.agent_id`, `timestamp`; response `acknowledged`, `server_timestamp`.

## Regeneration commands

From a checkout with dependencies:

```bash
bash scripts/generate_protos.sh python
bash scripts/generate_protos.sh typescript
bash scripts/generate_protos.sh all
```

Python generation uses `uv run python -m grpc_tools.protoc` and then fixes imports in the generated gRPC file. TypeScript generation uses Node tooling when available.

## Drift workflow

1. Inspect proto changes.
2. Run the bundled readiness helper in this skill to check tools and expected paths.
3. Run the repo regeneration script for all impacted languages.
4. Run Python gRPC unit tests and TypeScript build.
5. Commit proto and generated outputs atomically.

Never patch generated stubs by hand to make a test pass.
