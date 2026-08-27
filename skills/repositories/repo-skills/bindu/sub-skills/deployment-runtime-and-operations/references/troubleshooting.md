# Deployment and Operations Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `bindu` not found | Package/CLI not installed in active env. | Install Bindu or use the environment's Python/console script. |
| `serve` says `--grpc or --script required` | Missing mode. | Pass one serve mode. |
| Port 3773/3774 occupied | Stale server or Gateway. | Stop process or choose another URL/port. |
| boxd credentials missing | No `BOXD_API_KEY`/`BOXD_TOKEN`. | Export credentials before live deploy; dry-run does not need cloud. |
| Source too large | Tarball >50 MB. | Add large paths to `.binduignore`. |
| Sensitive files dropped | Safety exclusion working. | Use `--env KEY=VALUE` for runtime secrets. |
| VM health timeout | Script failed, deps missing, or port held inside VM. | `bindu logs AGENT`; inspect startup error. |
| Wrong code after redeploy | Old process or corrupted upload. | Redeploy; check runtime logs and source upload verification. |
| Postgres connect failure | Bad URL/driver/network/schema. | Use asyncpg URL, verify DB reachability, run migrations. |
| Redis scheduler loop errors | Redis unreachable. | Fix `redis_url`/network; use memory scheduler locally. |
| OTLP export errors | Bad endpoint/vendor path. | Verify collector URL and headers. |
| Tunnel creation fails | FRP/network/subdomain issue. | Continue local-only or fix tunnel settings. |
