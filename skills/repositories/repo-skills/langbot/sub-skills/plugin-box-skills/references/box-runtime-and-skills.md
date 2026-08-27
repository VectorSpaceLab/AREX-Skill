# Box Runtime and Skills

## Box Role

Box is the sandbox subsystem behind native agent tools, stdio MCP hosting,
skill authoring/editing, managed processes, session execution, file mounts, and
runtime workspace storage.

LangBot main owns:

- Box service facade for exec, sessions, managed processes, skill CRUD/status,
  reconnects, quotas, mounts, and sandbox profiles.
- Box connector for local stdio, Windows subprocess/WebSocket, or remote
  WebSocket runtime paths.
- Native/MCP stdio/skill tool loaders that depend on Box availability.
- Skill manager/service integration and local fallback behavior.

The SDK owns the Box server/runtime/backends and `lbp box` CLI.

## Config Keys

Important keys are under `box:`:

| Key | Purpose |
|---|---|
| `box.enabled` | Master switch for sandbox features. |
| `box.backend` | `local`, `docker`, `nsjail`, or `e2b` backend selection. |
| `box.runtime.endpoint` | External Box Runtime endpoint for standalone/containerized mode. |
| `box.local.host_root` | Host root for local workspace mounts. |
| `box.local.skills_root` | Box-owned skill package directory under host root. |
| `box.admission.*` | Optional admission/readiness policy for controlled deployments. |

Container deployments need aligned host/container mount roots and shared control
tokens. A Docker daemon without user socket permission commonly looks like a Box
backend availability problem.

## Skill CRUD and Storage

Skill APIs can list/read/write/install skill files through Box-backed storage.
When changing these paths, verify:

- hidden file handling and traversal protections,
- upload/install preview vs commit behavior,
- Workspace/tenant scoping,
- Box enabled/disabled UI/API behavior,
- native tool guidance and mounted skill paths.

## Real Integration Caveat

Box integration tests use real Docker/Podman and sockets. They are optional for
ordinary connector/service changes but required when the task changes actual
sandbox lifecycle, managed process WebSocket attach, container backend policy,
or admission/generation fencing.
