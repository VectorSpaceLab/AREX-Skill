---
name: auto-deep-researcher-24x7
description: "Operate the Deep Researcher Agent repository for autonomous deep-learning experiments, execution backends, provider/tool dispatch, GPU resources, durable progress, and research-support integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deep Researcher Agent

Use this repo skill when a Researcher needs to operate or troubleshoot the
Deep Researcher Agent: a Python application that runs a human-directed
THINK→EXECUTE→REFLECT loop around GPU experiments, monitors training without
LLM calls, and preserves experiment context across cycles.

This is an operating graph, not a replacement for the source checkout. It is
self-contained and routes by task. Read [configuration](references/configuration.md)
when selecting providers, execution modes, memory features, or export settings.
Read [troubleshooting](references/troubleshooting.md) before retrying an
installation, launch, or reporting failure. Check
[repository provenance](references/repo-provenance.md) before using this skill
against a changed checkout or deciding whether it needs refresh.

## First route

1. Confirm the target experiment project, its human-owned `PROJECT_BRIEF.md`,
   intended execution mode, GPU/scheduler resources, and whether the request is
   a dry-run, a bounded launch, monitoring, recovery, or reporting task.
2. Keep the brief and stable research direction human-owned. Never put API keys,
   private tokens, or destructive commands in the brief or generated reports.
3. Run the relevant read-only validator before side effects:
   - project lifecycle: `sub-skills/autonomous-experiments/scripts/check_project.py`
   - backend YAML/path: `sub-skills/execution-and-monitoring/scripts/check_backend_config.py`
   - provider metadata: `sub-skills/agent-tools-and-providers/scripts/validate_provider_config.py`
   - local GPU status: `sub-skills/gpu-and-resource-operations/scripts/gpu_status.py`
4. Use a finite first run, require the worker dry-run, and preserve the
   structured PID/job-id and log-file handoff. Do not infer success from prose.
5. Do not import this skill or modify a live skill router in this task. The
   graph was generated with the explicit `not import` boundary.

## Route map

- **Project launch, cycle steering, dry-run, state transitions, and stop/recover**
  → [autonomous-experiments](sub-skills/autonomous-experiments/SKILL.md).
- **Local, SSH, or Slurm transport, command/path safety, liveness, logs, and
  truthful terminal outcomes** → [execution-and-monitoring](sub-skills/execution-and-monitoring/SKILL.md).
- **Provider aliases/endpoints, leader-worker dispatch, text tool protocol,
  repository reading, literature calls, and protected writes** →
  [agent-tools-and-providers](sub-skills/agent-tools-and-providers/SKILL.md).
- **Memory files, ledger/journals, stagnation/gates, safety signals, status,
  reports, and Obsidian/local export** →
  [memory-safety-and-progress](sub-skills/memory-safety-and-progress/SKILL.md).
- **NVIDIA detection/free-device selection and opt-in GPU keep-alive** →
  [gpu-and-resource-operations](sub-skills/gpu-and-resource-operations/SKILL.md).
- **Claude/Codex source integrations, installation ownership, papers,
  conference search, reports, and no-import boundaries** →
  [skills-and-installation](sub-skills/skills-and-installation/SKILL.md).

## Prerequisites and minimal checks

The application documents Python 3.10+, `PyYAML`, and at least one provider
package (`anthropic` and/or `openai`). From the repository's application
environment, install the documented runtime set with:

```bash
python -m pip install -r requirements.txt
```

GPU training additionally needs a working NVIDIA driver, a compatible
CUDA-enabled training environment, and a user project. SSH needs a reachable
configured host; Slurm additionally needs `sbatch`, `sacct`, and `squeue` on the
submit host. Public literature routes need network access; provider routes need
the relevant API key environment or logged-in CLI subscription.

For a read-only installation/import probe, run
`scripts/check_environment.py --repo-root <checkout> --cuda` from a context where
the application modules are available. It reports imports, non-secret provider
metadata, and an optional CUDA probe without training or network calls. For the
application's own check, run `python -m core.loop --project <project> --check`.
Neither check proves a provider credential, GPU training command, remote host,
scheduler, or source-skill installation works.

## Cross-cutting safety boundaries

- Workspace paths are relative and symlink-safe; do not weaken traversal checks.
- `run_shell` is not a full sandbox. Avoid explicit shell interpreters and never
  use it for long training; use the launch path after a mandatory dry-run.
- Monitoring is deliberately zero-LLM-cost. Do not add polling-time model calls.
- Local/SSH terminal success can be indeterminate after a PID exits; Slurm's
  observed `COMPLETED` is the only scheduler success state.
- Missing metrics, malformed history, missing logs, unavailable hardware, and
  missing credentials are explicit unknowns or blockers, not evidence of success.
- Install/uninstall, vault writes, external API calls, GPU keeper activity, and
  live training are user-visible side effects requiring a separate decision.

## Refresh trigger

Run `refresh-repo-skill` when the source commit, dirty paths, public entry
points, configuration fields, agent prompts, or source integration layout no
longer match the provenance snapshot. The canonical router scenario is
`agent-frameworks-tooling-and-sandboxed-llm-workflows`.
