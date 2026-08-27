# CLI Reference

## Purpose

Read this when you need to remember KAG's top-level commands, flags, and what each command family is for.

## `kag`

The `kag` console command is the package's operational entry point.

| Command | Use it for | Key notes |
| --- | --- | --- |
| `kag interface --list` | List registered interfaces and components | Safe registry smoke check. |
| `kag interface --cls <ClassName>` | Inspect one registered interface family | Shows registered subclasses, docstrings, constructors, required and optional args. |
| `kag builder --git_url ... --commit_id ...` | Submit a distributed builder job to a cluster | Posts a job to OpenSPG-backed infrastructure; use `--validity_check` first. |
| `kag benchmark --job_config <file>` | Run benchmark jobs from a YAML config | Mutates benchmark state and may restore projects, commit schemas, build data, and run eval loops. |
| `kag mcp-server --transport sse|stdio --port <n> --enabled-tools qa-pipeline,kb-retrieve` | Launch the KAG MCP server | `stdio` is usually safer for agents; `all` enables both supported tools. |

### `kag builder`

Important flags from the source command:

- `--git_url` and `--commit_id` are required.
- `--validity_check` checks that `init_script` and `entry_script` exist in the cloned repo before job submission.
- `--entry_script` is executed as `python <entry_script>` inside the cloned source tree.
- `--num_workers`, `--num_gpus`, `--gpu_type`, `--num_cpus`, `--memory`, and `--storage` shape the worker request.
- `--env` accepts comma-separated `key=value` pairs.

### `kag benchmark`

Important flags from the source command:

- `--job_config` points at the benchmark YAML file.
- `--env` injects comma-separated environment variables before the benchmark runs.

## `knext`

The `knext` command is the project, schema, reasoner, and thinker client.

| Command | Use it for | Key notes |
| --- | --- | --- |
| `knext project create --config_path <file>` | Create a new project from a config file | Validates model config and namespace rules before creation. |
| `knext project restore --host_addr <url> --proj_path <dir>` | Recreate a project from a local directory | Writes project metadata back into `kag_config.yaml`. |
| `knext project update --proj_path <dir>` | Sync local project config to the server | Uses the current `kag_config.yaml` and project id. |
| `knext project list --host_addr <url>` | List projects on a server | Safe read-only listing. |
| `knext schema commit` | Commit local schema and derived index schema | Reads `schema/<Namespace>.schema` when present and merges index-derived schema. |
| `knext schema reg_concept_rule --file <dsl>` | Register a concept rule from a DSL file | Requires a project and server connection. |
| `knext reasoner execute --dsl "..."` | Execute a GQL/DSL query string | Use exactly one of `--dsl` or `--file`. |
| `knext reasoner execute --file <dsl-file>` | Execute a DSL file | Optional `--output` writes results to a file. |
| `knext thinker execute --subject ... --predicate ... --object ...` | Execute a thinker reasoning job | Used for SPO-style reasoning tasks. |

## How to choose

- Use `kag` for package-level introspection, distributed builder submission, benchmark launching, and MCP server operations.
- Use `knext` for project/schema lifecycle and reasoner/thinker client calls.
- Use the bundled scripts in `scripts/` when you need a safe check before running the live commands.
