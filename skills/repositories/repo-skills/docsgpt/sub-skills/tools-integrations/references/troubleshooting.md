# Tools and Integrations Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| tool not visible | not loaded, disabled, wrong picker scope, required config absent | inspect available tools and agent tool ids; distinguish default/builtin/user tools |
| tool never called | description/schema weak or model lacks tools | clarify action/parameter descriptions and model capability |
| generic API parse fails | unsupported spec version, no paths, malformed YAML/JSON, complex/external refs | run offline validator; reduce to supported OpenAPI 3.x/Swagger 2.0 operations |
| request blocked by URL policy | private/link-local/metadata target or unsafe redirect | do not disable SSRF controls; expose an approved gateway |
| repeated write | timeout retried without idempotency | check remote state, add idempotency and approval before retry |
| MCP connection refused/403/timeout | backend cannot reach server, credentials/scopes wrong, timeout | test from backend network; rotate/reconfigure without logging secrets |
| MCP OAuth never completes | public callback mismatch or Redis unavailable | fix redirect/public API URL and event/status backend |
| code/artifact fails every call | sandbox runner absent, endpoint/token/kernel wrong | remove from defaults; verify isolated runner first |
| PPTX/DOCX/XLSX/PDF fails on Daytona but HTML works | render libraries absent from snapshot | build/select reviewed snapshot with render packages |
| Read Document times out | parsing queue absent, file too large/complex | run parsing worker, enforce limits, test tiny file |
| remote device offline | daemon stopped, token revoked, network, idle timeout | check CLI host status/service and server device state |
| remote command waits | Ask approval not completed or denylist forced approval | review exact split command; never bypass catastrophic guard |
| widget Network Error/CORS | `apiHost` points at frontend/wrong origin or proxy | point at backend API and configure exact CORS/HTTPS |
| Chatwoot loops/replies to wrong conversation | event filtering/account/assignee scope missing | filter bot events, constrain account/inbox and honor human takeover label |

Stop before weakening SSRF, sandbox isolation, device denylist, approval policy, OAuth validation, or third-party webhook authentication. These controls are security boundaries, not debugging inconveniences.
