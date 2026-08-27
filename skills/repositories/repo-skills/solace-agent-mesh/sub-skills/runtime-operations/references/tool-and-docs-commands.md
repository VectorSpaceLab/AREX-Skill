# Runtime docs and built-in tool discovery commands

This reference covers `sam docs` and `sam tools`. These commands help inspect installed SAM capabilities without starting a broker-backed application, though `sam docs` starts a local documentation web server.

## `sam docs`

`sam docs [OPTIONS]` serves bundled documentation through a local HTTP server and opens a browser tab.

| Option | Meaning |
| --- | --- |
| `-p, --port INTEGER` | Port for the docs server. Default is 8585. |
| `-h, --help` | Parser/help only; no server start. |

Operational details:

- The served URL uses the `/solace-agent-mesh/` prefix and points to the getting-started introduction page.
- Requests with that prefix are rewritten before static-file serving.
- A 404 redirects to the introduction page.
- The command looks for packaged docs first and development-built docs second. If neither exists, it exits with "Documentation directory not found."
- Starting the command opens a browser and blocks until interrupted.

Examples:

```sh
# Help only
sam docs --help

# Serve on the default port
sam docs

# Serve on a custom port when 8585 is busy
sam docs --port 9000
```

Troubleshooting:

- Port already in use: choose another `--port`.
- Browser does not open: copy the printed URL into a browser manually.
- Documentation directory missing: use an installed distribution that includes docs or rebuild/package docs in a development checkout.

## `sam tools list`

`sam tools list [OPTIONS]` inspects registered built-in tools. It is useful before authoring or reviewing agent configs. Do not treat tool availability as proof that external services for a tool are configured.

| Option | Meaning |
| --- | --- |
| `-c, --category TEXT` | Filter by category. Invalid categories report valid categories from the installed registry. |
| `-d, --detailed` | Include parameters and required scopes. |
| `--json` | Emit JSON for scripts, inventory, or diffing. |
| `-h, --help` | Parser/help only. |

Examples:

```sh
# Human-readable inventory
sam tools list

# JSON inventory suitable for scripts
sam tools list --json

# Detailed artifact-management tool schemas
sam tools list --category artifact_management --detailed

# Combine filter and JSON for config review
sam tools list -c web --json
```

The installed registry determines the authoritative list. Common documented groups include:

| Group | Typical use | Representative tools |
| --- | --- | --- |
| `artifact_management` | Create, list, load, resolve, extract, or modify file artifacts. | `append_to_artifact`, `list_artifacts`, `load_artifact`, `apply_embed_and_create_artifact`, `extract_content_from_artifact` |
| `data_analysis` | Query, transform, and visualize data. | `query_data_with_sql`, `create_sqlite_db`, `transform_data_with_jq`, `create_chart_from_plotly_config` |
| `web_search` | Web search. | `web_search_google` |
| `research` | Deeper research workflows. | `deep_research` |
| `web` | HTTP/web interactions. | `web_request` |
| `audio` | Speech generation/transcription and related audio utilities. | `text_to_speech`, `multi_speaker_text_to_speech`, `transcribe_audio` |
| `image` | Image generation, description, editing, and related multimodal helpers. | `create_image_from_description`, `describe_image`, `edit_image_with_gemini` |
| `general` | General conversion and diagram helpers. | `convert_file_to_markdown`, `mermaid_diagram_generator` |

## Interpreting tool output for agent configs

Tool usage is configured in an agent `app_config.tools` list. Keep detailed YAML authoring in the workflow/config sub-skills, but these snippets show how runtime inventory maps to config concepts:

```yaml
# Enable a whole documented group
tools:
  - tool_type: builtin-group
    group_name: "artifact_management"
```

```yaml
# Enable a single built-in tool
tools:
  - tool_type: builtin
    tool_name: "web_request"
```

Important runtime caveats:

- Duplicate registrations are de-duplicated by SAM; enabling a group and one tool from that group should not load it twice.
- Some tools require scopes. Use `--detailed` to inspect required scopes and avoid confusing "tool missing" with "tool filtered by auth" in gateway agent cards.
- Some tools require external credentials, network access, model providers, artifact storage, or optional packages. `sam tools list` only proves registration, not successful external execution.
- Agent card discovery through the Web UI gateway filters tools by user scopes; a tool may appear in local `sam tools list` but not in `/api/v1/agentCards` for a restricted user.

## Safe automation patterns

```sh
# Fail fast if no tools are registered or category is invalid
sam tools list --json > sam-tools.json

# Inspect gateway-visible agents/tools without sending a task
python scripts/check_gateway.py --url http://localhost:8000 --json
```

For CI or scripted inventory, prefer JSON output and parse names/categories rather than scraping rich table output.
