# Auth and integration troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `auth status --verify` reports missing credentials | Provider login was never completed or the token cache was cleared. | Run the provider-specific login/config command and retry `potpie auth status --verify`. |
| Browser/OAuth callback never completes | Redirect URI, local port, client ID, or browser session is invalid. | Re-run the provider login command, check callback/redirect settings, and capture the provider-specific error. |
| Token works in one CLI but not Potpie | Token scope, host URL, or provider account differs. | Use the matching provider command family and verify instance/site/workspace identifiers. |
| GitLab or GitBucket requests go to the wrong host | Base URL or self-hosted instance normalization is missing. | Reconfigure with an explicit host/base URL; do not assume github.com-style defaults. |
| Atlassian command works for Jira but not Confluence, or vice versa | Jira and Confluence share auth concepts but have distinct site/project/space semantics. | Use the command family matching the resource and confirm site/base-url fields. |
| Linear read fails with authorization error | API key is missing, expired, or lacks workspace access. | Refresh the key and verify the workspace/team/resource id. |
| `ledger use self-hosted` fails validation | Required URL/config argument is missing or malformed. | Provide the URL/config explicitly; then rerun `potpie ledger status`. |
| `ledger query` or `ledger pull` appears unsupported | External Event Ledger provider path is limited/roadmap in this version. | Treat ledger as configuration evidence; use local graph commands for supported memory operations unless the runtime proves the provider works. |
| Provider auth succeeded but graph reads are empty | Credentials do not imply source registration or graph records. | Route to `workspace-boundaries` for source registration and to `graph-read` for read diagnostics. |

## Live e2e caveat

Provider unit tests validate command shape and local behavior, but full end-to-end provider auth requires real credentials and external services. Do not make live e2e auth a default verification gate unless the user explicitly supplies credentials and asks for that scope.

## Safe recovery checklist

1. Identify the provider and resource: GitHub repo, GitLab project, Linear issue, Jira issue, Confluence page, or GitBucket repo.
2. Inspect auth state with `potpie auth status --verify`.
3. Re-run the provider-specific login/config command only after confirming the intended host and account.
4. Register or inspect the corresponding source separately.
5. Retry provider read or graph operation, preserving the original error if it still fails.
