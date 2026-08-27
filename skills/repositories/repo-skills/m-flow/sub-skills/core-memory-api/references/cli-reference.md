# `mflow` CLI Reference

The installed console entry point is `mflow = m_flow.cli.app:main`. The CLI is a
thin argparse wrapper around the public Python APIs. Use it for simple local
operations and smoke tests; use Python APIs for complex orchestration, structured
return values, or unsupported commands such as one-step `ingest()`.

## Top-level commands

```bash
mflow --help
mflow --version
mflow --debug <command> ...
mflow -ui
```

`--debug` prints full stack traces on errors. `-ui` starts local UI/API/MCP
processes and is owned by `../../service-integrations/SKILL.md`, not this sub-skill.

Registered subcommands: `add`, `search`, `memorize`, `delete`, `config`.

## `mflow add`

```bash
mflow add DATA [DATA ...] [--dataset-name NAME]
mflow add "M-flow builds persistent memory." --dataset-name notes
mflow add notes.md https://example.invalid/page -d docs
```

Flags:

| Flag | Meaning |
| --- | --- |
| positional `DATA...` | One or more text strings, file paths, URLs, file URLs, or S3 URIs. |
| `--dataset-name`, `-d` | Target dataset name. Default: `main_dataset`. |

Behavior: normalizes one item to a string and multiple items to a list, then
calls `await m_flow.add(data=..., dataset_name=...)`. After adding, run
`mflow memorize` before expecting search/query results.

## `mflow memorize`

```bash
mflow memorize [--datasets NAME [NAME ...]] [--chunk-size N]
mflow memorize -d notes docs --content-type text
mflow memorize --datasets chat_logs --content-type dialog --background --verbose
```

Flags:

| Flag | Meaning |
| --- | --- |
| `--datasets`, `-d` | Dataset names to process. Omit to process all available data for the user. |
| `--chunk-size` | Maximum tokens per chunk; omitted means model/config-derived default. |
| `--chunker` | One of `TextChunker`, `LangchainChunker`, `CsvChunker`; default `TextChunker`. |
| `--background`, `-b` | Start processing and return immediately. Query only after completion. |
| `--verbose`, `-v` | Print extra progress notes and result detail. |
| `--content-type`, `-t` | `text` or `dialog`; default `text`. |

The command calls `m_flow.memorize(...)` with the selected chunker class and
`ContentType.TEXT` or `ContentType.DIALOG`. For advanced chunking, content
routing, procedural toggles, or custom pipeline tasks, route to
`../../ingestion-pipelines/SKILL.md`.

## `mflow search`

```bash
mflow search QUERY [--query-type MODE] [--datasets NAME [NAME ...]] [--top-k N]
mflow search "How does M-flow work?" --query-type EPISODIC -d notes
mflow search "Summarize decisions" -t TRIPLET_COMPLETION -k 5 --output-format json
```

Flags:

| Flag | Meaning |
| --- | --- |
| positional `QUERY` | Natural language query or, for Cypher mode, a graph query. |
| `--query-type`, `-t` | One of `TRIPLET_COMPLETION`, `CYPHER`, `EPISODIC`, `PROCEDURAL`, `CHUNKS_LEXICAL`; default `TRIPLET_COMPLETION`. |
| `--datasets`, `-d` | Restrict to one or more dataset names. |
| `--top-k`, `-k` | Maximum result count. Default: `10`. |
| `--system-prompt` | Prompt file path for LLM answer modes. Default behavior uses `direct_answer.txt`. |
| `--output-format`, `-f` | `pretty`, `json`, or `simple`; default `pretty`. |

Triplet completion produces natural-language answers with LLM reasoning over
retrieved graph context and needs LLM credentials. If the user only needs
retrieved context, prefer `--query-type EPISODIC` or the Python `query(...,
mode="episodic")` helper. For scoring/tuning details, route to
`../../retrieval-graph-search/SKILL.md`.

## `mflow delete`

```bash
mflow delete --dataset-name notes
mflow delete --user-id USER_ID
mflow delete --all --force
```

Flags:

| Flag | Meaning |
| --- | --- |
| `--dataset-name`, `-d` | Delete a specific dataset. |
| `--user-id`, `-u` | Delete all data for a user. |
| `--all` | Purge the whole knowledge base. Takes precedence when combined with other targets. |
| `--force`, `-f` | Skip preview and confirmation prompts. |

This command is destructive. Without `--force`, it previews counts and prompts
for confirmation. Do not use `--all` unless the user explicitly asks to purge
everything. If `mflow delete` fails with an attribute error mentioning
`m_flow.remove`, do not assume deletion occurred; the current public Python API
exports `delete`, `datasets.delete_dataset`, and `prune`, while the CLI delete
implementation may expect a legacy `remove` alias. Prefer the Python API for
precise, version-safe deletion in automation.

## `mflow config`

```bash
mflow config list
mflow config get [KEY]
mflow config set KEY VALUE
mflow config unset KEY [--force]
mflow config reset [--force]
```

Available registry keys used by `list`/`unset`:

- `llm_provider`, `llm_model`, `llm_api_key`, `llm_endpoint`
- `graph_database_provider`
- `vector_db_provider`, `vector_db_url`, `vector_db_key`
- `chunk_size`, `chunk_overlap`

`set` parses JSON first and falls back to a string value. The CLI's `get` and
`set` paths may require legacy `m_flow.config.get`, `get_all`, or `set` methods
that are not present on the current static config facade. If these commands warn
that a method is unavailable or fail with `AttributeError`, use Python instead:

```python
import m_flow
print(m_flow.config.show("llm"))
m_flow.config.set_llm_api_key("...")
m_flow.config.set_llm_model("gpt-4o-mini")
m_flow.config.clear_caches()
```

## CLI validation checklist

Use these non-destructive parser checks when validating an installation:

```bash
mflow --help
mflow --version
mflow add --help
mflow memorize --help
mflow search --help
mflow delete --help
mflow config --help
mflow config list
```

Live workflow checks write data and may require credentials:

```bash
mflow add "M-flow smoke note" -d cli_smoke
mflow memorize -d cli_smoke --content-type text
mflow search "What is the smoke note?" -d cli_smoke -t EPISODIC
```

For repeatable, guarded Python validation, prefer
`../scripts/core_workflow_smoke.py` from this sub-skill.
