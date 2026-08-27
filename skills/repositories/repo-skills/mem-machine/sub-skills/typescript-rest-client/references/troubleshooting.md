# TypeScript Troubleshooting

## Install And Runtime

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `npm` install/build fails with engine warning | Node version below `>=20.19.0` | Use a supported Node version. |
| Cannot import package | ESM/CJS mismatch or package not installed | Try default import in ESM, named import, or `require` according to project config; reinstall package. |
| TypeScript path alias errors in source checkout | Build tooling expects package tsconfig/aliases | Use the published package or run package scripts from the TS client package root. |

## Base URL And Auth

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| 404 on `/health` or `/memories/search` | Base URL prefix mismatch | Cloud default is `https://api.memmachine.ai/v2`; self-hosted server may need `http://host:8080/api/v2`. Test `healthCheck()` after changing. |
| 401/403 | Missing or invalid API key | Pass `api_key` from a secret environment variable; never log it. |
| Proxy/network errors | Axios proxy/fetch adapter interaction or corporate proxy | Check `HTTP_PROXY`/`HTTPS_PROXY`, adapter setting, and server reachability. |

## Memory Operation Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Empty results | Wrong project or memory context, wrong `types`, filter mismatch | Check `client.project({ org_id, project_id })` and `project.memory({ user_id, ... })`; remove filters for a first search. |
| Search option ignored | Python option name used in TS | Use `top_k`, `expand_context`, `score_threshold`, `agent_mode`, `types`, and `filter`. |
| Delete fails | Wrong ID type or endpoint unavailable | Use `memory.delete(id, 'episodic')` or `'semantic'` and verify server supports the route. |
| API error object unfamiliar | Error normalized into `MemMachineAPIError` | Catch `MemMachineAPIError` and inspect its message/status fields without logging secrets. |

## Self-hosted Server Checklist

1. Confirm `curl <base-url>/health` or `client.healthCheck()` works.
2. If using a self-hosted FastAPI server, try a base URL ending in `/api/v2`.
3. Provide `api_key` only if the deployment requires bearer auth.
4. Use a test project and non-sensitive memory content.
5. Compare equivalent Python/CLI call only if the server path remains unclear.
