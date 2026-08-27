---
name: state-recovery-and-experiment-ops
description: "Use ARIS Research Wiki, project state files, session recovery,
  watchdog monitoring, experiment queues, and remote/GPU operating guidance
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# State Recovery and Experiment Operations

Use this sub-skill when an ARIS workflow must persist research knowledge, resume after compaction or a crashed session, initialize or query `research-wiki/`, monitor long-running tasks, register screen/tmux jobs, or plan local/remote/GPU experiment operations.

## Route Here

- Initialize and maintain Research Wiki papers, ideas, experiments, claims, graph edges, log, and query pack.
- Resolve ARIS helpers from `.aris/tools`, local tools, manifest, or pointer files.
- Build recovery checkpoints from pipeline status and canonical artifacts.
- Register and monitor watchdog tasks for training and downloads.
- Hand off experiments to local/remote/Vast/Modal/GPU environments without claiming unverified hardware.
- Diagnose state drift, missing helper scripts, stale task status, and interrupted review loops.

## Reroute

- Installer/manifests and host skill roots: `../install-and-distribution/SKILL.md`.
- Workflow/artifact selection: `../workflow-routing-and-skill-catalog/SKILL.md`.
- Reviewer traces, MCP state, provider credentials: `../review-and-provider-backends/SKILL.md`.
- Changes to helper scripts or watchdog/wiki tests: `../repository-maintenance/SKILL.md`.

## Recovery Pattern

1. Find the project root (prefer the Git root when available).
2. Read pipeline status, research contract, fixed-name handoffs, `REVIEW_STATE.json`, and recent trace directories.
3. Check active training/download sessions and watchdog status before restarting anything.
4. Reconstruct the next stage from files; never rely on memory after compaction.
5. Write an explicit checkpoint before another long tool call.

## Reference Map

- `references/project-state.md` explains the project file contracts, priority order, and recovery sequence.
- `references/watchdog-and-wiki.md` explains Research Wiki commands, task JSON, status semantics, and helper lookup.
- `references/troubleshooting.md` covers stale state, missing helpers, dead sessions, and remote/GPU uncertainty.
- Root `../../references/helper-resolution-and-project-files.md` gives the shared resolver and artifact map.

## Safety

- Do not start or kill remote jobs without user intent.
- Do not treat a missing GPU probe as a successful GPU run.
- Preserve append-only logs and versioned artifacts.
- Keep API credentials and private server paths out of persistent research artifacts.
