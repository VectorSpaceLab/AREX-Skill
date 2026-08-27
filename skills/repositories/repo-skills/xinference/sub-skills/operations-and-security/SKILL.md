---
name: operations-and-security
description: "Operate and secure Xinference deployment surfaces, including
  environment variables, auth, API keys, metrics, logging, Web UI static
  serving, and production deployment notes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Operations and Security

Use this sub-skill for production-facing Xinference concerns: environment
variables, persistent state, auth bootstrap, API keys, OIDC, audit/admin,
metrics, logging, frontend static serving, IP and network exposure,
Docker/Kubernetes deployment, and operational safety.

## Use this for

- `XINFERENCE_HOME`, model cache/source, launch history, log, auth DB, and
  frontend dist path planning.
- Health checks, metrics exporter host/port, disabling metrics, request
  timeouts, concurrency, batching, and launch strategy knobs.
- Advanced auth, users, API keys, password reset/migration CLI entry points,
  JWT/encryption key persistence, OIDC, audit logs, and Elasticsearch-backed
  audit search.
- Allowed IPs, trusted proxies, permissive CORS caveats, and network exposure
  boundaries.
- Docker, Docker Compose, Kubernetes, and static Web UI deployment notes.

## Route elsewhere

- Model launch flags, replicas, GPU placement, cache/model lifecycle CLI syntax,
  and distributed supervisor/worker command templates: `serving-and-cli`.
- Model families, optional backend extras, LoRA, virtualenv model dependencies,
  and custom model specs: `models-and-backends`.
- Python client calls, HTTP request bodies, OpenAI-compatible snippets, and
  streaming behavior: `client-and-api`.

## Working pattern

1. Establish the deployment shape: local, Docker/Compose, Kubernetes, or a
   supervisor/worker cluster behind a proxy.
2. Choose persistent `XINFERENCE_HOME` and related DB/log/cache paths before
   enabling auth or relying on launch history.
3. Decide whether advanced auth stays enabled; if it does, plan admin bootstrap,
   API key issuance, token storage, and recovery procedures.
4. Configure network exposure separately from CORS. Treat allowed IPs and
   trusted proxies as access-control inputs.
5. Decide metrics/logging/audit policy before exposing `/metrics` or collecting
   audit records.
6. Route model-specific failures or request-body failures to sibling sub-skills.

## Security rules

- Never invent or print real default credentials, JWT secrets, encryption keys,
  OIDC client secrets, model hub tokens, or API keys.
- Use placeholders such as `<api-key>`, `<jwt-secret>`, and `<oidc-client-secret>`
  in examples.
- Persist auth secrets and databases under stable storage before depending on
  users, permissions, or API keys across restarts.
- Treat permissive CORS as non-authoritative; use network boundaries, IP
  restrictions, and trusted proxy settings for real access control.
- Keep static environment matrices from reading live secret values unless the
  user explicitly asks for a local audit.

## References

- [Configuration](references/configuration.md) for environment variables grouped
  by persistence, model source, health, launch, frontend, auth, and virtualenv.
- [Security and auth](references/security-and-auth.md) for advanced auth, API
  keys, OIDC, reset/migration, and audit/admin guidance.
- [Metrics and observability](references/metrics-and-observability.md) for
  Prometheus metrics, logging, and OpenTelemetry notes.
- [Deployment notes](references/deployment-notes.md) for local, Docker, Compose,
  Kubernetes, frontend, and external-service caveats.
- [Troubleshooting](references/troubleshooting.md) for auth failures, missing
  Web UI assets, disabled metrics, proxy/IP issues, and persistence mistakes.

## Helper script

- [render_env_matrix.py](scripts/render_env_matrix.py) prints a static matrix of
  important environment variables without reading or revealing live values.
