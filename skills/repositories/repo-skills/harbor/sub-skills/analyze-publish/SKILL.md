---
name: analyze-publish
description: "Inspect, compare, regrade, export, share, upload, and publish
  Harbor results, trajectories, artifacts, Hub records, and versioned task or
  dataset packages with mutation and credential gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Analyze and publish Harbor outcomes

Use this skill when a Harbor run already exists and the task is to inspect its
results, understand trajectories or artifacts, compare runs, regrade a recorded
execution, browse the local viewer or Hub, export traces, upload/share job
results, or publish and version task/dataset packages. Keep the source record
immutable unless a command below explicitly creates a derived result or asks for
confirmation.

## Route by intent

- **Inspect result files, rewards, retries, artifacts, ATIF, or native sessions:**
  read [results-and-trajectories.md](references/results-and-trajectories.md).
- **Run a rubric analysis or quality check, browse locally, query Hub records, or
  compare jobs:** read [analysis-viewer-hub.md](references/analysis-viewer-hub.md).
- **Download, share, upload, publish, inspect package versions, or move a tag:**
  read [publish-upload-versioning.md](references/publish-upload-versioning.md).
- **Summarize benchmark parity records:** read
  [parity-reporting.md](references/parity-reporting.md).
- **Diagnose malformed outputs, missing artifacts, auth, viewer, or version
  failures:** start with [troubleshooting.md](references/troubleshooting.md).

Route task/schema/verifier authoring to `author-benchmarks`, job/provider/agent
execution failures to `run-evaluate`, and custom framework or plugin code to
`integrations`. Do not relaunch an evaluation merely to inspect a recorded run.

## Safety and mutation gates

1. Identify whether the input is a local trial directory, local job directory,
   Hub job/trial UUID, task package, or dataset package before selecting a
   command. Check `harbor --version` when command behavior may be version-sensitive.
2. Prefer local parsing, `--json`, `harbor hub ... show/list/tasks/trials/shares`,
   `harbor version list/show`, and `harbor view` for read-only inspection.
3. Treat `harbor analyze` and `harbor check` as **source-preserving but not
   cost-free**: they create derived Harbor jobs, may run an evaluator agent and
   environment, and write reports. Show rubric, agent/model, environment,
   attempts, filters, and output directory before running them.
4. Never run `harbor upload`, Hub copy/share/retry/cancel/delete, visibility or
   access changes, `harbor publish`, or `harbor version tag` without explicit
   approval for the exact target, credentials, visibility, recipients, and
   mutation. `harbor traces export` is local by default; `--push` or OTLP
   endpoint upload is an external mutation and needs the same gate.
5. Keep credentials in the CLI's auth flow or environment. Do not print tokens,
   copy private result contents into prompts, or infer that a local login grants
   access to another organization.

## Safe operating sequence

1. Inventory the local tree (`config.json`, `lock.json`, `result.json`,
   `job.log`/`trial.log`, `artifacts/manifest.json`, `agent/trajectory.json`,
   native session files, retry folders) and preserve a digest or copy when an
   audit needs reproducibility.
2. Read result and manifest JSON before opening large logs. Separate the recorded
   agent/model/configuration from verifier rewards, exceptions, costs, retries,
   and post-hoc analysis. A retry is a new attempt; a regrade is a new derived
   trial that does not rerun the agent.
3. Use the narrowest read-only command or local parser. For a Hub record, inspect
   with `harbor hub job show`, `tasks`, `trials`, `shares`, `compare`, or `hub
   trial show`; use `--json` for machine processing and `--include-retries` when
   retry history changes the conclusion.
4. For a regrade, verify the source has readable `result.json`, a trustworthy
   artifact manifest and bytes, and that the replacement verifier is
   single-step and separate-mode. Use `harbor job regrade` or `harbor trial
   regrade`; record the new output path and compare the printed reward delta.
5. For any external operation, preview the exact command and expected side
   effects, obtain confirmation, check authentication, then verify the returned
   ID, visibility, revision, digest, or URL. Record partial failures and retry
   only the failed/idempotent portion.

## What this skill does not claim

Help/parser checks and mocked/unit evidence validate command contracts only.
Docker, cloud providers, model APIs, Hub/registry credentials, Hugging Face,
OTLP endpoints, GPU, and frontend build toolchains are optional capabilities and
must remain explicitly unverified unless actually exercised with approval.
