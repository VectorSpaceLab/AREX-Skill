# Validation Guide

This reference classifies transport-focused checks.

## Health-only smoke

Use this first when you only need to know whether the gateway is alive and which MCP runtime is mounted.

- GET `/health`
- Inspect runtime and transport headers
- Do not create or delete any remote resources

The bundled smoke script in this sub-skill is designed for this mode by default.

## Read-only transport smoke

Use this when you want to validate the transport path without mutating catalogs.

Good candidates:

- initialize a streamable HTTP session
- list tools
- list resources
- list prompts
- inspect A2A agent cards or task state
- verify gRPC reflection output

## Optional final candidates requiring services

These are useful when the live stack is available and the task really depends on the running transport path:

- `test-mcp-protocol-e2e`
- `test-mcp-rbac`
- `test-mcp-access-matrix`
- `test-mcp-session-isolation`
- `test-mcp-plugin-parity` for runtime parity checks
- `test-e2e-sso` when SSO/OAuth is part of the task

## Rust runtime candidates

Use the Rust runtime checks only when the task touches runtime ownership or session handling:

- `make testing-rebuild-rust-shadow`
- `make testing-rebuild-rust`
- `make testing-rebuild-rust-full`
- follow with the relevant MCP live-gateway checks

## Scope boundary

If the question is really about overall repo gates, move to `development-validation` instead of widening this sub-skill.
