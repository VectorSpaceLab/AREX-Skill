# LangGraph Configuration Reference

`langgraph.json` declares dependencies, graph exports, environment settings, and Docker/server options for the LangGraph CLI.

## Core Python Config

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "python_version": "3.12",
  "dependencies": ["langchain_openai", "."],
  "graphs": {
    "agent": "./agent.py:graph"
  },
  "env": ".env"
}
```

Rules:

- `graphs` must be present and non-empty.
- Dependency-based Python configs require `dependencies` unless `source.kind` is `uv`.
- `dependencies` entries can be package names or local relative paths such as `.` and `./my_package`.
- `python_version` uses `major.minor`; patch versions are invalid.
- The schema enum includes `3.11`, `3.12`, and `3.13`; CLI validation enforces a minimum of `3.11`.
- If Python graphs are present and `python_version` is omitted, validation defaults it to `3.11`.

## Graph Specifications

Graph entries map graph IDs to either strings or objects with `path` and optional `description`.

String form:

```json
{
  "graphs": {
    "agent": "./agent.py:graph"
  }
}
```

Object form:

```json
{
  "graphs": {
    "agent": {
      "path": "./agent.py:graph",
      "description": "Customer support agent"
    }
  }
}
```

Validation checklist:

- The graph ID should be stable and URL-safe for clients.
- The path should be relative to the directory containing `langgraph.json`.
- The path and attribute are separated by `:`.
- The file extension determines Python vs Node behavior.
- Python targets should export a compiled LangGraph/Pregel object, an accepted factory, or an accepted context manager.
- If a Python target exports an uncompiled `StateGraph`, compile it in code and point to the compiled variable. See [`../../graph-runtime/SKILL.md`](../../graph-runtime/SKILL.md).

## Python Dependency Fields

Common fields:

```json
{
  "dependencies": [".", "langchain_openai"],
  "pip_config_file": "./pip.conf",
  "pip_installer": "auto",
  "keep_pkg_tools": ["pip", "setuptools"]
}
```

Notes:

- `pip_installer` accepts `auto`, `pip`, or `uv`.
- Invalid `pip_installer` values fail validation.
- `pip_config_file` is copied/used for pip configuration; do not include credentials in public examples.
- `keep_pkg_tools` can be `true` or a list containing only `pip`, `setuptools`, and `wheel`.
- Local dependency paths must exist when Docker generation needs them.

## `source.kind: uv`

Use this for uv-managed Python projects and workspaces:

```json
{
  "python_version": "3.12",
  "source": {
    "kind": "uv",
    "root": ".",
    "package": "agent"
  },
  "graphs": {
    "agent": "./src/agent/graph.py:graph"
  }
}
```

Rules:

- Only `source.kind: "uv"` is supported.
- It is Python-only and requires `python_version`.
- Do not set `dependencies`; uv reads packages from `pyproject.toml` and `uv.lock`.
- `source.root` must be a non-empty string.
- `source.package` must be a non-empty string when provided.
- Top-level legacy `project_root` and `package` are no longer supported; use `source.root` and `source.package`.
- Workspace builds can fail when the target package is ambiguous, ignored by Docker context, or has invalid uv sources; repair workspace metadata rather than adding ad hoc Docker shell commands.

## JS/TS Config Branch

Graph specs ending in `.ts`, `.mts`, `.cts`, `.js`, `.mjs`, or `.cjs` are treated as Node graphs.

```json
{
  "node_version": "20",
  "graphs": {
    "agent": "./src/agent.ts:graph"
  }
}
```

Rules:

- Node version defaults to `20` when Node graphs are detected.
- Minimum Node major version is `20`.
- Node version must be a major version only.
- If `package.json` has `engines`, only `node` is supported there and it must be a major version only.
- Python `langgraph dev` does not support JS/TS graphs in this CLI version.

## Docker and API Server Fields

```json
{
  "base_image": null,
  "api_version": "0.11",
  "image_distro": "debian",
  "dockerfile_lines": ["RUN apt-get update && apt-get install -y git"],
  "store": null,
  "checkpointer": null
}
```

Notes:

- `base_image` pins the API server base image; when omitted, the CLI chooses Python or Node defaults.
- `api_version` accepts major, major.minor, or major.minor.patch style values.
- Compatible API version ranges can use `~=...` or `>~=...`; do not combine compatible ranges with a tagged `base_image`.
- `image_distro` accepts `debian`, `bookworm`, or `wolfi`; `bullseye` is deprecated.
- `dockerfile_lines` are appended to generated Dockerfiles after the base image import; review them for security and reproducibility.
- `store`, `checkpointer`, `encryption`, and persistence-sensitive fields should be coordinated with [`../../persistence/SKILL.md`](../../persistence/SKILL.md).

## Environment and Secrets

`env` can be a file path or a mapping:

```json
{
  "env": ".env"
}
```

```json
{
  "env": {
    "LANGSMITH_TRACING": "true"
  }
}
```

Guidance:

- Prefer file paths for local secrets.
- Do not commit real `.env` files.
- Generated Docker ignore content excludes `.env` and `.env.*` by default.
- Avoid embedding API keys in `langgraph.json` examples.
- For Docker `up`, credentials such as `LANGSMITH_API_KEY` or `LANGGRAPH_CLOUD_LICENSE_KEY` may be required depending on usage.

## Optional App Hooks

Several fields point to Python objects with the same `./file.py:attribute` shape:

- `auth.path`
- `encryption.path`
- `http.app`
- custom checkpointer paths when configured by object fields

Validation catches missing `:` for `auth.path`, `encryption.path`, and `http.app`. Use the bundled checker for file and import checks.

## Unknown Keys and Typos

The CLI tracks recognized top-level keys and emits warnings for unknown ones. Common repairs:

- `graph` -> `graphs`
- `dependency` -> `dependencies`
- `python` -> `python_version`
- `project_root` -> `source.root`
- `package` -> `source.package`

Treat unknown-key warnings as real bugs unless the user is intentionally testing a future CLI field. One exception: repository examples may include `$schema` for editor/schema tooling; current CLI validation can warn about it even though it is harmless metadata.

## Example: Multiple Graphs

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "python_version": "3.12",
  "dependencies": ["langchain_openai", "langchain_anthropic", "."],
  "graphs": {
    "agent": "./agent.py:graph",
    "research": "./research.py:graph"
  },
  "env": ".env"
}
```

Validate with:

```bash
python skills/langgraph/sub-skills/cli-deployment/scripts/validate_langgraph_config.py langgraph.json --check-imports
langgraph validate -c langgraph.json
```
