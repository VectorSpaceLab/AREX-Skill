# Admin and Collaboration Workflows

## Identity and access

- Bootstrap the first admin user if the deployment is fresh.
- Configure trusted headers, OAuth, LDAP, or SCIM only after confirming the proxy and identity source are consistent.
- Treat user/group/role changes as policy changes, not as general chat settings.

## Storage and session state

- Local storage is the easiest starting point.
- Redis-backed sessions or alternate storage providers are operator-level choices.
- If sessions disappear or files cannot be recovered, check the storage and session settings before reopening chat or file workflows.

## Collaboration features

- Channels, calendar, and automations are collaborative operator-facing workflows.
- They usually depend on the same identity and storage policies that protect the rest of the deployment.
- If a collaboration feature is broken, confirm auth and storage first.

## Observability and audit

- Telemetry and audit are optional but common in production deployments.
- `ENABLE_OTEL`, `OTEL_*`, and `ENABLE_AUDIT_*` are the main signals.
- Configure the export endpoint before trying to debug data loss or message flow.

## Practical operator questions

- Who is allowed to sign in?
- Which storage backend owns data and uploads?
- Which session or cache backend stores identity state?
- Are the collaboration features enabled for this deployment?
- Where do telemetry and audit logs go?

## Useful configuration groups

- `WEBUI_AUTH`, `WEBUI_ADMIN_EMAIL`, `WEBUI_ADMIN_PASSWORD`
- `WEBUI_AUTH_TRUSTED_*`
- `ENABLE_SCIM`, `SCIM_TOKEN`, `SCIM_AUTH_PROVIDER`
- `DATABASE_URL`, `REDIS_URL`
- `STORAGE_PROVIDER`, `S3_*`, `GCS_*`, `AZURE_STORAGE_*`
- `ENABLE_OTEL`, `OTEL_*`, `ENABLE_AUDIT_*`
