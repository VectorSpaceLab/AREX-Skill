# Authentication, Storage, and Observability

## Authentication modes

| `AUTH_TYPE` | Behavior | Main caution |
|---|---|---|
| unset/`None` | no authentication | safe only for isolated local use unless another trusted gateway enforces access |
| `simple_jwt` | one shared bearer token | broad blast radius; rotate and protect it |
| `session_jwt` | per-session/user JWTs | protect signing secret and token issuance |
| `oidc` | external IdP login with PKCE, then DocsGPT session JWT | issuer, redirects, claims, groups, proxy headers and cookies must agree |

OIDC preflight:

1. verify discovery for `OIDC_ISSUER`;
2. register the exact callback/public frontend origins;
3. set client id and optional secret;
4. choose stable `OIDC_USER_ID_CLAIM` (email is common when paired with SCIM);
5. verify group claim/allowlist before enforcing it;
6. map admin groups deliberately;
7. test login, refresh, logout and session revocation behind the real proxy.

`LOCAL_MODE_ADMIN=true` is not a shortcut for OIDC/RBAC. It applies only to no-auth local mode and must remain false on networked deployments.

## SCIM and RBAC

- Enable SCIM only with a long bearer token and restricted network exposure.
- Align SCIM `userName` with the OIDC user identity claim.
- Test create, update/deactivate, and group changes in a staging tenant.
- Persisted admin grants apply under OIDC; bootstrap the first admin with a controlled administrative command or IdP group mapping.
- Separate global admin, team roles, source sharing, and agent sharing when diagnosing `403`.

## Postgres

`POSTGRES_URI` accepts standard Postgres forms and is normalized internally. In managed services, include required TLS options. Production databases should be pre-created and migrated out of band.

Before migration:

- record application and migration versions;
- back up and verify restore;
- estimate locks/runtime;
- stop incompatible workers if required;
- run migration once;
- verify schema and high-value queries;
- retain rollback or forward-fix instructions.

## Vector storage versus user-data storage

Selecting FAISS, Qdrant, Milvus, Elasticsearch, MongoDB Atlas, or pgvector changes document embeddings storage, not the canonical Postgres user-data store. GraphRAG requires pgvector.

## Object storage

Set `STORAGE_TYPE=s3` for AWS S3 or an S3-compatible service. Configure bucket, credentials, region, optional endpoint, and path-style behavior. Use `S3_PATH_STYLE=true` for services that require it. Credentials need only the bucket actions DocsGPT uses.

- `URL_STRATEGY=backend` keeps downloads behind DocsGPT authorization.
- `URL_STRATEGY=s3` exposes direct/presigned object URLs; verify expiry, CORS and tenant isolation.
- Test put/get/delete/list against a staging prefix before migration.
- User-data backup and object backup are separate recovery concerns.

## Observability

OpenTelemetry packages cover Flask/Starlette, Celery, requests, Redis, SQLAlchemy/psycopg and logging. Configure exporter endpoint/resource attributes at deployment level.

Correlate:

- HTTP request/activity id;
- user/agent id without secret values;
- Celery task id and queue;
- source/workflow/schedule run id;
- model id/provider and token usage;
- tool attempt and error type.

Do not emit prompts, tool credentials, bearer tokens, attachment bytes, or full provider responses by default. Validate logs after enabling instrumentation because auto-instrumentation can expose headers or payloads if configured carelessly.
