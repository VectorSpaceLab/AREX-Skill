# Runtime Modes and Health Headers

Use `/health` to confirm which MCP runtime actually owns the public transport.

## Mode summary

| Boot / effective shape | What it means for public MCP |
|---|---|
| `off` | Python owns the transport.
| `shadow` | Rust is present, but the public `/mcp` mount still behaves like Python.
| `edge` | Rust can own the public path; Python still backs some runtime pieces.
| `full` | Rust owns the public path plus the session/event-store/resume/affinity stack.

## Health headers to inspect

- `x-contextforge-mcp-runtime-mode`
- `x-contextforge-mcp-transport-mounted`
- `x-contextforge-rust-build-included`
- `x-contextforge-mcp-session-core-mode`
- `x-contextforge-mcp-event-store-mode`
- `x-contextforge-mcp-resume-core-mode`
- `x-contextforge-mcp-live-stream-core-mode`
- `x-contextforge-mcp-affinity-core-mode`
- `x-contextforge-mcp-session-auth-reuse-mode`

## How to read mismatches

- `runtime-mode=rust-managed` with `transport-mounted=python` usually means shadow mode.
- `runtime-mode=rust-managed` with `transport-mounted=rust` means the public path is Rust-owned.
- If `GET /mcp` still looks like Python after a Rust boot, check the mounted transport header before changing any session logic.
- If session or replay behavior looks wrong, compare the session/event/resume/affinity headers instead of inferring from runtime mode alone.

## Validation candidates

When services are available, the relevant checks are:

- `make testing-rebuild-rust-shadow`
- `make testing-rebuild-rust`
- `make testing-rebuild-rust-full`
- `make test-mcp-protocol-e2e`
- `make test-mcp-rbac`
- `make test-mcp-access-matrix`
- `make test-mcp-session-isolation`

These are transport-focused candidates. Broader repo gating belongs to the validation skill.
