# Configuration Files and Managed State

The CLI stores state under `DATA_DESIGNER_HOME`, defaulting to `~/.data-designer`. Set `DATA_DESIGNER_HOME` before invoking the CLI when you need an isolated state directory.

## Files and directories

| Path under `DATA_DESIGNER_HOME` | Root shape | Used by | Notes |
| --- | --- | --- | --- |
| `model_providers.yaml` | `providers:` | `config providers`, `config list`, `agent state model-aliases`, generation health checks | Stores provider endpoints, provider types, and API key references. |
| `model_configs.yaml` | `model_configs:` | `config models`, `config list`, `agent state model-aliases`, generation commands | Stores model aliases. Alias presence does not imply usability. |
| `mcp_providers.yaml` | `providers:` | `config mcp`, `config list`, `check-models` | Stores MCP provider definitions. |
| `tool_configs.yaml` | `tool_configs:` | `config tools`, `config list`, `check-models` | Stores tool aliases and MCP provider references. |
| `plugin_catalogs.yaml` | `catalogs:` | `plugin catalog add/list/remove` and package metadata commands | Stores user-added catalogs only; the built-in `nvidia` catalog is always available. |
| `plugin-catalog-cache/` | JSON cache files | `plugin list/search/info/install/uninstall` | Cache files are keyed by catalog alias and URL hash. |
| `managed-assets/datasets/` | locale parquet files | `download personas`, `agent state persona-datasets`, persona sampling workflows | Installed state is checked per locale. |

External state:

| Path | Used by | Notes |
| --- | --- | --- |
| `~/.ngc/config` | `download personas` | Required for non-dry-run NGC downloads; create with `ngc config set`. |

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DATA_DESIGNER_HOME` | Overrides the root CLI state directory. |
| `DATA_DESIGNER_DEFAULT_PLUGIN_CATALOG_URL` | Repoints the built-in `nvidia` plugin catalog URL for QA/staging/local testing. |
| `NVIDIA_API_KEY` | Default API key variable for the built-in NVIDIA provider. |
| `OPENAI_API_KEY` | Default API key variable for the built-in OpenAI provider. |
| `OPENROUTER_API_KEY` | Default API key variable for the built-in OpenRouter provider. |

## Bootstrap behavior

- Every non-`--version` CLI invocation best-effort initializes missing default provider/model config settings.
- A fresh state can contain default model aliases while `agent context` still reports no usable aliases because API keys are missing.
- Verify actual readiness with `data-designer agent state model-aliases`.

## Persona locales

Built-in managed persona locales and sizes:

| Locale | Size |
| --- | --- |
| `en_US` | 1.24 GB |
| `en_IN` | 2.39 GB |
| `en_SG` | 0.30 GB |
| `fr_FR` | 3.87 GB |
| `hi_Deva_IN` | 4.14 GB |
| `hi_Latn_IN` | 2.7 GB |
| `ja_JP` | 1.69 GB |
| `ko_KR` | 2.66 GB |
| `pt_BR` | 2.33 GB |

Use `data-designer agent state persona-datasets` to check which locale files are present. Persona install status is per-locale, not global.

## Delete/reset caution

- `data-designer config reset` only targets `model_providers.yaml` and `model_configs.yaml`, with confirmation for each file.
- It does not delete MCP configs, tool configs, plugin catalog aliases, plugin cache, managed persona assets, or NGC config.
- Remove plugin catalogs with `data-designer plugin catalog remove ALIAS`.
- Remove managed assets manually only when disk cleanup is intentional.

## Safe isolated inspection

```bash
export DATA_DESIGNER_HOME="$(mktemp -d)"
data-designer --help
data-designer agent context
```

The bundled `scripts/capture_agent_context.py` uses this isolated-home pattern by default.
