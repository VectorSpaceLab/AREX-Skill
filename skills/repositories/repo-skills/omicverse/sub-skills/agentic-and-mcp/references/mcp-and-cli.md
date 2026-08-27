# MCP and CLI Reference

Return to [`../SKILL.md`](../SKILL.md) for routing and safe-start guidance.

## Console Scripts

OmicVerse publishes three relevant entry points:

| Command | Target | Use |
| --- | --- | --- |
| `omicverse` | `omicverse.cli:main` | Top-level dispatcher for `claw`, `jarvis`, `web`, `gateway`, and `skill-seeker`. |
| `omicverse-mcp` | `omicverse.mcp.server:main` | MCP server over stdio or local `streamable-http`. |
| `ov-skill-seeker` | `omicverse.ov_skill_seeker.cli:main` | Lists, validates, packages, or creates agent skills. |

Safe parser checks:

```bash
omicverse --help
omicverse-mcp --help
ov-skill-seeker --help
python -m omicverse.mcp --help
```

The top-level `omicverse` dispatcher routes:

- `omicverse claw`: gateway mode by default; switches to JARVIS one-shot/daemon mode when `-q`, `--question`, `--daemon`, `--use-daemon`, or `--stop-daemon` is present.
- `omicverse jarvis`: legacy alias for the JARVIS CLI.
- `omicverse gateway`: starts JARVIS gateway daemon mode and adds `--with-web` unless already supplied.
- `omicverse web`: launches the optional OmicClaw/legacy web workspace when the web package is importable.
- `omicverse skill-seeker`: delegates to the skill seeker CLI.

## MCP Server CLI

`omicverse-mcp` and `python -m omicverse.mcp` expose the same MCP server. Important flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--version` | exit-only | Print OmicVerse package version and exit. |
| `--phase` | `P0+P0.5` | Rollout phase(s) to expose: `P0`, `P0+P0.5`, or `P0+P0.5+P2`. |
| `--transport` | `stdio` | MCP transport, either `stdio` or `streamable-http`. |
| `--session-id` | `default` | Logical session identifier for handle isolation. |
| `--persist-dir` | temporary/lazy | Directory used by `ov.persist_adata`; created lazily on first persist. |
| `--max-adata` | `50` | Maximum AnnData handles per session. |
| `--max-artifacts` | `200` | Maximum artifact handles per session. |
| `--host` | `127.0.0.1` | Bind host for `streamable-http`. |
| `--port` | `8765` | Bind port for `streamable-http`. |
| `--http-path` | `/mcp` | Route path for `streamable-http`. |

The parser configures logging to stderr because stdout is reserved for MCP JSON-RPC in stdio mode.

### Safe Manifest Inspection

Use the bundled script to inspect tools without starting a server:

```bash
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --phase P0+P0.5 --limit 20
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --search marker --phase P0+P0.5 --show-schema
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --phase P0+P0.5+P2 --categories
```

Programmatic equivalents:

```python
from omicverse.mcp import build_default_manifest, get_manifest, build_mcp_server

manifest = get_manifest(phase="P0+P0.5")
server = build_mcp_server(phase="P0")
```

`get_manifest(...)` returns read-only manifest dictionaries with internal function references removed. `build_mcp_server(...)` creates a `RegistryMcpServer` object; do not call `run_stdio()` or `run_streamable_http(...)` unless service startup is intended.

## Manifest Fields and Phases

Registry manifest entries are built from OmicVerse `@register_function` metadata after registry hydration. Common fields include:

| Field | Meaning |
| --- | --- |
| `tool_name` | Canonical MCP tool name, usually prefixed with `ov.`. |
| `full_name` | Underlying OmicVerse function or class path. |
| `kind` | `function` or `class`. |
| `execution_class` | `stateless`, `adata`, or `class`. |
| `adapter_type` | Adapter used by the executor. |
| `category` | Registry category such as preprocessing, plotting, single, or utility. |
| `parameter_schema` | JSON-schema-style input contract. |
| `state_contract` | Session/handle assumptions and mutations. |
| `dependency_contract` | Prerequisites, required slots, and produced outputs. |
| `return_contract` | Return payload shape. |
| `availability` | Optional dependency/backend availability signal. |
| `risk_level` | Safety level for tool invocation. |
| `rollout_phase` | `P0`, `P0.5`, `P2`, or deferred/hidden. |
| `status` | Manifest availability status. |

Phase selection is additive when separated by `+`. Use `P0` for the smallest core pipeline surface, `P0+P0.5` for the default core plus analysis/visualization set, and `P0+P0.5+P2` when class tools are intentionally needed.

## Built-In MCP Meta Tools

Meta tools are always available independently of registry phase. The most useful groups are:

| Group | Tools |
| --- | --- |
| Discovery | `ov.list_tools`, `ov.search_tools`, `ov.describe_tool` |
| AnnData inspection | `ov.adata.describe`, `ov.adata.peek`, `ov.adata.find_var`, `ov.adata.value_counts`, `ov.adata.inspect` |
| Session handles | `ov.get_session`, `ov.list_handles`, `ov.persist_adata`, `ov.restore_adata` |
| Observability | `ov.get_metrics`, `ov.list_events`, `ov.get_trace`, `ov.list_traces` |
| Artifacts | `ov.list_artifacts`, `ov.describe_artifact`, `ov.register_artifact`, `ov.delete_artifact`, `ov.cleanup_artifacts`, `ov.export_artifacts_manifest` |

Typical MCP flow:

1. Call `ov.list_tools` or `ov.search_tools` to select a tool.
2. Call `ov.describe_tool` before invoking a scientific tool to inspect schema, prerequisites, availability, and risk.
3. Call an IO/tool that returns an `adata_id`; AnnData objects stay inside the session and never cross the MCP protocol boundary.
4. Use `ov.adata.describe` or `ov.adata.inspect` to validate slots before downstream calls.
5. Use `ov.persist_adata` or `ov.export_artifacts_manifest` only when the user wants durable outputs.

## Session and Persistence Limits

The MCP runtime stores state in a `SessionStore` scoped by `session_id`. Cross-session handle access raises a structured `cross_session_access` error. Default runtime limits are:

| Limit | Default |
| --- | --- |
| AnnData handles | `50` per session |
| Artifact handles | `200` per session |
| Class instances | `50` per session |
| Event ring buffer | `10000` newest events |
| Trace ring buffer | `5000` newest traces |
| Handle TTLs | disabled unless configured in code |

`--max-adata` and `--max-artifacts` override the two most common hard limits from the CLI. Persistence is explicit: call `ov.persist_adata` to write `.h5ad` plus metadata sidecar, and `ov.restore_adata` to load it into a session.

## Skill Seeker CLI

`ov-skill-seeker` discovers package and project skills, with user/project skills overriding package skills when slugs collide. Safe commands:

```bash
ov-skill-seeker --help
ov-skill-seeker --list
ov-skill-seeker --validate
ov-skill-seeker --package SLUG --out-dir output
ov-skill-seeker --package-all --out-dir output
```

Creation commands can crawl or read external sources and should be gated by user intent:

```bash
ov-skill-seeker --create-from-link URL --name "Display Name" --description "Short purpose" --max-pages 30 --target output
ov-skill-seeker --build-config build.json --out-dir output
```

Relevant options:

| Option | Meaning |
| --- | --- |
| `--project-root PATH` | Project root containing `.claude/skills`; defaults to auto-detected root. |
| `--list` | List discovered skills. |
| `--validate` | Check frontmatter and required files. |
| `--package SLUG` | Build a zip for one skill. |
| `--package-all` | Build zips for all skills. |
| `--create-from-link URL` | Create a new skill by same-domain crawling. |
| `--max-pages N` | Bound link-crawl size. |
| `--target skills|output` | Write generated skills to `.claude/skills` or `./output`. |
| `--package-after` | Package a newly created skill immediately. |
| `--build-config PATH` | Use a unified build JSON config. |
| `--out-dir PATH` | Output directory for packaged zips. |

