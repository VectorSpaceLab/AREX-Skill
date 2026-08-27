# Auth and integration workflow reference

Potpie has three related but separate surfaces:

1. **Potpie account auth** — `login`, `logout`, `whoami`.
2. **Provider credentials and reads** — GitHub, GitLab, Linear, Jira, Confluence, GitBucket.
3. **Event Ledger configuration** — source binding/query/pull configuration, with external-provider paths still limited/roadmap-oriented.

## Account and provider matrix

| Goal | Command family | Notes |
| --- | --- | --- |
| Potpie account login | `potpie login` | Authenticates the Potpie account/session, not every provider. |
| Potpie account logout | `potpie logout` | Clears account auth state. |
| Inspect account | `potpie whoami` | Use before assuming cloud/hosted capabilities are available. |
| Provider overview | `potpie auth status` | Lists provider auth state. Add `--verify` to validate cached credentials. |
| GitHub auth/read | `potpie github ...` | Use for GitHub-specific login/status/read workflows. |
| GitLab auth/read | `potpie gitlab ...` | Often needs an instance/base URL in addition to token state. |
| Linear auth/read | `potpie linear ...` | API-key style reads and issue/workspace access. |
| Jira auth/read | `potpie jira ...` | Atlassian auth; keep Jira project/site terms explicit. |
| Confluence auth/read | `potpie confluence ...` | Atlassian auth; separate from Jira command intent. |
| GitBucket auth/read | `potpie gitbucket ...` | Self-hosted style host normalization matters. |
| Ledger configuration | `potpie ledger ...` | Configure/query/pull/detach Event Ledger sources; do not assume full external sync without runtime proof. |

## Provider flow

1. Decide whether the task needs Potpie account auth, provider auth, or both.
2. Inspect state: `potpie auth status --verify` for provider credentials, `potpie whoami` for account state.
3. Use the provider command family, not a generic token prompt, so host-specific validation and messages apply.
4. Register source boundaries separately with `workspace-boundaries` if graph work will depend on the provider source.
5. Route to graph read/write only after the source and credentials are known to be available.

## Ledger flow

| Goal | Command | Caveat |
| --- | --- | --- |
| Inspect ledger state | `potpie ledger status` | Safe first check. |
| Query ledger | `potpie ledger query ...` | Treat results as runtime-dependent. |
| Bind ledger provider | `potpie ledger use ...` | `self-hosted` style bindings require URL/config. |
| Detach ledger | `potpie ledger disconnect` | Confirm intent before removing config. |
| Pull ledger data | `potpie ledger pull ...` | Do not promise source ingestion without a working provider runtime. |
| List sources | `potpie ledger sources list` | Useful for current configuration only. |

## Credential handling rules

- Do not invent tokens, client IDs, secrets, callback URLs, or provider hosts.
- Prefer user-provided credentials, already configured local auth state, or documented environment variables from the current runtime.
- When a live provider is required, tell the user which provider command must be rerun after credentials are available.
- Keep provider identity and pot/source identity distinct: a GitHub token does not automatically mean the current repo is linked to a pot.
