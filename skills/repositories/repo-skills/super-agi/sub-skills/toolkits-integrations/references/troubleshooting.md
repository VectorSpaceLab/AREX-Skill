# Toolkits and Integrations Troubleshooting

## Symptoms and Recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| Tool cannot be imported dynamically | Folder name or module path mismatch, or the checkout layout changed. | Re-run the static inventory helper and inspect the `folder_name`, `class_name`, and `file_name` fields. |
| Tool executes but fails validation | The tool's input JSON does not match the schema derived from the function signature. | Compare the payload with the tool's `args` schema and the signature of its `execute`/`_execute` method. |
| Missing toolkit config value | The DB record is absent, encrypted, or the fallback `config.yaml` lacks the key. | Check the toolkit's `get_env_keys`/`ToolConfiguration` entries and the config reference. |
| Secret decrypt error | Stored toolkit value is encrypted with the wrong key or is malformed. | Verify `ENCRYPTION_KEY` and the stored DB value before retrying. |
| Marketplace download fails | GitHub/network access is unavailable or the target repo path is wrong. | Treat the downloader as an external side effect and confirm the source repo before retrying. |
| `apt` or pip install changes too much | The installer script is container-oriented and not safe for casual host use. | Prefer Docker or an isolated environment; do not run the installer without authorization. |
| Unknown tool at runtime | Tool name normalization or registration missed the expected `Tool` record. | Check the exact toolkit name and the normalized tool name used during execution. |

## Safe Checks

- Use the bundled static inspector for a checkout-wide inventory before any
  download.
- Use the payload validator in `agents-workflows` for end-to-end agent payloads
  if the tool is only one field among many.
- Avoid network or apt-based recovery unless the downstream user wants the
  integration to mutate the checkout or container.
