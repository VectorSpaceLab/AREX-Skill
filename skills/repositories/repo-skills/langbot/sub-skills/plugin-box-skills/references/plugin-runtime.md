# Plugin Runtime

## LangBot-side Responsibilities

LangBot main owns the bridge to the Plugin Runtime:

- Connector: lifecycle, stdio/WebSocket control transport, marketplace install,
  plugin logs/assets/readme/config, tool invocation, RAG parser/engine calls,
  command execution, event emission, and reconciling desired plugin states.
- Handler: converts LangBot actions and SDK runtime actions, handles plugin
  storage/RAG/provider/tool flows, and enforces tenancy/context boundaries.
- Tool loader: exposes plugin Tool components to model runners.
- Pipeline handlers: emit SDK events such as normal-message and prompt-processing
  events.

## SDK Boundary

The sibling SDK package owns:

- `BasePlugin`, component base classes, manifests, and plugin developer APIs.
- Shared message/event/platform entities.
- Runtime action protocol entities.
- `lbp rt` Plugin Runtime and `lbp box` Box Runtime implementation.

If the task changes shared entities, component APIs, action protocol, runtime
CLI behavior, or Box server behavior, change the SDK first or in lockstep.
Install the local SDK into LangBot's environment, then run LangBot with
`--no-sync` for verification.

## Runtime Modes

- Local/source startup can spawn/connect to the plugin runtime through stdio.
- Containerized/standalone deployments use `plugin.runtime_ws_url`, commonly
  pointing at `ws://langbot_plugin_runtime:5400/control/ws`.
- `--standalone-runtime` tells LangBot to use the standalone runtime path.

## Verification

Use connector/handler unit tests for LangBot-side protocol and tenancy behavior.
Use SDK tests or runtime smoke checks when changing `lbp` or shared protocol
surfaces. Avoid marketplace/live install checks unless network and credentials
are part of the task.
