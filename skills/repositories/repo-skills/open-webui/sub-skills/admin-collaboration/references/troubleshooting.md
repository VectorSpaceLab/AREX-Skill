# Admin and Collaboration Troubleshooting

## Trusted headers or SSO fail

- **Symptom**: the proxy says the user is signed in, but Open WebUI rejects the request.
- **Likely causes**: the trusted header names do not match the upstream identity source, or the OAuth/LDAP/SCIM provider is misconfigured.
- **Recovery**: verify the header and provider mapping before changing the broader auth policy.

## Existing users block auth changes

- **Symptom**: disabling or radically changing auth is rejected on a live deployment.
- **Likely causes**: the deployment already has persisted users and the app protects against unsafe auth toggles.
- **Recovery**: make the change on a fresh instance or keep the existing policy.

## Redis or session problems

- **Symptom**: sessions vanish, login state is unstable, or multi-worker behavior is inconsistent.
- **Likely causes**: incorrect `REDIS_URL`, bad cluster/sentinel settings, or a session cookie mismatch.
- **Recovery**: verify the cache/session backend independently of the auth provider.

## Storage backend problems

- **Symptom**: uploads, files, or persistent state disappear or cannot be written.
- **Likely causes**: wrong storage-provider credentials, missing buckets, or permission issues.
- **Recovery**: confirm the selected storage backend and credentials, then re-check the deployment path.

## SCIM / provisioning issues

- **Symptom**: automatic provisioning or user sync does not update the app.
- **Likely causes**: token, provider, or upstream identity mismatches.
- **Recovery**: validate the SCIM settings and the identity source together.

## Telemetry and audit problems

- **Symptom**: traces, metrics, or audit events do not appear where expected.
- **Likely causes**: endpoint URL, auth, or exporter flags are wrong.
- **Recovery**: verify the export endpoint and the `ENABLE_OTEL_*` or `ENABLE_AUDIT_*` flags separately from the app login path.

## Safe checks to repeat

- Re-read the `configuration.md` table for the exact variable group.
- Re-run the deployment smoke check if the operator settings appear to affect startup.
- Separate identity problems from storage and telemetry problems before changing more than one variable at a time.
