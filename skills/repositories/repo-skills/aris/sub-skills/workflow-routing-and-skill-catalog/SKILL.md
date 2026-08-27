---
name: workflow-routing-and-skill-catalog
description: "Choose ARIS research workflows, slash skills, skill groups, common
  parameters, and artifact handoffs without mirroring every leaf skill body."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Workflow Routing and Skill Catalog

Use this sub-skill when the user asks which ARIS skill to run, how W1-W6 connect, what `effort` or `assurance` means, how skill groups are selected, how Codex mirrors differ from mainline skills, or where ARIS artifacts flow between workflows.

## Route Here

- Pick the right ARIS workflow for a research direction, experiment plan, review loop, paper draft, rebuttal, resubmission, talk, patent task, or utility task.
- Explain the common parameter axes: `effort`, `assurance`, reviewer, GPU backend, human checkpoints, and auto-proceed behavior.
- Diagnose why a workflow stopped because a required artifact is missing.
- Decide whether to invoke an orchestrator or a leaf skill.
- Maintain a user's minimal install set by mapping tasks to skill groups.

## Reroute

- Installation mechanics, manifests, or skill-link failures: `../install-and-distribution/SKILL.md`.
- Reviewer/backend setup or cross-model review correctness: `../review-and-provider-backends/SKILL.md`.
- Research Wiki, session recovery, or watchdog state: `../state-recovery-and-experiment-ops/SKILL.md`.
- Source edits to skill catalog, mirrors, or tests: `../repository-maintenance/SKILL.md`.

## Fast Routing

- New research direction -> W1 `/idea-discovery` or full `/research-pipeline`.
- Existing experiment plan -> W1.5 `/experiment-bridge`.
- Existing paper/results needing iterative critique -> W2 `/auto-review-loop` or a reviewer variant.
- Narrative report ready for manuscript -> W3 `/paper-writing`.
- Reviews received -> W4 `/rebuttal`.
- Rejected paper to a new venue under no-new-experiment constraints -> W5 `/resubmit-pipeline`.
- Accepted paper to presentation -> W6 `/paper-talk`.
- Single utility need -> route directly to the leaf skill group instead of the whole orchestrator.

## Reference Map

- `references/workflow-map.md` lists W1-W6, core artifacts, and when to use each path.
- `references/skill-groups.md` summarizes the catalog groups and representative skills.
- `references/troubleshooting.md` covers missing artifacts, over-broad workflows, group selection issues, and same-family review caveats.
- Root `../../references/capability-map.md` maps all major ARIS surfaces to sub-skills.

## Important Distinctions

- `effort` controls breadth/depth/budget; `assurance` controls audit strictness. They are independent.
- At high assurance, audit gates may block a final report even if drafting succeeded.
- Codex base mirrors are useful for Codex execution but same-family review must be labeled provisional unless an independent gate is configured.
- HTML reports are readable views; Markdown/JSON artifacts remain canonical.
