# MCP and Automation Troubleshooting

## Purpose

Use this when KAG service launch, cluster submission, or benchmark planning fails or looks risky.

## Failure surfaces

### `mcp` is missing

**Symptoms**

- the MCP server refuses to start
- the helper reports that the `mcp` package is not installed

**Likely causes**

- the environment does not include the MCP dependency from the package requirements

**Recovery**

1. Run `scripts/check_kag_install.py` to confirm the base install.
2. Install the package in the intended environment if `mcp` is absent.
3. Re-run the config check before trying to start the server.

### Unknown MCP tool name

**Symptoms**

- server startup fails with an unknown tool error
- the requested tool is not one of the supported names

**Likely causes**

- `enabled-tools` contains a typo
- the config assumes a tool that the server does not provide

**Recovery**

1. Use only `qa-pipeline`, `kb-retrieve`, or `all`.
2. Run `scripts/check_mcp_config.py` before launch.
3. Do not start the server until the tool list is valid.

### MCP server port conflict

**Symptoms**

- the `sse` server fails to bind
- an old server is already using the target port

**Likely causes**

- the port is already occupied
- the wrong transport was chosen for the workflow

**Recovery**

1. Prefer `stdio` for local agent workflows.
2. Choose a different port for `sse` if you need a networked server.
3. Do not retry blindly without confirming the transport choice.

### Missing `store_path` or bad MCP executor config

**Symptoms**

- the solver-side MCP executor cannot connect
- the script points at a bad local file or URL

**Likely causes**

- the executor config is incomplete
- the target MCP bundle or store file is missing

**Recovery**

1. Run `scripts/check_mcp_config.py`.
2. Confirm `store_path`, `name`, `description`, `llm`, `prompt`, and `env`.
3. Fix the config before starting the server or solver pipeline.

### Cluster submission is unsafe

**Symptoms**

- `kag builder` looks like it will mutate cluster state or launch remote jobs
- the user wants a dry run only

**Likely causes**

- a live builder submission was requested too early
- the validity check was skipped

**Recovery**

1. Use the builder command's `--validity_check` first.
2. Confirm `git_url`, `commit_id`, and `entry_script`.
3. Ask for explicit approval before submitting the live job.

### Benchmark planning would rewrite files

**Symptoms**

- the shell workflow would patch `kag_config.yaml`
- the run would restore a project, commit a schema, and start build/eval steps

**Likely causes**

- the benchmark workflow is being treated as read-only even though it mutates config and state

**Recovery**

1. Use `scripts/plan_benchmark_command.py` first.
2. Read the planned command sequence before touching files or servers.
3. Stop and ask for approval if the user only wants a dry run.

### External API credentials are missing

**Symptoms**

- service examples fail because a provider or external API is unavailable
- the launch plan depends on keys or network access that are not present

**Likely causes**

- the workflow needs credentials or external connectivity

**Recovery**

1. Confirm whether the task can be solved with `stdio` or a dry-run planner.
2. Request the missing credential or network approval.
3. Do not treat the service as verified until the external dependency is available.
