---
name: tooling-and-deployment
description: "Use tooling-and-deployment for Isaac Lab installation, docs,
  tests, packaging metadata, changelog fragments, scaffolding, and
  deployment-maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tooling and Deployment

Use this sub-skill when the task is about maintaining the Isaac Lab repository itself rather than using one of the simulation or task workflows.

## Route here for

- Installation and packaging questions.
- Docs builds, formatting hooks, and test execution.
- Changelog fragments and release-note hygiene.
- Repository maintenance helpers and scaffolding commands.
- Deployment and CI-adjacent helpers when they are part of repo maintenance rather than end-user training.

## Use other subskills for

- Simulation launch and backend choice: `../simulation-core/SKILL.md`.
- Task discovery and preset selectors: `../tasks-and-presets/SKILL.md`.
- RL train/play wrappers: `../rl-training/SKILL.md`.
- Teleoperation, Mimic, and augmentation: `../imitation-and-teleop/SKILL.md`.

## Working references

- `references/maintenance-workflows.md` covers docs, tests, packaging, and scaffold commands.
- `references/package-and-release-notes.md` covers package metadata, extras, and changelog-fragment rules.
- `references/deployment-notes.md` covers deployment helpers and explicit exclusions.
- `references/troubleshooting.md` covers build, docs, and maintenance failures.
- `scripts/inspect_repo_maintenance.py` prints a safe maintainer checklist and the current repo version metadata.

## Acceptance checks

- Distinguish user-facing maintenance from implementation-only internals.
- Name the correct repo wrapper or maintenance command for the requested action.
- Avoid promising destructive or cloud-automation workflows as if they were safe defaults.
- Cite the maintenance file or command family the user should inspect or run next.
