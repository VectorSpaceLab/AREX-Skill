# Package Topology

## When To Read

Read this when deciding which Langflow package, import name, CLI, or sub-skill owns a task.

## Public Distributions and Imports

| Distribution | Import/module | Role | Skill route |
| --- | --- | --- | --- |
| `langflow` | `langflow` | Thin top-level distribution and public CLI entry point for the full Langflow application. | root, `deployment-and-operations`, `backend-runtime` |
| `langflow-base` | `langflow` | Core FastAPI backend, services, graph execution, component framework re-exports, settings, database, auth/authz, starter flows. | `backend-runtime`, `flow-authoring`, `component-development` |
| `lfx` | `lfx` | Lightweight executor CLI/library, component framework implementation, flow run/serve, MCP, extension system, Flow DevOps commands. | `executor-cli`, `component-development`, `flow-authoring` |
| `langflow-sdk` | `langflow_sdk` | Python REST SDK for flow/project CRUD, run/stream, push/pull, normalization, tests. | `sdk-and-api-clients` |
| `lfx-arxiv` | `lfx_arxiv` | Standalone extension bundle for arXiv search components. | `component-development`, `executor-cli` |
| `lfx-docling` | `lfx_docling` | Standalone extension bundle for Docling document components; heavy local conversion stack is optional. | `component-development`, `deployment-and-operations` |
| `lfx-duckduckgo` | `lfx_duckduckgo` | Standalone extension bundle for DuckDuckGo search components. | `component-development` |
| `lfx-ibm` | `lfx_ibm` | Standalone extension bundle for IBM Db2/watsonx components. | `component-development`, `deployment-and-operations` |

## CLI Entry Points

- `langflow`: full application CLI. Commands include `run`, `superuser`, `copy-db`, `migration`, `api-key`, and nested `lfx` commands.
- `langflow-base`: compatibility CLI entry point that launches the same Langflow command surface.
- `lfx`: lightweight executor and Flow DevOps CLI. Commands include `init`, `login`, `create`, `validate`, `requirements`, `upgrade`, `extension`, `run`, `serve`, `status`, `push`, `pull`, and `export`.
- `lfx-mcp`: MCP server that connects to a running Langflow instance; it is not the same as `lfx serve`.

## Important Ownership Rules

- The `Component` class and many schema/io objects are implemented by `lfx` and re-exported by `langflow` for compatibility.
- Built-in components and extension bundles should preserve class names and `name` attributes because saved flows identify components by those values.
- Full Langflow server state uses backend services, database sessions, settings, auth, and migrations; `lfx run`/`lfx serve` use a stateless/no-op database path for lightweight execution.
- The Python SDK calls a running Langflow server; it does not replace local `lfx` execution or backend implementation.
- Frontend code consumes backend component metadata and API shapes; when component names, output handles, or schemas change, check both Python and UI routes.

## Optional Dependencies

Langflow has many provider, vector-store, document, observability, local model, and deployment extras. Install only the extras needed for the workflow at hand:

- Use provider extras such as OpenAI, Anthropic, Google, IBM, or Groq only when a flow/component needs that provider.
- Use database/vector-store extras only when the selected component or deployment actually uses that backend.
- Use Docling local/chunking/image-description extras only when local document conversion or image-description workflows need them.
- Use local model/PyTorch/transformer execution packages only when model execution is part of the task, not for ordinary flow JSON, API, or repository maintenance checks.

## Verification Signals

Good low-risk checks include:

```bash
python -c "import langflow, lfx, langflow_sdk; print('imports ok')"
langflow --help
lfx --help
python -c "from langflow_sdk import Client, AsyncClient; print(Client, AsyncClient)"
```

If `langflow --help` fails on a missing optional route dependency, select an environment or package build that includes the relevant application dependency before debugging the CLI itself.
