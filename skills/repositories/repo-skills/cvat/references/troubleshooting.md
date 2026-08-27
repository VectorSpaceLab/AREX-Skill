# CVAT cross-cutting troubleshooting

| Symptom | Likely cause | Route/fix |
|---|---|---|
| `cvat_sdk` or `cvat-cli` import/command missing | Package not installed in the active environment | Install `cvat-sdk`/`cvat-cli`; run `scripts/cvat_env_check.py`; then read `sub-skills/sdk-automation/` or `sub-skills/cli-automation/`. |
| SDK warns about unsupported server | SDK and server minor versions differ | Install the SDK/CLI version matching the server; see SDK troubleshooting. |
| Auth prompts unexpectedly | No PAT/profile/password secret available | Prefer profiles or `CVAT_ACCESS_TOKEN`; avoid embedding passwords/tokens. |
| Resource is not found | Wrong organization workspace or personal workspace | Set `--org`/`client.organization_slug` correctly. |
| Dataset import/export fails | Format/archive/layout/label mismatch | Read `sub-skills/dataset-ops/references/troubleshooting.md`. |
| Auto-annotation returns no shapes | Label mismatch, threshold/ROI issue, bad function spec, or missing model deps | Read `sub-skills/auto-annotation/references/troubleshooting.md`. |
| Docker CVAT stack is unreachable | Containers not running, host/port mismatch, unsupported browser, or missing admin user | Read `sub-skills/deployment-admin/references/troubleshooting.md`. |
| Serverless models absent | Serverless overlay or Nuclio function not ready | Route to auto-annotation serverless docs and deployment-admin service checks. |
| GPU workflow unverified | Python CPU import is not a GPU/backend check | Verify the actual GPU deployment/function separately before claiming support. |

## Privacy and safety

- Do not print PATs, passwords, cookies, auth store contents, or server tokens.
- Treat delete/import/restore/auto-annotation/volume-removal operations as side-effecting.
- For large datasets or deployments, validate a tiny sample and a dry command first.
- For self-hosted services, distinguish local-client reachability from server/container reachability.
