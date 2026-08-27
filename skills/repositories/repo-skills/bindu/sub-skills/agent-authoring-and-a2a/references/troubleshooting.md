# Agent Authoring and A2A Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ConfigError: 'deployment.url' is required` | Missing nested deployment URL. | Add `"deployment": {"url": "http://localhost:3773"}`. |
| `deployment.url must be a valid http(s) URL` | Unsupported scheme or missing netloc. | Use `http://...` or `https://...`. |
| Handler validation says parameter must be `messages` | Handler has no args, too many args, or wrong parameter name. | Define `def handler(messages): ...`. |
| Handler returns prompt but task completes | Returned plain text instead of structured state. | Return `{"state":"input-required","prompt":"..."}`. |
| First response is only `submitted` | Normal task-first behavior. | Poll `tasks/get` until terminal. |
| `context_id` invalid params | Bad UUID string. | Send a valid UUID in `contextId` or omit it to start a new context. |
| `Context not found` while auth is enabled | Context belongs to another DID or does not exist. | Use the caller's own context id; do not probe tenant existence. |
| Cannot continue terminal task | Reused a completed/failed/canceled task id. | Create a new task id and optionally reference the old one. |
| `/agent/skills/{id}/documentation` missing | Skill lacks documentation content or wrong id. | Check skill path and frontmatter/YAML metadata. |
| Negotiation says no skills advertised | Config did not load skills. | Fix skill paths or inline definitions. |
| Port already in use | Existing Bindu/Gateway/other server owns the port. | Free the port or choose another deployment URL/port. |
