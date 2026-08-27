# CVAT SDK troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: cvat_sdk` | Package not installed in the active Python | Run `python -m pip install cvat-sdk`; verify with `python -c "import cvat_sdk"`. |
| `ModuleNotFoundError: torch` when importing `cvat_sdk.pytorch` | Optional PyTorch extra not installed | Install `pip install "cvat-sdk[pytorch]"` in an environment compatible with your Torch backend, or avoid the PyTorch adapter. |
| `ModuleNotFoundError: numpy` for mask helpers | `masks` extra not installed | Install `pip install "cvat-sdk[masks]"`. |
| Unsupported server warning | SDK/server minor versions do not match the supported range | Install a matching `cvat-sdk` for the server or set strict `Config(allow_unsupported_server=False)` to fail early. |
| Auth store permission error | Profile file or parent directory is group/world-readable | Fix owner-only permissions (`0600` for file, `0700` for directory) or recreate profiles via `cvat-cli profile create`. |
| Script unexpectedly prompts for password | No PAT/profile and no password supplied via secure runtime channel | Prefer `access_token=...`, `CVAT_ACCESS_TOKEN`, or profile reuse. If password auth is required, pass a secret value at runtime. |
| Resource ID returns 404 or list appears empty | Wrong organization context or personal workspace vs organization mismatch | Set `client.organization_slug` correctly or test with no org context. |
| SSL/certificate failure on self-hosted test server | Private/self-signed certificate | Prefer fixing trust roots. Use `Config(verify_ssl=False)` or CLI `--insecure` only for explicitly trusted test systems. |
| Upload/import/export hangs or fails after a request id | Background worker/server error | Lower operation size, inspect CVAT worker logs, verify file format and labels, and catch `BackgroundRequestException`. |
| `Bad request` during task creation | Invalid label schema, wrong resource type, bad data params, or unavailable server-share/cloud-storage path | Validate labels JSON, use `ResourceType.LOCAL/REMOTE/SHARE` correctly, and check `data_params`. |
| `conv_mask_to_poly` ignored or fails | Format/shape combination does not support the requested conversion | Use a format that supports masks/polygons and test on a small annotation archive first. |
| Downloaded frames have unexpected extensions | The SDK guesses from image MIME type unless `image_extension` is provided | Pass `image_extension="jpg"` or another explicit extension. |

## Credential hygiene

Never print access tokens, profile file contents, passwords, cookies, or `Authorization` headers. If debug logging is enabled, redact logs before sharing. Do not embed PAT values in generated scripts; accept them through environment variables, a secret manager, or CVAT profiles.

## Version and generated API mismatches

The high-level SDK wraps a generated REST client derived from the CVAT server schema. If a method or model field is missing:

1. Check server and SDK versions.
2. Prefer the SDK version matching the server release.
3. If using a development server, regenerate or install the corresponding development SDK before relying on new endpoints.
4. Use `client.api_client.call_api()` only as a narrow fallback and document the endpoint.

## Data upload/import failures

Before retrying a large upload:

- Confirm the `resource_type` matches the input (`LOCAL`, `REMOTE`, or `SHARE`).
- For remote URLs, confirm the CVAT server can reach the URLs, not just the client machine.
- For server-share paths, confirm the path is visible to the CVAT server container/service.
- For cloud storage, confirm `cloud_storage_id` belongs to the correct organization/workspace.
- Use small fixtures first; then scale up after format/label validation passes.

## Background request recovery

For failed imports/exports/backups, capture the operation type, resource id, format name, status message, and whether images were included. Retry only after changing the suspected cause; blind retries usually repeat malformed archive or label errors.
