# Workspace/Auth Troubleshooting

Use this playbook before attempting live resource operations. Keep all token values redacted in commands, notes, screenshots, and copied output.

## Quick triage

1. Inspect local environment presence without printing tokens:

   ```bash
   python scripts/check_workspace_context.py
   ```

2. If credentialed read-only checks are allowed, inspect the persisted CLI context:

   ```bash
   python scripts/check_workspace_context.py --run-cli --commands list id url
   ```

3. If the task requires a live workspace-info check, run:

   ```bash
   python scripts/check_workspace_context.py --run-cli --commands status
   ```

4. If any raw token appears in terminal output, stop copying that output and replace the token with `<redacted-token>` before sharing or saving.

## Failure modes

| Symptom | Likely cause | Safe diagnosis | Recovery |
|---|---|---|---|
| `It seems that you are not logged in. Please run lep login first.` | No current persisted workspace record for CLI workspace commands. | Run `lep workspace list` to see stored records; run `lep workspace id` to confirm current selection. | `lep login`, or `lep workspace login -i <workspace_id> -t '<auth_token>'`; if a record exists, `lep workspace login -i <workspace_id>` can switch to it. |
| `You have not specified a workspace id, and have not set the current workspace either.` | `WorkspaceRecord.client()` was called without a current persisted record. | Check current record with `lep workspace id`; check env presence with the bundled script. | Log in through the CLI or pass explicit `APIClient(...)` context. |
| `You must specify workspace_id or set LEPTON_WORKSPACE_ID...` | `APIClient()` could not resolve any workspace id. | Check whether `LEPTON_WORKSPACE_ID` is set and whether a current persisted record exists. | Pass `workspace_id=...`, set `LEPTON_WORKSPACE_ID`, or run `lep login`. |
| 401 unauthorized | Token missing, expired, invalid, or not yet propagated. | Run `lep workspace list` and inspect the masked expiry column; confirm no raw token is being printed. | Reissue a token, then `lep login -c '<workspace_id>:<auth_token>'` or `lep workspace login -i <workspace_id> -t '<auth_token>'`. For a fresh token, wait a few minutes and retry. |
| 403 forbidden | Token is valid somewhere but not for this workspace URL/environment, or the user lacks access. | Compare `lep workspace url` with the intended Lepton environment; check `LEPTON_WORKSPACE_URL` and `LEPTON_WORKSPACE_ORIGIN_URL` presence. | Login again with the correct API URL: `lep workspace login -i <workspace_id> -t '<auth_token>' --workspace-url <workspace_api_url>`. Clear stale env overrides. |
| 404 workspace not found | Wrong workspace id or newly created workspace not fully provisioned. | Verify the workspace id, not the token. Avoid trying resource operations. | If just created, wait 5-10 minutes; otherwise log in with the correct id and token. |
| `Workspace '<id>' not found; please provide --auth-token.` | Trying to switch to a new workspace id without a token. | Run `lep workspace list`; if the id is not listed, a token is required. | `lep workspace login -i <workspace_id> -t '<auth_token>'`. |
| CLI context differs from Python `APIClient()` context | Environment variables override `APIClient()` while CLI workspace commands read the persisted record. | Run the bundled script and compare env presence with `lep workspace id/url`. | Either clear env overrides or align `LEPTON_WORKSPACE_ID`, `LEPTON_WORKSPACE_TOKEN`, `LEPTON_WORKSPACE_URL`, and the persisted record. |
| Token expiry shows `-` | Expiry could not be fetched, is unsupported for the workspace type, or the token could not be matched. | Treat absence as unknown, not proof of validity. | If auth fails or expiry is suspected, reissue a token and log in again. |

## URL mismatch / 403 workflow

1. Do not retry resource create/update/delete commands.
2. Run `lep workspace id` and `lep workspace url` if a persisted record is current.
3. Inspect whether `LEPTON_WORKSPACE_ID`, `LEPTON_WORKSPACE_URL`, or `LEPTON_WORKSPACE_ORIGIN_URL` is set in the running process.
4. Confirm the token was issued for the same Lepton environment as the workspace API URL.
5. Re-login with the correct URL if needed:

   ```bash
   lep workspace login -i <workspace_id> -t '<auth_token>' --workspace-url <workspace_api_url>
   ```

6. Only after `lep workspace status` succeeds should resource-specific commands resume.

## Expired or invalid token workflow

1. Prefer `lep workspace list` to inspect masked token and expiry status.
2. If the token is expired or near expiry, reissue a new token in the dashboard.
3. Log in with the new token:

   ```bash
   lep login -c '<workspace_id>:<auth_token>'
   ```

4. If a bad persisted record keeps being selected, remove it:

   ```bash
   lep workspace remove -i <workspace_id>
   ```

5. If the token was just created, wait a few minutes before deciding it is invalid.

## Newly created workspace workflow

- A newly created workspace can return unauthorized or not-found while backend setup propagates.
- Top-level `lep login` retries unauthorized responses for a short propagation window; `lep workspace login` reports the first failure.
- Wait 5-10 minutes before escalating a newly created workspace failure.
- Do not keep switching URLs or reissuing tokens during the provisioning window unless the workspace id or URL is clearly wrong.

## Token printing hazards

Do not use these for routine auth status:

```bash
lep workspace token
python -c 'from leptonai.api.v2.client import APIClient; print(APIClient().token())'
```

Safer alternatives:

```bash
lep workspace id
lep workspace url
lep workspace list
lep workspace status
python scripts/check_workspace_context.py --run-cli --commands list id url
```

If a user asks to print the token but their actual task is status, deployment, logs, or debugging, respond with: "I do not need the raw token for that task; I will check workspace id, URL, and status with token redaction instead." Only retrieve a raw token when the user's explicit deliverable is token retrieval, and never save it into notes.
