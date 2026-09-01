# Dynamic Workflows

DisCo includes a deterministic JavaScript `workflow` tool for work that benefits
from coordinated subagents, bounded concurrency, or multiple execution phases.
Creator and Researcher can both use the runtime, and every workflow subagent
inherits the parent session's mode and skill boundary.

Use ordinary tools for simple sequential work. Use `workflow` when the task has
independent lanes, an explicit coverage set, or a review/recovery loop that is
clearer and safer when represented as one managed run.

This page documents the execution and authoring contracts hardened in DisCo
0.2.0. It is not a complete catalog of every workflow helper or model-routing
feature.

## Running a workflow

A workflow call supplies a raw JavaScript `script` and optional structured
`args`. The script must begin with metadata and must call `agent()` at least
once:

```js
export const meta = {
  name: "inspect_components",
  description: "Inspect independent components in parallel",
  phases: [{ title: "Inspect" }],
};

phase("Inspect");
const rows = await parallel(
  args.jobs.map((job) => () =>
    agent(job.prompt, {
      label: job.id,
      subSkill: job.id,
    }),
  ),
);

return rows;
```

Pass the script as raw JavaScript, without Markdown fences. `parallel()` takes
functions, not promises that have already started.

### Background execution

Workflow calls run in the background by default. The tool returns a run ID, the
current assistant turn ends normally, and the workflow continues without
blocking the user. When the run completes, fails, or returns incomplete
coverage, DisCo delivers a follow-up into the same conversation and starts a
new turn when the agent is idle. If another turn is active, the result waits as
a follow-up rather than interrupting it.

Use `background: false` only when the main agent must consume the result inline
in the same turn. A foreground run blocks until it finishes and returns its
result directly, so DisCo does not deliver it a second time.

Background runs remain available through `/workflows` even if follow-up
delivery cannot be displayed after a reload or other session transition.

## Keep scripts small and briefs structured

Treat the workflow script as orchestration code, not as a container for the
task's full natural-language brief:

- Keep metadata, phases, job mapping, `agent()` calls, coverage accounting, and
  the final return value in `script`.
- Put long or Markdown-rich prompts in `args.jobs` or `args.briefs`.
- Do not embed unescaped Markdown backticks in JavaScript template literals.
- Keep additional custom JSON fields in `args` when the workflow needs them;
  `environment`, `jobs`, and `briefs` are documented common fields, not an
  exclusive schema.

For example:

```js
export const meta = {
  name: "draft_sections",
  description: "Draft a fixed set of sections",
  phases: [{ title: "Draft" }],
};

phase("Draft");
const rows = await parallel(
  args.jobs.map((job) => async () => {
    const result = await agent(job.prompt, {
      label: job.id,
      subSkill: job.id,
      environment: args.environment,
    });
    return { id: job.id, ok: result !== null, result };
  }),
);

const missing = rows
  .filter((row) => !row || row.ok !== true)
  .map((row, index) => row?.id ?? args.jobs[index].id);

return {
  rows,
  complete: missing.length === 0,
  missing,
  errors: rows
    .filter((row) => row && row.ok !== true)
    .map((row) => ({ id: row.id, error: row.error })),
};
```

## Prepared environments

Workflows that depend on a prepared runtime should pass it structurally. A
generic workflow does not need an environment object, but a Creator workflow
that prepared and verified a package environment must reuse that exact
environment instead of falling back to an ambient executable.

Use the canonical shape:

```js
args: {
  environment: {
    executable: "/absolute/path/to/python",
    cwd: "/path/to/repository",
    package: "distribution-name",
    version: "exact-version",
  },
  jobs,
}
```

Every dependent lane then passes the object to `agent()`:

```js
await agent(job.prompt, {
  label: job.id,
  subSkill: job.id,
  environment: args.environment,
});
```

Before creating the subagent session, DisCo executes the absolute
`environment.executable` without a shell and verifies the requested package or
runtime version. A missing executable, a relative executable path, an execution
failure, or a version mismatch is a non-recoverable environment assertion
failure. DisCo does not substitute `python` from `PATH`, another virtual
environment, or an unverified installation.

The runtime recognizes only these legacy prepare-environment mappings as a
deprecated migration safety net:

```text
pythonExecutable       -> executable
expectedDistribution   -> package
expectedVersion        -> version
assertBeforeStartup    -> omitted; assertion is always required
```

New workflows must use the canonical names. A recognized legacy handoff emits a
visible warning. Conflicting canonical and legacy values fail before subagent
startup.

## Coverage and recovery

Give each planned job one stable ID and preserve it through drafting, status,
persistence, and recovery. When the job represents a generated sub-skill, pass
the same ID as `subSkill`.

A coordinated workflow should return an explicit coverage ledger:

```js
return {
  rows,
  complete: missing.length === 0,
  missing,
  errors,
};
```

`results.length` is not a success count. A missing row, `null`, or an explicit
`ok: false` means that coverage is incomplete.

When a managed run returns `complete: false`, DisCo persists it as a recoverable
`WORKFLOW_INCOMPLETE` failure, displays `recovery required`, and includes the
missing IDs in the background follow-up. Do not silently integrate the
successful subset as though the whole batch completed.

Start a recovery workflow with only the current missing jobs, preserving their
original IDs and briefs:

```text
args.jobs          = current missing jobs only
recoveryOfRunId    = original run ID
recoveryRound      = previous round + 1
```

The recovery run should reuse the prepared environment and continue asserting
it for every dependent lane. Successfully completed IDs must not be rerun.

For recovery managed inside one script, `recoverMissing(jobs, worker, options)`
submits only the pending IDs on each round. The default safety cap is 50 rounds,
the hard runtime cap is 1,000 rounds, and the helper stops early with
`stoppedReason: "no-progress"` after two consecutive rounds that do not reduce
the missing set. If the cap is reached first, it returns
`stoppedReason: "max-rounds"`. Both cases remain explicit incomplete results.

## Timeouts and retries

By default, workflow agents have no hard timeout. Set `agentTimeoutMs` only when
the run needs a time bound.

When a timeout is active and no run or configured default overrides retry
behavior, DisCo retries a recoverable timeout once. Set `agentRetries: 0`
explicitly to disable retries. The runtime clamps retries to a maximum of three.

Before retrying, DisCo aborts the timed-out attempt and waits for its session to
finish tearing down. The next attempt does not overlap the previous one, so two
attempts cannot continue writing the same output concurrently.

A non-recoverable environment or runtime failure is fatal to the run. DisCo
aborts and drains active sibling lanes before reporting the parent failure,
rather than leaving them running after the workflow has stopped.

## Usage and persistence

DisCo separates live observability from finalized accounting:

- Live usage snapshots update progress displays but are not final totals.
- Terminal provider usage is used for finalized accounting when available.
- If terminal usage is unavailable, DisCo uses an explicitly marked estimated
  fallback.
- Cache reads and cache writes are tracked separately.
- Each attempt keeps its own usage and error record; run totals include work
  spent by retries that actually executed.

Workflow state is stored under `~/.disco/workflows` in a project-keyed run
store. Persisted state includes the run limits, stable agent IDs, attempt
records, coverage, recovery lineage, journaled results, and usage needed by the
navigator and resume path. Resuming a run restores its original execution
limits instead of silently adopting unrelated defaults from a later session.

## Run controls

Open the interactive navigator with:

```text
/workflows
```

The corresponding text commands are:

```text
/workflows list
/workflows status <runId>
/workflows watch <runId>
/workflows stop <runId>
/workflows pause <runId>
/workflows resume <runId>
/workflows rm <runId>
/workflows save <name> [runId]
```

`status` and `watch` stream progress for an active run and show the persisted
snapshot for a finished run. `pause` preserves resumable state, `stop` aborts a
running workflow, `rm` removes a run record, and `save` registers a reusable
workflow script from a recorded run.

The navigator and status output show incomplete coverage, missing IDs,
recovery lineage, per-agent attempts, root errors, and finalized or estimated
token usage when available.

## Troubleshooting

### The script fails to parse

DisCo reports the source line, column, excerpt, and caret. If the failing line
contains Markdown backticks, move the prompt payload into `args.jobs` or
`args.briefs` instead of repeatedly escaping a large template literal.

### The prepared environment fails before the agent starts

Check that `environment.executable` is an absolute path and that
`environment.package` and `environment.version` match the prepared
installation. Do not replace the failed assertion with ambient Python. If an
old prepare-environment report was passed directly, migrate its known fields to
the canonical names shown above.

### A run says recovery is required

Read the persisted `missing` and `errors` fields with `/workflows status
<runId>`. Start the next workflow with only those missing IDs, preserve the
original briefs, and set the recovery lineage fields. Integrate results only
after the final ledger reports `complete: true`.

### Recovery stops without completing

`no-progress` means repeated rounds did not shrink the missing set;
`max-rounds` means the configured safety cap was reached. Report the remaining
IDs and blocker instead of treating the partial batch as complete.

### A background result does not appear immediately

The run may still be active, its follow-up may be queued behind another turn,
or the session may have reloaded. Inspect it with `/workflows status <runId>`;
the persisted result remains available even when automatic delivery cannot be
shown.

## Maintainer references

- [Workflow authoring skill](../packages/coding-agent/src/disco/skills/workflow-authoring/SKILL.md)
- [Inline adaptation provenance](../packages/coding-agent/src/disco/dynamic-workflows/UPSTREAM_SOURCE.md)
- [Workflow regression tests](../packages/coding-agent/src/disco/dynamic-workflows/workflow.test.ts)

