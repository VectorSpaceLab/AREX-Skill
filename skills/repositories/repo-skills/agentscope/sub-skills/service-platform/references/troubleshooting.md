# Troubleshooting

## Startup failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `create_app` fails immediately | One of the required components is missing or misconfigured | Verify storage, message bus, and workspace manager first |
| The service starts but the UI is missing a feature | The corresponding optional hook was never registered | Check `platform-overview.md` for the right extra hook |
| An index worker or knowledge-base endpoint misbehaves | The storage/vector-store pair does not match the configured knowledge-base manager | Re-read the RAG and storage references together |

## Backend mismatches

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Redis-backed deployments fail locally | Redis is not running or the host/port is wrong | Switch to the in-memory smoke test or start Redis before changing the code |
| Workspace actions fail only in production | The selected workspace backend or isolation policy is unsupported | Compare the workspace manager setup to the runtime backend before editing the service |
| Channels fail to connect | The credential object or channel config is incomplete | Re-check the channel constructor and required external credential fields |

## MCP and hub problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| MCP servers do not appear in the workspace | The client or default MCP list was never registered | Re-check `LocalWorkspaceManager(default_mcps=...)` and the MCP client config |
| A hub is visible but empty | The hub itself does not require credentials, but the underlying resource may | Verify the hub token or the resource-specific input schema |

## Safe next steps

- Run `scripts/service_smoke.py` before touching the live deployment.
- Use the in-memory message bus and a local workspace manager for the first pass.
- Escalate to the workspace-sandbox sub-skill only when the issue is really a backend/runtime sandbox problem.
