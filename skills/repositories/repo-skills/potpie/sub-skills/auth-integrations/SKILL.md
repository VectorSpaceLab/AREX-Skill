---
name: auth-integrations
description: "Handle Potpie account auth, provider credentials, provider reads,
  and ledger binding."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Potpie auth integrations

Use this sub-skill when the task is about Potpie login/logout, provider credentials, provider-specific read commands, or Event Ledger configuration.

## Read this when

- The user asks about `potpie login`, `potpie logout`, `potpie auth status`, `potpie github`, `potpie gitlab`, `potpie linear`, `potpie jira`, `potpie confluence`, `potpie gitbucket`, or `potpie ledger`.
- A workflow needs credentials before registering or pulling external sources.
- A command fails because an OAuth callback, PAT/API key, provider host, or ledger URL is missing.

## Do not use this for

- Pot/source tenancy itself: read `../workspace-boundaries/SKILL.md`.
- Runtime daemon readiness: read `../runtime/SKILL.md`.
- Graph reads or writes after data is available: read `../graph-read/SKILL.md` or `../graph-write/SKILL.md`.
- Installing bundled agent skills: read `../skills-management/SKILL.md`.

## Operating procedure

1. Separate Potpie account auth (`login`, `logout`, `whoami`) from provider auth (`github`, `gitlab`, `linear`, `jira`, `confluence`, `gitbucket`).
2. Use `potpie auth status --verify` when you need to confirm cached provider credentials rather than only listing configured providers.
3. Prefer provider-specific commands for instance details: GitLab and GitBucket often need host/base-url normalization; Atlassian commands split Jira and Confluence concerns; Linear uses API-key style reads.
4. Treat `potpie ledger ...` as configuration and roadmap/stub integration evidence unless the current runtime proves the provider path works. Do not promise full external-ledger sync from this skill alone.
5. Never ask a model to invent secrets. Require user-provided credentials, configured env vars, or existing local auth state.

## References

- `references/workflow.md` — provider command map, account-vs-provider auth, and ledger flow notes.
- `references/troubleshooting.md` — OAuth/PAT/callback, provider URL, refresh, and ledger-stub failure handling.

## Verification notes

- Safe native candidates include provider command-shape tests for GitHub, GitLab, Linear, Atlassian, GitBucket, auth helper/config tests, and credential-store tests.
- Live credentialed e2e auth tests are intentionally excluded from default verification.
