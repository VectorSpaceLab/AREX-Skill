# Deployment and Configuration Troubleshooting

| Symptom | Cause candidates | Recovery |
|---|---|---|
| import fails on Python 3.13 or compiled package install | supported development target is Python 3.12; compiled wheels may lag | create an isolated 3.12 environment and install exact backend requirements |
| startup tries to create/migrate a production DB | development defaults are enabled | stop rollout; set `AUTO_CREATE_DB=false`, `AUTO_MIGRATE=false`; run controlled migrations |
| `POSTGRES_URI is not set; skipping database bootstrap` | no user-data connection configured | configure Postgres before using persisted routes; import-only checks are not deployment readiness |
| worker receives no tasks | broker URL mismatch, queue restriction, Redis failure | compare web/worker URLs and queue names; use a bare worker temporarily for diagnosis |
| `/mcp` or reconnect route 404 | Flask-only server or proxy path mismatch | run ASGI target; inspect proxy route table |
| custom models missing | key env unset, directory absent, model disabled, malformed catalog, unregistered provider | run bundled validator; inspect startup warnings/errors; use one live model test |
| app fails on model YAML | unknown key/provider/alias or duplicate/incompatible definition | fix schema; keep stable ids; restart and query model listing |
| OIDC redirect loop | public URL/callback mismatch, proxy scheme/host, cookie policy, issuer or clock | compare exact browser URL and registered redirect; inspect discovery and token claims |
| OIDC user authenticates but receives 403 | group allowlist/admin/team/source authorization | inspect normalized claims and authorization layer separately |
| S3 upload works but download fails | URL strategy, CORS, signing, endpoint/path style or bucket policy | test server-side get then browser access; minimize bucket permissions |
| SSE stalls behind proxy | buffering, compression, idle timeout or insufficient workers | disable buffering for event routes; set keepalive/timeout; size WSGI threadpool/concurrency |
| high parser-worker memory | Docling/OCR buffering, large input, child not recycled | lower pipeline queue size, enforce limits, split parsing queue, tune child memory recycle |

## Safe diagnosis commands

```bash
python scripts/check_services.py --api-url http://localhost:7091
python scripts/validate_model_catalog.py ./models-config
```

Do not paste connection strings or settings dumps into tickets. Redact userinfo, query parameters, tokens, bucket names when sensitive, and private hostnames.

## When to stop

Stop before changing production identity provider settings, rotating encryption/JWT keys, rerunning a backfill, dropping indexes/tables, truncating E2E data on a shared database, or changing bucket ownership. Require backup, impact analysis, staged verification and rollback.
