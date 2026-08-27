# Gateway and Inbox Troubleshooting

| Symptom | Layer | Fix |
|---|---|---|
| `/plan` 401 | Gateway inbound bearer | Send token matching `GATEWAY_API_KEY` or configure local no-auth intentionally. |
| Peer returns auth-required/401 | Peer outbound auth | Fix `agents[].auth`, token env var, or DID identity/Hydra provider. |
| `did_signed peer requires a gateway LocalIdentity` | Gateway DID not configured | Set seed/author/name or use another auth mode. |
| `Partial DID identity config` | Only some identity vars set | Set all identity variables or none. |
| Deadline/abort error | Stuck peer or low timeout | Increase `timeout_ms` or debug peer health. |
| Recipe not loaded | Bad name, empty description, duplicate, or denied permission | Fix frontmatter/permissions. |
| Inbox UI unavailable | Ports 3775/3787 occupied or npm deps missing | Free ports and run npm install/dev. |
| Personal agent stays down | Missing OpenRouter/Hydra settings, port issue, Python startup error | Check API logs and personal-agent log; verify settings. |
| Demo peers fail | Missing OpenRouter key or Hydra/network unavailable | Export key or skip credentialed demo. |
| Webhooks not recorded | Token mismatch or endpoint URL wrong | Align `BINDU_WEBHOOK_TOKEN` and agent webhook config. |
