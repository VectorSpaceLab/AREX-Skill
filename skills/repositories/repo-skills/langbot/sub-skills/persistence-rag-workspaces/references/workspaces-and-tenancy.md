# Workspaces and Tenancy

## Context Objects

- `RequestContext` carries authenticated principal, Workspace membership,
  fixed-role permissions, instance, request id, and placement generation for
  HTTP/API/MCP requests.
- `ExecutionContext` carries trusted runtime execution binding for pipeline,
  bot, plugin, Box, and background execution paths.

Services should receive one of these contexts rather than independently trusting
headers, UUIDs, or caller-supplied Workspace ids.

## API-Key Tenancy

Database-backed API keys are bound to one Workspace and explicit scopes. The
global config key is only for trusted Community singleton Workspace use. Do not
let `X-Workspace-Id` move an API key across tenants.

## Workspace Collaboration

Workspace services and collaboration logic own membership, invitations, role
updates, support-admin restrictions, and placement bindings. When touching this
area, verify member view/invite/update permissions and support-admin denial
rules for sensitive routes.

## Cloud Runtime and Directory State

Cloud/toB paths add directory projection, launch/support admin services,
entitlement checks, placement generations, and resource fences. Changes here
usually need both service tests and integration-level reasoning about stale
placement generations and write fencing.
