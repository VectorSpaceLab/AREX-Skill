# Trajectory lifecycle, multi-step sessions, handoff, and regrade

A trajectory is execution evidence and/or session state. Harbor's portable
trajectory format and each agent's native session format have different
lifecycles. Files created in the sandbox are not restored merely by loading a
trajectory; collect them as artifacts when they matter.

## Trial lifecycle and output layout

A normal `Trial.create()` resolves the task and selects `SingleStepTrial` or
`MultiStepTrial`. `trial.run()` performs environment/agent setup, agent
execution, artifact recovery, verification, result persistence, and teardown.
A normal trial directory contains:

```text
<trial-dir>/
  config.json
  lock.json
  result.json
  agent/
  verifier/
  artifacts/
```

Agents may add native session files, ATIF output, terminal recordings, or
provider-specific logs beneath `agent/`. Multi-step trials additionally archive
per-step agent/verifier/artifact directories beneath `steps/<step-name>/`.
Treat `config.json`, `lock.json`, `result.json`, and `artifacts/manifest.json`
as the authoritative local records; do not infer completion from a partial log.

`result.json` records timing, agent identity/model information, verifier
rewards, exceptions, and (for multi-step trials) step results. An execution
failure normally becomes `exception_info` in the result. Cancellation is
recorded and re-raised so the containing job can preserve cancellation state.

## Multi-step execution

A multi-step task has ordered `[[steps]]` entries and one shared environment.
Each step can have its own instruction, setup/workdir, healthcheck, agent and
verifier timeout, network policy, verifier mode, reward gate, and artifact
entries. Files persist in the shared environment across steps. A setup failure,
healthcheck failure, agent/verifier failure without a usable result, or failed
`min_reward` gate can abort the remaining steps.

By default every step starts a fresh agent conversation, while the environment
and filesystem persist:

```text
step 1: fresh
step 2: fresh
step 3: fresh
```

Set `agent.resume_trajectory: true` or pass `--resume-trajectory` to request
native session continuation:

```text
step 1: fresh
step 2: resume
step 3: resume
```

Harbor validates `SUPPORTS_RESUME` before environment spend when more than one
step can resume. An unsupported agent is a preflight error; do not remove the
flag just to make a run start unless changing the experiment is intended.
The simulated-user bridge is not supported for multi-step tasks.

The task's per-step `min_reward` can be a scalar (the `reward` key) or a
mapping of reward keys. A missing key fails its threshold. If a threshold fails,
remaining steps are skipped. The trial-level verifier result defaults to a
per-key mean across steps that produced verifier results (missing keys count as
zero); a task can choose the final step's result instead with its reward
strategy. A step without a verifier result is excluded from the mean
numerator/denominator logic as defined by the installed task model.

Artifacts are collected after each step into `steps/<step-name>/artifacts/`
for non-mounted environments. Task-level, trial-level, and current step
artifacts are merged in that order for each pass. The shared environment is
not a fresh trial between steps, so network/resource and evidence boundaries
must be reasoned about per phase.

## Loading a trajectory

Use `--load-trajectory FILE` to seed the first agent session:

```bash
harbor run -p ./tasks/continuation -a codex -m <model> \
  --load-trajectory ./prior-trial/agent/trajectory.json
```

The extension is a useful guard:

- `.jsonl` is an agent-native session. It is lossless and normally only
  loadable by the same agent; preserve the file name because agents use it to
  locate/validate the session.
- `.json` is an ATIF document. Harbor validates and converts it to the loading
  agent's native session format. It is portable across supported agents but
  drops agent-specific session details and is not lossless.

The run-level path overrides a task-level `trajectory.json` shipped beside the
instruction (or beside the first multi-step step instruction). Task-level
loading is ATIF-only because a task must remain agent-agnostic. Loading and
resume compose for multi-step execution:

```text
without resume: load, fresh, fresh, ...
with resume:    load, resume, resume, ...
```

The loaded conversation is restored, not the old environment filesystem. If
the agent lacks the required native/ATIF loader, the file does not exist, or
an ATIF document is invalid, Harbor should fail before environment spend.
Resolve that support/file problem rather than suppressing verification.

## Handoff to a local agent CLI

`harbor trial handoff TARGET` resumes a finished trial's agent session in the
local agent CLI. `TARGET` is a local trial directory or a Harbor trial UUID;
a UUID is downloaded first. Handoff requires:

- a trial directory with a valid `config.json`;
- an agent with `SUPPORTS_HANDOFF` (the installed support set is
  version-dependent; verify the selected agent); and
- exactly one agent session. Multi-step runs with fresh per-step sessions are
  normally rejected.

Handoff copies/locates the native session in the local CLI's session store and
replaces the Harbor process with the resumed CLI command. It restores the
conversation only. Container files, working-directory changes, and artifacts
remain in the trial directory and are not automatically present in the local
working directory. If the user wants the files, download/copy artifacts
separately and do not claim that handoff reproduces the sandbox.

There is no generic `harbor trial resume` command. Use loading to create a new
trial with prior context, or handoff for an interactive continuation.

## Resuming jobs

`harbor job resume --job-path JOB_DIR` is job-plan recovery, not trajectory
continuation. It reads the persisted job config and lock, recognizes completed
trial configs, optionally removes selected cancelled/error trials, and runs
only remaining trials. It preserves the original experiment identity and
rejects changed config/lock combinations. A trial's native session is not
implicitly resumed by job resume; request trajectory resume/load explicitly if
the trial configuration calls for it.

## Regrade boundary

`harbor trial regrade SOURCE -p TASK` and `harbor job regrade SOURCE -p TASK`
create new output and run a replacement verifier without rerunning the agent.
The source can be a local directory or a Harbor UUID. The source is never
modified. The replacement verifier must resolve to separate mode and the
source must be a completed single-step trial/job with readable result and
artifact manifest. Every declared input (including the implicit
`/logs/artifacts` convention) must have present, trustworthy manifest bytes;
failed/skipped entries are not replayable. Multi-step regrade is unsupported.

Regrade preserves the source agent identity/configuration for provenance but
recomputes rewards in a new verifier environment. It is not a trajectory
analysis command and it is not a way to rerun an agent with a new model.
Route result comparison, trajectory inspection, viewer use, and score
interpretation to `analyze-publish` after choosing the execution operation.
