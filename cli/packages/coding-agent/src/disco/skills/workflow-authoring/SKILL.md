---
name: workflow-authoring
description: "Writes deterministic DisCo workflow scripts that coordinate subagents with stable coverage IDs, bounded recovery, explicit usage semantics, and structured environment handoffs."
metadata:
  disco-role: shared
  upstream: "@quintinshaw/pi-dynamic-workflows@3.10.0"
disable-model-invocation: false
---

# Workflow Authoring

Use the `workflow` tool only for genuinely decomposable work. The script is an
orchestration program, not a container for the task's entire natural-language
brief.

When another skill requires workflow orchestration, read this file completely
before the first `workflow` call. Do not infer `agent()` option fields from a
producer's private report schema.

## Script and args boundary

- Keep `script` short: metadata, phases, job mapping, `agent()`/`parallel()` calls,
  coverage accounting, and the final return value.
- Put long or Markdown-rich prompts in `args.jobs` or `args.briefs`. This keeps
  Markdown backticks, code spans, quotes, and multiline content out of JavaScript
  template literals and prevents avoidable parser failures.
- Do not put an unescaped Markdown backtick inside a script template literal. If a
  parser error does occur, use its source line and caret, then move that payload to
  `args` instead of escaping one occurrence and retaining the fragile structure.
- `parallel()` receives functions, not already-started promises:
  `await parallel(jobs.map((job) => () => agent(job.prompt, options)))`.

## Stable coverage contract

Every job needs one canonical lowercase-hyphen `id`. Pass that same value as
`subSkill` when it represents a generated sub-skill. A coordinated workflow
should return a ledger shaped like:

```js
const rows = await parallel(jobs.map((job) => async () => {
  const result = await agent(job.prompt, {
    label: job.id,
    subSkill: job.id,
    environment: args.environment,
  });
  return { id: job.id, ok: result !== null, result };
}));

const missing = rows
  .filter((row) => !row || row.ok !== true)
  .map((row, index) => row?.id ?? jobs[index].id);

return {
  rows,
  complete: missing.length === 0,
  missing,
  errors: rows
    .filter((row) => row && row.ok !== true)
    .map((row) => ({ id: row.id, error: row.error })),
};
```

`results.length` is only the number of returned positions; it is never the
success count. `null`, a missing row, or an explicit `ok: false` is incomplete
coverage.

## Recovery

For recovery, create a new workflow call with:

- `args.jobs` containing only the current `missing` IDs and their original briefs;
- `recoveryOfRunId` set to the original run ID;
- `recoveryRound` incremented for the new round;
- `maxRecoveryRounds` left at the default 50 unless the user has a reason to
  choose another value.

Within one script, `recoverMissing(jobs, worker, options)` is also available. It
only submits the current pending IDs, never reruns successful IDs, and stops with
an explicit `stoppedReason` after the configured round cap or two consecutive
rounds with no reduction in the missing set. An incomplete result must be shown
to the main agent and resolved before integration; never silently merge the
successful subset as if the batch were complete.

## Timeouts, retries, and usage

- Omit `agentTimeoutMs` unless the user explicitly asks for a hard time bound.
  The runtime default is no hard timeout.
- A timeout attempt is aborted and drained before its default one retry begins.
  Do not design workflows that assume the timed-out agent can keep writing in the
  background.
- Use `tokenBudget` only when the user asks for a spend cap.
- Final usage is terminal usage when available. Live usage is observability only;
  it is not finalized accounting. Estimated fallback usage is labeled as such,
  and `cacheRead` is shown separately.

## Prepared environment handoff

After `prepare-repo-skill-env` succeeds, use the report's canonical
`workflowEnvironment` object. Pass its verified executable and expected
distribution version structurally, for example:

```js
args: {
  environment: {
    executable: preparedEnvironmentExecutable,
    cwd: repositoryPath,
    package: "target-package",
    version: "target-version",
  },
  jobs,
}
```

Every subagent must pass `environment: args.environment` to `agent()`. The
runtime executes the assertion before creating the session. A missing executable
or version mismatch is a hard failure; never replace it with ambient `python`, a
different virtual environment, or an unverified package installation.

The private prepare-env report may also contain legacy evidence fields. Their
only supported migration mapping is:

```text
pythonExecutable       -> executable
expectedDistribution   -> package
expectedVersion        -> version
assertBeforeStartup    -> omitted; assertion is always required
```

Do not author new workflows with those legacy names. The runtime normalizes this
known shape only as a visible deprecation safety net. Canonical and legacy values
that disagree are a hard contract failure before subagent startup; no ambient
runtime is guessed.

## Integration gate

Only integrate generated files after `complete === true`. If the result is
incomplete, preserve the original jobs and IDs, start a recovery workflow for
the current missing set, and report any no-progress or safety-cap stop explicitly.
