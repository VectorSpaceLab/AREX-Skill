# Runtime Surfaces

## Gateway

The gateway is the durable local runtime. It serves the control/Web UI and backs sessions, most memory operations, schedules, channel runtimes, cost/diagnostics state, MetaSkill launches, and the MCP bridge. `gateway status` can distinguish a saved configuration from a running service. A config edit may require a full gateway restart rather than an adapter-only restart.

## CLI and Terminal

`opensquilla chat` is the terminal conversation surface; `--ui auto|tui|plain` controls presentation. Release installs use the stable Python-native terminal path. OpenTUI source-host instructions are development-only. `agent` and `code-task` are bounded automation surfaces with different trust and workspace constraints.

## Web UI and Desktop

The Web UI is served by the gateway, normally at `http://127.0.0.1:18791/control/`. Official wheels and desktop builds carry verified frontend assets; source checkouts must build them. The desktop shell owns its packaged gateway lifecycle and application data paths. UI presentation faults route to the TUI/desktop sub-skill; gateway readiness faults route to setup/gateway.

## Channels and MCP

Messaging adapters are gateway-backed ingress/egress transports. Catalog registration is not live provider certification. Pairing and allowlists govern admission, while host permissions and sandbox policy still govern tools. `opensquilla mcp-server run` is a stdio process used by an MCP-capable client and connects to an already-running gateway.

## Skills and MetaSkills

The Skill catalog has local discovery and managed mutation surfaces. Eligibility depends on provenance, shadowing, disabled state, and optional readiness. MetaSkills are deliberate multi-step compositions, normally launched through `/meta` on supported gateway surfaces. Natural-language MetaSkill triggering is compatibility behavior, not the default assumption.

## Exposure Boundary

Loopback is the safe default. Binding publicly makes the gateway, Web UI, channels, and connected tooling part of a network security boundary. Require explicit intent, authentication, and reviewed proxy/tunnel configuration before recommending it.
