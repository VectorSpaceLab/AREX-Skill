# agent-runtime Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| A run returns a model/provider error before any tool use | The model string is malformed or the provider backend is unavailable. | Check the provider/model route first. If the string is right, install the provider extra or fix the credential. |
| `Task` output does not match the requested shape | The response format or schema is too strict for the selected model. | Relax the schema, switch to a model/profile that supports structured output, or route through tools for schema shaping. |
| `do_async` appears to hang | The caller may be blocking the loop or waiting on a slow tool/model path. | Use `timeout`, reduce retry count, or inspect the upstream tool/backend route. |
| A run times out but should have returned something useful | The default is a hard failure, not a partial answer. | Set `partial_on_timeout=True` if the workflow can use a partial result. |
| Run output changes after a tool call | The task or tool may be mutating the same shared state. | Prefer explicit `Task` inputs and isolate context when you debug run control. |
| `Agent` construction raises about memory or storage | A persistence backend is missing or misconfigured. | Route to chat-memory-storage for session and backend troubleshooting. |

## Smoke check

```bash
python scripts/check_upsonic_install.py
```

If that script fails on a core import, do not debug provider APIs yet; reinstall the base package first.
