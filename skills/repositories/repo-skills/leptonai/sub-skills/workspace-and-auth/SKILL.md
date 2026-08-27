---
name: workspace-and-auth
description: "Authenticate and select Lepton workspaces safely, build workspace
  API clients, and troubleshoot auth, URL, and token state without leaking
  credentials."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Workspace and Auth

Use this sub-skill when the task is to establish, inspect, switch, or debug the Lepton workspace context before doing any cloud work.

## Route here for

- `lep login` and `lep workspace login` flows, including credential strings in `<workspace_id>:<auth_token>` form.
- `lep workspace list`, `status`, `id`, `url`, `logout`, and `remove` usage.
- Local workspace records and current-workspace selection.
- Programmatic workspace API context with `APIClient(workspace_id, auth_token, url, workspace_origin_url)`.
- Environment fallback with `LEPTON_WORKSPACE_ID`, `LEPTON_WORKSPACE_TOKEN`, `LEPTON_WORKSPACE_URL`, and `LEPTON_WORKSPACE_ORIGIN_URL`.
- Diagnosing expired/invalid tokens, missing current workspace, URL/environment mismatches, and 401/403/404 workspace access failures.

## Route elsewhere for

- Creating, updating, stopping, or deleting endpoints, jobs, pods, Ray clusters, fine-tunes, storage, secrets, ingress, logs, or other live resources after auth is established.
- Dynamic endpoint invocation with the high-level endpoint `Client`; use the SDK/client sub-skill for endpoint call patterns.
- General `lep` command discovery and mutation-safety policy beyond workspace/auth commands.

## Non-negotiable safety rules

1. Never print, echo, log, save, or quote a raw workspace token unless the user explicitly requests token retrieval as the task itself. If the task only needs auth status, provide redacted status instead.
2. Treat `<workspace_id>:<auth_token>` as a secret-bearing credential string. Prefer environment variables, secure prompts, or user-side paste into `lep login`; do not put raw tokens in persistent notes.
3. Redact tokens in all summaries and copied command output. The safe display form is only a short prefix/suffix mask such as `ab****yz` or a generic `<redacted-token>`.
4. Verify auth before planning live resource operations. A workspace command being read-only does not make it non-credentialed; `status` and some `list` paths can contact the workspace API.
5. If a user asks to print a token but the stated goal is simply to verify login, refuse the raw-token path and run safer checks such as `lep workspace id`, `lep workspace url`, `lep workspace list`, or the bundled context checker.

## Fast path

1. Inspect context without exposing secrets:

   ```bash
   python scripts/check_workspace_context.py
   ```

2. If CLI checks are explicitly allowed, run read-only workspace checks with redaction:

   ```bash
   python scripts/check_workspace_context.py --run-cli --commands list id url
   python scripts/check_workspace_context.py --run-cli --commands status
   ```

3. If not logged in, use one of these user-side login forms:

   ```bash
   lep login
   lep login -c '<workspace_id>:<auth_token>'
   lep workspace login -i <workspace_id> -t '<auth_token>'
   ```

4. If a custom workspace API URL is required by the token issuer, include it at login time:

   ```bash
   lep workspace login -i <workspace_id> -t '<auth_token>' --workspace-url <workspace_api_url>
   ```

5. After auth succeeds, hand off resource-specific work to the appropriate workload, storage/secret/ingress, or SDK sub-skill.

## Read next

- Workspace records, CLI commands, environment variables, and redaction: [references/auth-and-workspaces.md](references/auth-and-workspaces.md)
- Programmatic `APIClient` construction and failure surfaces: [references/api-client.md](references/api-client.md)
- Recovery playbooks for common auth failures: [references/troubleshooting.md](references/troubleshooting.md)
- Safe local context helper: [scripts/check_workspace_context.py](scripts/check_workspace_context.py)
