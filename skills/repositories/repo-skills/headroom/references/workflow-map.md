# Cross-surface workflow map

Use this map when a request crosses the root routes.

## Install → proxy → agent

1. `ops`: install or deploy `headroom-ai`, run `headroom doctor`, and determine whether the proxy is healthy.
2. `proxy-wrap`: start `headroom proxy`, choose the backend/base URL, and configure `wrap` or a client environment.
3. `ops`: verify `perf`, `savings`, or `inspect` after real traffic.

## Python app → CCR/MCP retrieval

1. `sdk`: call `compress()` or a `HeadroomClient` wrapper and preserve `CompressResult.ccr` metadata.
2. `memory`: configure `headroom mcp serve` or agent registration and explain `headroom_retrieve`.
3. `proxy-wrap`: if retrieval or compression requires a running proxy, check `/livez`, `/health`, and the proxy URL.

## Memory-enabled agent

1. `memory`: choose local SQLite vs service-backed memory, set an explicit database/service path, and decide whether `with_memory` or tool-based memory is appropriate.
2. `proxy-wrap`: route the agent traffic through Headroom if the user wants automatic proxy compression.
3. `ops`: use `doctor`, `perf`, and `savings` to distinguish memory activity from compression activity.

## TypeScript application

1. `sdk`: install/use `headroom-ai`, choose `compress`, `HeadroomClient`, `SharedContext`, hooks, or adapters.
2. `proxy-wrap`: start or validate the proxy when the TS client uses the default loopback base URL.
3. `memory`: route to CCR/MCP only when the application needs full-content retrieval or agent-facing tools.

## Diagnosis decision tree

- Package/CLI missing → `ops`.
- Proxy reachable but no savings → `ops` first, then `proxy-wrap` for base URL/wrapper routing.
- Proxy saves tokens but retrieval hash fails → `memory` for CCR/MCP, then `proxy-wrap` for proxy URL.
- Python API returns passthrough → `sdk` for config/thresholds and `ops` only if the app is actually proxy-backed.
- Cloud provider error → `proxy-wrap` for provider path and credentials; do not conflate with a local import failure.
