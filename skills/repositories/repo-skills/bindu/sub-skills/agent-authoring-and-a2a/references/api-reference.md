# Agent Authoring API Reference

## `bindufy()`

```python
bindufy(config, handler, run_server=True, key_dir=None, launch=False) -> AgentManifest | None
```

Use `bindufy()` to transform a Python callable into a Bindu A2A microservice. It validates config and handler shape, creates DID-backed identity material, loads public/private skills, builds an `AgentManifest`, creates a Starlette `BinduApplication`, and starts the server when requested.

The internal `_bindufy_core(config, handler_callable, ..., skills_override=None, skip_handler_validation=False, run_server_in_background=False)` is used by SDK registration. Normal user agents should call `bindufy()`.

## Handler return values

| Return shape | Task effect |
|---|---|
| `"text"` | Completed task with text content and artifact. |
| `{"state": "input-required", "prompt": "..."}` | Open task waiting for user input. |
| `{"state": "auth-required", "prompt": "..."}` | Open task waiting for auth/action. |
| Exception | Failed task; payment metadata may record orphan-payment risk if settlement already happened. |

Local Python handler validation expects exactly one parameter named `messages`. The worker passes chat-style history: `[{"role": "user", "content": "..."}]`.

## Required config

```python
config = {
    "author": "you@example.com",
    "name": "my-agent",
    "deployment": {"url": "http://localhost:3773"},
}
```

Optional but common keys: `description`, `version`, `recreate_keys`, `skills`, `private_skills`, `allowed_dids`, `capabilities`, `storage`, `scheduler`, `execution_cost`, `kind`, `debug_mode`, `debug_level`, `monitoring`, `telemetry`, `global_webhook_url`, `global_webhook_token`, and `documentation_url`.

## `AgentManifest`

`create_manifest(...)` records identity, DID extension, capabilities, skills, agent kind, history settings, public/private skill catalog, webhook settings, negotiation metadata, and a generated `run` callable around the handler.

## `BinduApplication`

`BinduApplication(...)` registers the HTTP routes future agents most often inspect:

| Route | Purpose |
|---|---|
| `GET /.well-known/agent.json` | Public agent card. |
| `POST /` | A2A JSON-RPC endpoint. |
| `GET/POST /did/resolve` | DID document resolution. |
| `GET /agent/skills` | Public skill summaries. |
| `GET /agent/skills/{skill_id}` | Skill detail without full docs. |
| `GET /agent/skills/{skill_id}/documentation` | Full skill documentation. |
| `GET /agent/private.json` | Private merged card, only when configured/authenticated. |
| `GET /health` | Health. |
| `GET /metrics` | Metrics. |
| `POST /agent/negotiation` | Capability assessment. |

## `TaskManager`

`TaskManager(scheduler, storage, manifest=None)` wires message, task, context, push-notification handlers, and `ManifestWorker`. It parses context ids strictly: missing context id creates a new context; malformed context id returns invalid params rather than silently creating another context.

## Skills loader

`load_skills(skills_config, caller_dir)` and `load_skill_from_directory(skill_path, caller_dir)` support `skill.yaml`, `SKILL.md` with YAML frontmatter, or both. Parsed skill objects keep documentation content for `/agent/skills/{id}/documentation` and for SDK transmission.
