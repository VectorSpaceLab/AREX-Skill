# CLI Reference

## When to read

Read this for verified `chatchat` command names and flags. These commands were inspected from the installed Click entry point for `langchain-chatchat` 0.3.1.3.

## Top-level command

```bash
chatchat [OPTIONS] COMMAND [ARGS]...
```

Commands:

| Command | Purpose |
| --- | --- |
| `init` | Initialize project data/config directories and optional knowledge-base vectors. |
| `kb` | Knowledge-base table/vector-store maintenance commands. |
| `start` | Start API server, WebUI, or both. |

## `chatchat init`

```bash
chatchat init [OPTIONS]
```

Options:

| Option | Meaning | Default / caution |
| --- | --- | --- |
| `-x`, `--xinference-endpoint TEXT` | Override Xinference API service URL | Default documented as `http://127.0.0.1:9997/v1`; use only if using Xinference. |
| `-l`, `--llm-model TEXT` | Set default LLM model in generated settings | Must match a model available from the configured platform. |
| `-e`, `--embed-model TEXT` | Set default embedding model | Must be reachable before vector rebuild. |
| `-r`, `--recreate-kb` | Also rebuild knowledge-base vectors | Requires embedding provider; avoid on first plain config generation if provider is not ready. |
| `-k`, `--kb-names TEXT` | Comma-separated KB names for rebuild | Default `samples`. |

Plain `chatchat init` creates directories, copies sample KB files, creates DB tables, and writes YAML config templates. With `--recreate-kb`, it additionally calls vector rebuild logic and therefore depends on embedding model availability.

## `chatchat kb`

```bash
chatchat kb [OPTIONS]
```

Options:

| Option | Meaning | Risk |
| --- | --- | --- |
| `-r`, `--recreate-vs` | Recreate vector stores for files under KB content folders | Requires embedding provider; can be slow for large KBs. |
| `--create-tables` | Create empty metadata tables if missing | Low risk. |
| `--clear-tables` | Drop/reset DB tables before recreation | Destructive; confirm backup and data root. |
| `-u`, `--update-in-db` | Update vectors for files already in DB | Requires embedding provider. |
| `-i`, `--increment` | Add vectors for local files not yet in DB | Requires embedding provider. |
| `--prune-db` | Delete DB docs not present in local folder | Destructive relative to DB metadata. |
| `--prune-folder` | Delete local files not present in DB | Destructive relative to files. |
| `-n`, `--kb-name TEXT` | Select one or more KB names | Multiple allowed. |
| `-e`, `--embed-model TEXT` | Specify embedding model for vector operations | Must match provider config. |
| `--import-db TEXT` | Import tables from a sqlite database | Validate source DB first. |

## `chatchat start`

```bash
chatchat start [OPTIONS]
```

Options:

| Option | Meaning |
| --- | --- |
| `-a`, `--all` | Run API server and WebUI. |
| `--api` | Run API server only. |
| `-w`, `--webui` | Run WebUI only. |

Default host/port come from `basic_settings.yaml`: API typically uses port `7861`; WebUI typically uses port `8501`.

## Validation checklist

Before `chatchat start`:

- `CHATCHAT_ROOT` points to the intended data/config root.
- `chatchat init` has completed for that root.
- `model_settings.yaml` model names match provider-visible names.
- Provider service is running if chat/RAG/model calls are expected.
- `kb_settings.yaml` vector-store config matches chosen backend.
- For WebUI access from another host, bind/public host settings are deliberate and safe.
