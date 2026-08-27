# Setup and CLI Troubleshooting

## `chatchat init`

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Files were created in the wrong directory | `CHATCHAT_ROOT` was unset or changed between commands | Set `CHATCHAT_ROOT` explicitly; rerun `chatchat init` in the intended root; migrate or delete the accidental root only after backup. |
| `sqlite3.OperationalError: unable to open database file` | Data directory or DB parent is missing, often because imports ran before initialization | Run `chatchat init`; for scripts that only inspect routes, use a temp initialized root. |
| `--recreate-kb` fails during init | Embedding provider is not reachable | Run plain `chatchat init`; configure provider and embedding model; then run `chatchat kb -r`. |
| Template generation overwrote custom settings | Re-initialization after upgrade without backup | Restore from backup or version control; reapply custom provider/KB settings onto new templates. |

## `chatchat kb`

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Vector rebuild fails on provider errors | Embedding model name/endpoint/key is wrong | Fix `model_settings.yaml`; test provider embedding endpoint; rerun with a small KB first. |
| `--clear-tables` removed metadata | Destructive command used on production data root | Restore DB/content backup; avoid clear/prune commands until the target root is confirmed. |
| No files are indexed | Wrong KB name or content directory | Check `KB_ROOT_PATH`, `DEFAULT_KNOWLEDGE_BASE`, and `-n/--kb-name`; list files before rebuild. |
| External vector DB connection fails | Service config or credentials missing | Test service independently; verify `kbs_config`; fall back to FAISS only if acceptable to the user. |

## `chatchat start`

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| API/WebUI starts but requests fail | Provider models are not loaded or names mismatch | Use provider health/model list; update `MODEL_PLATFORMS`, defaults, and role configs. |
| Browser cannot reach WebUI/API from another machine | Host binding/public host settings are local-only or blocked by firewall/proxy | Review `DEFAULT_BIND_HOST`, `API_SERVER`, `WEBUI_SERVER`, firewall, and reverse proxy. |
| Port already in use | Existing Chatchat/Streamlit/Uvicorn process or another app | Stop the process deliberately or change YAML ports; do not kill broad process names blindly. |
| Streamlit file watcher or cache warnings | WebUI runtime settings/noisy dependencies | Usually non-fatal; focus on service URL and model/provider errors first. |

## Optional dependency warnings

- `auto_detect_model needs xinference-client installed`: install the Xinference extra only if Chatchat should query Xinference from this environment; otherwise disable auto-detect or list models manually.
- Requests/urllib3 warnings can appear with certain dependency resolutions; if HTTP behavior is broken, align `requests`, `urllib3`, and `charset_normalizer/chardet` versions in a clean environment.
- LangChain deprecation warnings are usually non-fatal for operation, but refresh the skill if upstream APIs change materially.

## Audit procedure

1. Run `chatchat --help` and subcommand help to verify CLI availability.
2. Run `scripts/chatchat_config_audit.py --chatchat-root <root>`.
3. Check provider model list independently.
4. Run API route or SDK probes only after the data root is initialized.
5. Escalate to service-specific logs only after config roots and provider names are correct.
