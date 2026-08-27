# Troubleshooting

Use this table when the CLI or an external integration step fails.
Start with `scripts/check-cli.sh` and `yuxi remote list` before touching live
services.

| Symptom | Likely cause | Next move |
| --- | --- | --- |
| `python -m yuxi_cli --help` fails | wrong Python environment or package not installed | fix the local env, then rerun the offline smoke script |
| `remote 不存在` | current remote name is wrong or the config file was edited manually | run `yuxi remote list` and `yuxi remote use <name>` |
| remote URL seems to keep `/api` | manual config edit or stale mental model | store the instance base URL only; the CLI derives `/api` itself |
| `无法读取服务端 discovery` | the server does not expose discovery or is too old | upgrade the remote to a server that advertises discovery and `>=0.7.1` |
| capability error such as `cli.kb_upload` | the remote is missing the advertised CLI capability | do not force the command; switch to a server that supports it |
| `API Key 格式无效，应以 yxkey_ 开头` | the token is not a Yuxi API key | paste the real API key or use browser login |
| `authorization_pending` / `slow_down` during login | browser login is still waiting for approval | keep polling; only restart when the session expires |
| `expired_token` during login | the device-flow session expired | rerun `yuxi login --browser` |
| `remote 尚未登录` | no API key is stored for the selected remote | run login for that remote first |
| `chat` returns `请求来源无效` or `会话令牌无效` | the browser page is stale, cross-origin, or the session token changed | reopen the page from `yuxi chat` and do not reuse an old browser tab |
| browser chat stream ends with `终态前断开` | the remote SSE stream truncated before completion | retry the run and inspect the remote service health |
| `kb upload` hangs in CI | interactive prompts are waiting for a tty | pass `--yes`, `--kb-id`, or `--include-ext` |
| `kb upload` says there is no uploadable KB | only read-only connectors are available or the remote lacks the upload capability | pick a Milvus KB that supports documents |
| `kb upload` skips a file as unreadable, empty, symlink, too large, or unsupported | local file safety filter rejected it | fix the file or narrow the upload set |
| `kb upload` reports `已上传过` | duplicate filename or duplicate content was found | treat it as a skip unless the user explicitly wants to force re-upload |
| `agent eval` says the remote is not logged in | missing CLI auth for the selected remote | log in first, then rerun the eval |
| `agent eval` partial failure from Langfuse | some dataset items failed or timed out | lower `--max-concurrency`, raise `--timeout-seconds`, and verify the dataset inputs |
| `agent eval` cannot load a dataset | Langfuse environment variables or dataset name are wrong | set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, then confirm the dataset exists |
| `request_events_url must be relative` | a client sent an absolute URL to the CLI bridge | use the server-provided relative path only |

## Recovery order

1. Verify the CLI package and help output offline.
2. Check the current remote and config with `yuxi remote list`.
3. Probe the remote with `yuxi remote ping`.
4. Re-authenticate only if the discovery/version/capability gate is satisfied.
5. For write paths, confirm the user still wants the remote state change.
