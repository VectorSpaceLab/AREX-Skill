# TaskingAI Cross-Cutting Troubleshooting

Read this when a TaskingAI task crosses deployment, backend APIs, inference providers, plugin bundles, storage, or service-development setup. For focused workflow details, route to the relevant sub-skill.

## Fast triage order

1. **Classify the failing layer.** Deployment/ports/env belongs to `deployment-configuration`; backend objects and generation belong to `backend-api`; provider/model calls belong to `inference-providers`; plugin execution/storage belongs to `plugin-bundles`.
2. **Prefer static checks first.** Use `scripts/check_taskingai_env.py`, `scripts/summarize_taskingai_routes.py`, and `scripts/inspect_taskingai_catalogs.py` before starting services or calling providers.
3. **Separate local validation from external calls.** Missing env vars, bad schema fields, bad route prefixes, and blacklisted URLs are local failures. Provider auth, quotas, remote API errors, S3 access, and Docker pulls are external failures.
4. **Ask before side effects.** Docker Compose startup, broad pytest runs, provider credential tests, S3 integration, database migrations, or service cleanup mutate state or consume network/quota.

## Python import and dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TypeError: duplicate base class TimeoutError` while importing backend modules | `aioredis==2.0.1` in the backend dependency set is incompatible with Python 3.11+ | Use Python 3.10 for backend service inspection/development, or patch/upgrade the Redis dependency only as an explicit code-maintenance task. |
| Pydantic warnings about protected namespaces such as `model_id` | FastAPI/Pydantic v2 warns about model fields with `model_` prefixes | Treat as non-fatal unless validation fails; do not chase these warnings before checking actual request errors. |
| `Env ... is not set` during service import/startup | Required service env var missing for the selected purpose | Run `scripts/check_taskingai_env.py --profile backend-api`, `backend-web`, `inference`, `plugin`, or `compose` against the user's env file and fix missing fields. |
| Import works for one service but not another | The repo has separate service roots all named `app`; importing several services in one Python process can resolve the wrong package | Inspect backend, inference, and plugin in separate processes with service-specific source paths. Do not combine their `app` packages in one interpreter. |

## Docker and service reachability

- If the console loads but API calls fail, check nginx/public routing, backend-web health, and the public `HOST_URL` first.
- If backend generation fails when it reaches a model or tool, check `TASKINGAI_INFERENCE_URL` and `TASKINGAI_PLUGIN_URL` from the backend service's network namespace, not from the host shell.
- Inside Compose, `localhost` usually points at the current container, not the sibling service. Use service DNS names such as the inference/plugin service names in internal URLs.
- If health checks fail immediately after startup, inspect missing env variables, DB/Redis readiness, and volume permissions before changing application code.

## Database, Redis, and storage

| Surface | What to check |
| --- | --- |
| Postgres/pgvector | `POSTGRES_URL`, user/password/db, pgvector image readiness, database migrations/schema version, network reachability from backend. |
| Redis | `REDIS_URL` or Compose Redis password/db values, container health, and Python version compatibility for `aioredis`. |
| Local object storage | `OBJECT_STORAGE_TYPE=local`, `PATH_TO_VOLUME`, write permissions, `HOST_URL`, and whether generated URLs are reachable by the browser/provider. |
| S3 object storage | `S3_ENDPOINT`, bucket name, access key/secret, public domain, image bucket fallback behavior for plugin service, and network egress. |

## Provider and plugin credentials

- Missing credential fields or invalid encrypted credentials are request-validation problems; fix schema keys before retrying external calls.
- Upstream HTTP status, auth, quota, or provider-specific error payloads are provider/plugin external failures. Preserve the provider's error body when reporting.
- For synthetic checks, use no-credential plugin bundles (`arithmetic`, `calculator`, or similar) and the debug/local provider only when the deployment mode allows it.
- Do not paste real API keys into skill files, issue reports, or prompts. Ask the user to run credentialed tests in their environment when needed.

## Native tests and side-effect policy

TaskingAI source tests are useful evidence but are not safe default smoke tests. Backend tests require DB/Redis and service dependencies; inference tests often need live provider endpoints and credentials; plugin tests may need object storage and optional vision provider keys. Run only the narrow native case that matches the user's task and environment, after documenting prerequisites and side effects.
