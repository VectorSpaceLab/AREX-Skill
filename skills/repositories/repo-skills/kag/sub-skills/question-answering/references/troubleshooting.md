# Question Answering Troubleshooting

## Purpose

Use this when query-time answers, traces, or pipeline selection do not look right.

## Failure surfaces

### The answer is `UNKNOWN`

**Symptoms**

- the solver returns `UNKNOWN`
- the trace exists but the final answer is empty or clearly incomplete

**Likely causes**

- the project was not fully built or committed before the query
- the active pipeline is not the one you intended
- the retriever config does not match the project's index layout
- a provider-backed LLM or vectorizer is unavailable

**Recovery**

1. Confirm the build/index state in `knowledge-construction`.
2. Inspect the solver config with `scripts/inspect_solver_config.py`.
3. Check whether the query should use `index_pipeline`, `kag_static_pipeline`, or `mcp_pipeline` instead.

### No references or trace evidence

**Symptoms**

- the answer looks plausible but has no supporting references
- the trace does not show the steps you expected

**Likely causes**

- the pipeline is using a generation-only path
- the retriever list is empty
- the current query path skips evidence collection

**Recovery**

1. Check the pipeline name and `chat.index_list` settings.
2. Prefer an evidence-backed pipeline when citation quality matters.
3. Re-run only after the retriever config matches the built project.

### The wrong pipeline is active

**Symptoms**

- the query uses a different route than the config suggests
- iterative or self-cognition behavior appears unexpectedly

**Likely causes**

- `chat.ename` or a similar selector points at a different pipeline
- the config file discovered by the package is not the file you edited
- a fallback path took over because the primary config was missing a key

**Recovery**

1. Run `scripts/inspect_solver_config.py` and confirm the discovered config file.
2. Check the selector key that chooses the active pipeline.
3. Fix the config before re-running the query.

### `knext reasoner execute` misuse

**Symptoms**

- the CLI exits with a usage error
- the file/string query never reaches the server

**Likely causes**

- both `--dsl` and `--file` were supplied
- neither `--dsl` nor `--file` was supplied
- the project or host metadata does not match the active environment

**Recovery**

1. Choose exactly one of `--dsl` or `--file`.
2. Confirm the project is restored and reachable.
3. Re-run the command after fixing the selector.

### `knext thinker execute` returns nothing useful

**Symptoms**

- the thinker call succeeds but does not produce the expected reasoning output

**Likely causes**

- the subject/predicate/object fields are incomplete
- the reasoning mode does not match the task shape

**Recovery**

1. Check the thinker inputs.
2. Use the subject/predicate/object form that matches the reasoning goal.
3. Fall back to a reasoner query if the thinker route is not the right fit.

### Project or host mismatch

**Symptoms**

- the query goes to the wrong project
- the host address points at an old server or a different environment

**Likely causes**

- the local config was restored from another project
- the environment variables override the expected host or project id

**Recovery**

1. Inspect the active config summary.
2. Confirm the project id and host address.
3. Restore or update the project before retrying.
