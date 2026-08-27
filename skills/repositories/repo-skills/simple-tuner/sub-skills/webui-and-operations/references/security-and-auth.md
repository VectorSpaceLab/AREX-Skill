# Security, Auth, Quotas, and Audit

Use this reference when operating SimpleTuner as a shared WebUI/API service. Avoid printing secrets, tokens, cookies, private callback URLs, or local machine identity in user-visible handoffs.

## First-admin setup

On first launch, SimpleTuner requires creation of an administrator account before normal login.

- `GET /api/cloud/auth/setup/status` reports whether setup is still required.
- `POST /api/cloud/auth/setup/first-admin` creates the first admin with email, username, and password.
- After setup, manage users from the WebUI admin pages or the users API.
- Keep public registration disabled for private deployments unless the owner explicitly accepts the risk.

## Sessions and API keys

- Browser users authenticate with sessions.
- Automation can use API keys generated from the user's profile or admin panel.
- API keys use the `X-API-Key: <api-key-placeholder>` header.
- API key creation through the API requires an authenticated session cookie first.
- Treat API keys as secrets: never echo real values, store them in generated files, or include them in public text.

Example skeleton only:

```bash
curl -s <base-url>/api/training/status \
  -H 'X-API-Key: st_your_key_here'
```

## Users, levels, and permissions

Built-in user levels map to queue priorities and permission scopes:

| Level | Typical use |
| --- | --- |
| Viewer | Inspect status and outputs without submitting privileged work. |
| Researcher | Ordinary training and queue submission. |
| Lead | Higher priority and limited administrative controls such as priority overrides. |
| Admin | User management, auth provider setup, workers, approvals, audit, and system settings. |

Use custom levels for fine-grained access control. When diagnosing authorization failures, identify the user level and exact endpoint or UI action rather than broadening permissions blindly.

## External authentication

SimpleTuner supports OIDC and LDAP/Active Directory providers for SSO.

### OIDC

- Configure providers in the WebUI admin auth-provider page or `POST /api/cloud/external-auth/providers`.
- Required provider details include a unique name, enabled flag, client ID, client secret, discovery URL, scopes, default levels, optional level mappings, and whether users may be auto-created.
- The callback URL shape is `/api/cloud/external-auth/oidc/{provider-name}/callback` on the public SimpleTuner host.
- The login flow starts at `/api/cloud/external-auth/oidc/{provider}/start` and returns through the callback.
- OAuth state is persisted in the database so callbacks can survive restarts and load-balanced callbacks during the short authentication window.

### LDAP

- Configure server URL, TLS behavior, bind DN/password, user base DN, user filter, optional group base/filter, username/email/display attributes, default levels, and level mappings.
- LDAP login is submitted to `/api/cloud/external-auth/ldap/login`.
- Use a dedicated service account with minimal directory permissions and rotate its password according to site policy.

External-auth API endpoints:

- `GET /api/cloud/external-auth/providers`
- `POST /api/cloud/external-auth/providers`
- `PATCH /api/cloud/external-auth/providers/{name}`
- `DELETE /api/cloud/external-auth/providers/{name}`
- `GET /api/cloud/external-auth/providers/{name}/test`
- `GET /api/cloud/external-auth/available`

## Audit logging

Audit logs capture authentication, user management, API key actions, credential changes, and job operations. They are append-only through the public API and include a cryptographic hash chain.

CLI:

- `simpletuner auth audit list`
- `simpletuner auth audit list --event-type <event-type>`
- `simpletuner auth audit user <user-id>`
- `simpletuner auth audit security`
- `simpletuner auth audit stats`
- `simpletuner auth audit verify`

API endpoints require audit permission:

- `GET /api/audit`
- `GET /api/audit/stats`
- `GET /api/audit/types`
- `GET /api/audit/verify`
- `GET /api/audit/user/{user_id}`
- `GET /api/audit/security`

Security-relevant event families include `auth.login.success`, `auth.login.failed`, `auth.logout`, `auth.session.expired`, `auth.api_key.used`, user lifecycle events, API key lifecycle events, credential events, `job.submitted`, `job.cancelled`, `job.approved`, and `job.rejected`.

## Quotas, approvals, and cost limits

- Queue concurrency controls prevent one user or team from consuming all slots.
- Admins can update cloud and local concurrency through the queue settings UI or `POST /api/queue/concurrency`.
- Approval workflows can block jobs until an admin approves or rejects them.
- Cost limits can warn, block, or require approval for cloud providers.
- Review cost estimates and approval rules before submitting cloud jobs on behalf of another user.

Useful CLI surfaces:

- `simpletuner jobs approval list|pending|approve|reject|rules`
- `simpletuner cloud cost-limit show|set|disable`
- `simpletuner jobs status --format json`

## Production security posture

- Use HTTPS via server TLS or a trusted reverse proxy.
- Restrict network access to the WebUI/API; do not expose unauthenticated HTTP on untrusted networks.
- Keep self-registration disabled for private deployments.
- Use least-privilege user levels and worker tokens.
- Rotate API keys and worker tokens after suspected exposure.
- Verify audit-chain integrity during incident review.
- Do not publish local paths, local usernames, tokens, cookies, or raw sensitive terminal output in handoffs, PR text, job metadata, or model cards.
