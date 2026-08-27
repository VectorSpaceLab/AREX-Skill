---
name: refresh-repo-skill
description: "Refreshes an existing repository-specific Agent Skill after the source repository changed. Use when the user says repo code, APIs, docs, examples, configs, dependencies, or behavior changed and an old skill may now be stale, outdated, inconsistent with current code, or needs to be resynchronized from repository evidence."
metadata:
  disco-role: meta
---

# Refresh Repo Skill

## Purpose

Use this skill when an existing repo-specific Agent Skill should continue
describing the same repository, but the repository itself has changed since the
skill was created or last maintained.

Typical requests include:

- Refresh an old skill after new commits, releases, branches, APIs, CLIs,
  config formats, examples, or dependencies changed.
- Audit a skill for stale claims against the current repository code.
- Update copied references, scripts, workflows, troubleshooting, or usability
  cases that no longer match the repo.
- Rebuild the skill's repository evidence without discarding the skill's useful
  identity, routing, or prior coverage.

This workflow is different from `extend-repo-skill`: use
`extend-repo-skill` when the user asks to add a new capability or deeper
coverage to a working skill. Use this skill when repository drift is the main
reason the skill may be wrong.

## Inputs

Gather or infer:

- Existing skill directory containing `SKILL.md`.
- Current repository path to use as the source of truth.
- Existing `references/repo-provenance.md` from the skill, when present.
- Optional previous repository baseline, branch, tag, release, commit, or date
  when the skill has no provenance file.
- Python inspection environment and installed package name when live API or CLI
  verification is needed.
- Existing review/test artifact directory, if any.
- Desired review/test artifact output directory, if the user has a preference.

If the existing skill directory is missing or does not contain `SKILL.md`, stop
and ask for the correct skill path. If the repository path is missing and cannot
be inferred from the current working directory or user request, ask for it.

## Reference Map

Read these references as the workflow reaches each stage:

- [references/change-detection-and-staleness-audit.md](references/change-detection-and-staleness-audit.md):
  identify the current repo state, optional baseline, stale claims, and affected
  skill areas.
- [references/refresh-editing.md](references/refresh-editing.md): edit the
  existing skill in place, replace outdated guidance, preserve useful identity,
  and update tests/scripts/references.
- [references/verification-and-handoff.md](references/verification-and-handoff.md):
  run stale-claim checks, live verification, usability review, and final
  handoff.

Use [scripts/check_repo_provenance.py](scripts/check_repo_provenance.py) when
`references/repo-provenance.md` exists. It compares the skill snapshot with the
current Git checkout and prints JSON with `current`, `stale`, or `unknown`
status.

When useful, also read sibling workflow-skill references:

- `../create-repo-skill/references/` for repository evidence discovery,
  installed-package inspection, and output structure.
- `../verify-repo-skill/references/` for usability case format,
  verification review, and import/index routing guidance.
- `../extend-repo-skill/references/` for narrow editing and regression
  review rules.
- `../prepare-repo-skill-env/SKILL.md` if live Python
  inspection is needed and no verified environment is available.

## Required Workflow

1. Resolve the existing skill directory, current repository path, existing
   `references/repo-provenance.md` baseline, optional user-provided baseline,
   Python inspection context, review/test artifact directory, and review output
   path. If the user does not specify an artifact directory, default to
   `<repository-path>/skills/tests/<skill-id>/`, with usability cases under
   `test-cases/` and review reports under `reports/`. If the existing skill is
   the live managed copy under `<agent-dir>/skills/repositories/repo-skills/<skill-id>/`, copy
   only its runtime tree to a temporary working directory outside
   `<agent-dir>/skills/` before editing. Keep that working copy until the
   dedicated importer succeeds; never edit the live managed copy in place.
2. Read [references/change-detection-and-staleness-audit.md](references/change-detection-and-staleness-audit.md).
   Build a current-state map of the existing skill. When provenance exists, run
   `python scripts/check_repo_provenance.py --skill-dir <skill_dir> --repo-path <repo_path>`
   from this workflow-skill directory or adapt the script path to the installed
   skill copy. Use its JSON output as the first staleness signal, then gather
   current repository evidence and optional change evidence from Git history or
   release notes.
3. Produce a staleness audit that separates:
   - Claims still supported by current repo evidence.
   - Claims that are stale, removed, renamed, or behaviorally changed.
   - New repo capabilities that should be represented because they replace or
     materially alter existing skill guidance.
   - Unknowns requiring live inspection or user clarification.
4. If live Python inspection is required and no verified environment exists, use
   `prepare-repo-skill-env` to create or repair one, then
   continue only from its verified handoff.
5. Read [references/refresh-editing.md](references/refresh-editing.md). Edit the
   resolved runtime working copy in place. Preserve root and sub-skill identities unless the
   user explicitly asks for a rename or the current name is invalid. Add or
   update `references/repo-provenance.md` with the refreshed source snapshot.
   Preserve the canonical `repo_id` and `skill_id` by default. Treat the
   existing area-family assignments as the routing baseline: keep them when
   the repository's capability scope is unchanged, but do not keep them
   blindly when the refresh adds, removes, or materially changes a capability.
   If the capability scope changed, the taxonomy hash changed, or the user
   requests reclassification, produce a new external area-family routing
   handoff and matching minimal v2 metadata before import. Do not hand-edit
   generated router Markdown or silently change assignments in prose.
6. Update usability test cases under the review/test artifact directory's
   `test-cases/` subtree so at least one case proves refreshed behavior and at
   least one case guards a pre-existing workflow that should remain valid.
7. Read [references/verification-and-handoff.md](references/verification-and-handoff.md).
   Verify that refreshed public skill content is self-contained, current,
   privacy-safe, and reachable from nearby `SKILL.md` files. Save staleness
   audits, verification reports, and human-review notes under the review/test
   artifact directory's `reports/` subtree.
8. After verification passes, follow `verify-repo-skill`'s structured import
   policy: use `ask_user_question` when approval is still required, then run the
   approved or auto-authorized refresh through
   `verify-repo-skill/scripts/import_repo_skill.mjs` with `--overwrite`, the
   refreshed runtime skill directory, and `--routing-entry
   <repo-path>/skills/disco/routing_decision/classification.json`. The external
   handoff is mandatory for a normal classified import, even when the existing
   area-family assignments are retained. Use `--overwrite` only because this
   workflow is updating that exact approved repo skill. The helper installs the
   refreshed runtime tree under
   `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/`, rebuilds the
   sibling live DisCo `repo-skills-router` under the global lock, and restores
   both on failure. Do not hand-edit router Markdown or manually combine copy
   and updater commands. The refreshed skill is directly available to DisCo
   Researcher in a new session; use `import-repo-skills-to-agent` only when the
   user explicitly asks for a cross-agent export.

## Non-Negotiables

- Treat the current repository as the source of truth; do not preserve old skill
  claims just because they were previously useful.
- Do not regenerate a replacement skill from scratch unless the user explicitly
  asks or the old skill is so structurally invalid that in-place repair would be
  misleading.
- Do not edit a live skill under `<agent-dir>/skills/repositories/repo-skills/` before the
  global import lock is held. Refresh an external working copy, then let
  `verify-repo-skill/scripts/import_repo_skill.mjs` replace the live target.
- Do not finish a refresh without `references/repo-provenance.md`; if the old
  skill lacks it, create it from the current repository snapshot.
- Do not silently change a repository's `repo_id` or `skill_id` during a
  refresh. A rename is a separate identity migration and must update the
  central repository index and all router references together.
- Do not silently change area-family assignments. Preserve the prior routing
  when capability scope is unchanged; otherwise use the verified external
  routing handoff and minimal v2 metadata, then let the locked importer update
  the router and indexes atomically.
- Do not change the skill's public purpose to cover unrelated new repository
  areas unless those areas replace or materially affect existing guidance.
- Do not add claims about APIs, CLIs, configs, data formats, dependency
  behavior, or runtime behavior without current repository evidence or live
  inspection.
- Do not leak local checkout paths, Python executable paths, conda or virtualenv
  names, `pip show` locations, API keys, or machine-specific details into public
  skill files.
- Do not link runtime skill documentation to the source repository checkout.
  Distill current facts into the skill directory.
- Do not preserve or reintroduce runtime instructions that refer to source repo
  scripts, examples, notebooks, tools, or configs by path. If the refreshed
  skill still needs that behavior, add a bundled replacement under the skill's
  own `scripts/` or `references/` tree and link it instead.
- Do not treat `tests/` as a skill directory. It is the review/test artifact area.
- Do not write staleness audits, `evals/`, verification reports, human-review
  notes, publication checklists, prompt samples, benchmark notes, or other
  check-only artifacts inside the runtime skill directory. Put concrete
  usability cases under the review/test artifact directory's `test-cases/`
  subtree and reports under its `reports/` subtree, defaulting to
  `<repository-path>/skills/tests/<skill-id>/`.

## Output Summary

By the end, the user should have:

- A runtime working copy refreshed against current repository evidence, followed
  by a locked live replacement when import is approved or auto-authorized.
- An updated `references/repo-provenance.md` snapshot that future agents can use
  to detect whether the skill may be stale.
- A staleness audit and review package under the review/test artifact
  directory's `reports/` subtree that identifies changed, retained, and removed
  guidance.
- Updated references, scripts, sub-skills, and usability test cases where the
  old skill was stale.
- Verification evidence showing the public skill no longer depends on outdated
  repo facts.
- A routing handoff stating whether prior area-family assignments were
  preserved or reclassified, with the reason and evidence for any change.
- A final handoff that distinguishes refreshed public skill content, review/test
  artifacts, evidence used, and any accepted uncertainty.
