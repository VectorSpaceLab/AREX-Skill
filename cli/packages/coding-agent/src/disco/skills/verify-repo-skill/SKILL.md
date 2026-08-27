---
name: verify-repo-skill
description: "Verifies a generated or refreshed repo-specific Agent Skill by creating assertion-backed usability test cases, running content-level self-refine, checking backend-classified native repo examples/tests against the prepared CPU/GPU environment plan, enforcing required-backend and import gates, checking static quality, and producing final coverage and handoff artifacts. Use this after create-repo-skill, refresh-repo-skill, or extend-repo-skill finishes an integrated runtime skill draft, and whenever a repo skill needs usability or publication verification."
metadata:
  disco-role: meta
---

# Verify Repo Skill

## Purpose

Use this skill after a generated, refreshed, or extended repo skill draft exists.
It owns usability test case generation, content-level self-refine, native
repo test/example verification after whole-skill integration, static
verification, final coverage report creation, review-package creation, and
final verification handoff. Treat required GPU/accelerator runtime evidence as
a verification gate: synthetic assertions may test guidance and failure
handling, but cannot prove that the backend actually runs.

This skill does not create the repo skill from source evidence. It verifies and
refines an already-created runtime skill directory using the original creation
context, evidence notes, coverage/depth matrix, planned sub-skill structure, and
review rubrics when available. When this skill is called after
`create-repo-skill`, the runtime skill should already include all
sub-skills, root routing, repo-level references/scripts, repo provenance, and a
main-agent integration pass over parallel subagent outputs.

## Inputs

Resolve these before writing verification artifacts:

- Runtime repo skill directory containing `SKILL.md`.
  Keep this verified runtime directory outside `<agent-dir>/skills/repositories/`; if the only
  starting copy is live, make an external working copy before refining it.
- Review/test artifact directory. If omitted, use the artifact root selected by
  the calling workflow, normally `<repository-path>/skills/tests/<skill-id>/`.
  Write concrete test cases under `test-cases/` and reports or review
  documents under `reports/`.
- Repository path or evidence summary used to create the skill.
- Python inspection handoff, including `ok`/`partial`/`failed` readiness and
  every prepared backend prefix, or public package facts used by the skill.
- Coverage/depth matrix, target file tree, sub-skill plan, and subagent review
  rubrics from the calling workflow.
- Integration artifacts from the calling workflow, including the backend
  verification plan, backend-classified native test/example candidate map,
  integration notes, and long-tail gap register when available.
- Import decision policy from the calling workflow. Default to
  `importAfterVerification: ask`; use `auto-import` only when the original user
  request explicitly delegated the final import decision.
- Any user-provided verification focus, such as required scenarios, specific
  workflows, known failures, or publication gates.
- The original repository checkout and the current fixed taxonomy when router
  placement is required. The repository checkout is the primary routing
  evidence source; generated skill prose is only a summary/navigation aid.

Do not write check-only artifacts into the runtime skill directory. Keep
usability cases under `test-cases/` in the review/test artifact directory, and
keep evals, verification reports, human-review notes, publication checklists,
prompt samples, staleness audits, benchmark notes, and final reports under
`reports/` in that artifact directory.

## Reference Map

Read these references as the workflow reaches each stage:

- [references/usability-test-cases.md](references/usability-test-cases.md): how
  to create realistic, evidence-backed, assertion-backed user-prompt case
  directories and coverage indexes.
- [references/evaluation-verification-and-handoff.md](references/evaluation-verification-and-handoff.md):
  content-level self-refine, native repo test/example verification, static
  verification checklist, final skill coverage report, review package, final
  handoff, import guidance, and quality bar.
- [scripts/run_native_cases.py](scripts/run_native_cases.py): optional
  manifest-driven helper for running preselected safe native repo verification
  commands with timeouts and JSON output. Use it only after an agent has
  classified candidate commands and backend metadata for the assigned
  environment; it preserves required accelerator blocks instead of converting
  them to ordinary skips.
- [scripts/import_repo_skill.mjs](scripts/import_repo_skill.mjs): required entry
  point for an approved or auto-authorized DisCo repo-skill import. It acquires
  the global lock, stages and validates the runtime tree, installs it under
  `~/.disco/agent/skills/repositories/repo-skills/`, rebuilds the sibling live
  `repo-skills-router`, and rolls back both on failure.
- [scripts/with_import_lock.mjs](scripts/with_import_lock.mjs): lower-level lock
  helper used by the dedicated importer and router updater. Do not manually
  compose the normal repo-skill import with this helper.
- [scripts/update_repo_skills_router.mjs](scripts/update_repo_skills_router.mjs):
  lower-level managed updater called by the dedicated importer. Use it directly
  only for an intentional router-only maintenance or staging operation.
- [scripts/build_repo_skills_collection.mjs](scripts/build_repo_skills_collection.mjs):
  one-pass builder for an initial or collection-wide rebuild. It accepts an
  explicit source import manifest, terminal repository manifest, assignment
  ledger, taxonomy, and fresh staging directory; validates all inputs before
  copying, writes the v2 routing projection, runs the updater once, and leaves
  the staged collection for the managed-library transaction. Do not call the
  single-repository importer once per repository to perform a full build.

## Required Workflow

Use todo tracking or a visible checklist so the user can follow verification
progress.

1. Verification setup:
   Confirm the runtime skill directory, artifact directory, source repo context,
   creation evidence, planned sub-skill structure, coverage/depth matrix, and
   any user-specified verification focus. Inspect the generated root
   `SKILL.md`, sub-skills, references, scripts, repo provenance, integration
   notes, native test/example candidate map, and long-tail gap register before
   writing verification artifacts.
2. Usability test case generation:
   Read [references/usability-test-cases.md](references/usability-test-cases.md).
   Create realistic, difficult, evidence-backed case directories under
   `<artifact-root>/test-cases/`, including `user_request.txt`, `README.md`,
   optional fixtures, per-case `assertions.json`, and an `index.md` that maps
   cases to root or sub-skill capabilities. The generated cases should stress
   routing, workflow depth, support workflows, troubleshooting, and source-repo
   dependency avoidance, not just happy-path prompts. For every generated
   sub-skill, create one or two new difficult synthetic cases in addition to
   cases derived directly from original repo tests/examples. After all
   sub-skills are integrated, also create one or two integrated difficult cases
   under `test-cases/integration/`; prefer adapting original repo tests/examples
   from the native candidate map, and synthesize only when no suitable native
   integrated case exists.
3. Content-level self-refine:
   Read [references/evaluation-verification-and-handoff.md](references/evaluation-verification-and-handoff.md).
   Review the whole skill against the user request, confirmed repository
   include/exclude map, planned sub-skill structure, subagent rubrics, coverage
   matrix, self-containment, privacy, routing, references, scripts, and
   assertion-backed usability cases. Revise the runtime skill when the review
   finds actionable gaps.
4. Native repo test/example verification:
   Using the native test/example candidate map from the calling workflow or one
   built during setup, select a safe representative subset of original repo
   examples, tests, CLI help checks, tiny-fixture checks, or smoke scripts. Use
   the backend verification plan to run each selected case in its assigned
   prepared environment. Every `required` backend capability with no full CPU
   substitute needs runtime evidence from its actual backend; do not replace it
   with a CPU import or synthetic usability case.
   Run only commands that are safe for the current environment: short,
   deterministic, no network, no credentials, no destructive writes, no large
   downloads, and no long training unless the user explicitly approves. Record
   PASS, SKILL_GAP, NATIVE_FAIL, BLOCKED_REQUIRED_BACKEND, SKIP_UNSAFE, and
   SKIP_NOT_SELECTED results under the artifact directory. Use
   `BLOCKED_REQUIRED_BACKEND` when required hardware/environment/runtime
   evidence is unavailable. Treat it as a high or critical import blocker, not
   a skip or pass. Use failures or gaps to revise the runtime skill before
   static verification when the generated skill is wrong or thin.
5. Static verification, final report, and review package:
   Run the static checks from the verification reference. Save verification
   reports, final skill coverage report, human-review notes, publication
   checklist, prompt samples, native verification reports, and any
   eval/self-refine notes under `<artifact-root>/reports/`.
6. Router placement:
   When the skill is intended for the managed repository collection, classify
   the repository against the exact fixed taxonomy after verification. Inspect
   README and substantive documentation first, then the generated root and
   relevant sub-skills, package manifests/entry points, and only a small number
   of source/config/test artifacts needed to resolve ambiguity. Assign zero or
   more exact area -> family paths. Every assignment needs its own rationale
   and at least one non-generated repository evidence item; reject keyword-only,
   dependency-only, optional-integration, example-only, and context-collision
   matches. If no exact family is supported, record `unclassified` and ask the
   user whether to import it. If the user wants it imported, propose a taxonomy
   extension and wait for user approval or correction before changing the
   taxonomy. Interrupted or inaccessible classification is `blocked` or
   `failed`, not a guessed assignment.

   Write the full decision outside the runtime skill, preferably under
   `<repo-path>/skills/disco/routing_decision/`, with a machine-readable
   `classification.json` and human-readable `evidence.md`. The runtime
   `references/repo-routing-metadata.json` is only the minimal v2 projection:
   `schema_version`, canonical `owner/repository` `repo_id`, `skill_id`, the
   current taxonomy hash, `routing_status`, exact assignments, and an
   `unclassified_reason` only when applicable. Do not store evidence or
   rationale in that runtime JSON.
7. Handoff and import readiness:
   Report the runtime skill path, artifact path, usability coverage, native
   verification results, failures fixed, remaining long-tail gaps, and whether
   the skill is ready to import. Record that a self-contained, versioned
   repo/package skill is classified as high reuse because it is intended to
   support multiple checkouts, projects, and research tasks. This classification
   selects the specialized managed repo collection, not the generic managed
   importer or the current project's `.agents/skills`. If
   `importAfterVerification` is `ask`, use
   `ask_user_question` when available to ask whether to import the verified
   runtime skill into `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/`; do not only ask in a normal
   assistant message and stop. If `importAfterVerification` is `auto-import`
   and the skill is verified/import-ready with no unresolved high or critical
   failures or `BLOCKED_REQUIRED_BACKEND` results, import without asking again
   and state that the original create request authorized auto-import. A partial
   environment handoff or required-backend block disables auto-import even if
   the original request delegated it. Present the exact limitation and require
   a new informed manual import decision after final verification. If import is
   approved or auto-authorized,
   run the dedicated importer once with the verified runtime skill directory
   and its verified external routing handoff:

   ```bash
   node scripts/import_repo_skill.mjs --agent-dir <agent-dir> --routing-entry <classification.json> [--overwrite] <runtime-skill-dir>
   ```

   The handoff is not only an assignment list: it must include the canonical
   source URL, source commit, final `skill_root`, and the SHA-256 digest of the
   portable runtime skill tree. Every classified assignment must carry its own
   rationale and at least one non-generated repository evidence item. The
   importer validates these fields and passes the handoff to the router updater
   so the central repository index preserves provenance.

   Omit `--overwrite` for a new skill. Use it only after approval to replace
   that exact existing repo skill. The importer copies only the runtime tree,
   recursively validates its role and visibility contract, requires the v2
   `references/repo-routing-metadata.json` and matching routing handoff, acquires the global lock, rebuilds
   and validates the live DisCo `repo-skills-router`, and restores both the previous skill and router on failure. Do not hand-edit router Markdown as the import mechanism or manually combine a copy command with the lower-level updater. After success,
   DisCo Researcher can use the managed skill in a new session without exporting
   it to another agent. Use `import-repo-skills-to-agent` only when the user
   explicitly asks for a cross-agent export.

## Non-Negotiables

- Do not put usability cases, evals, verification reports, human-review notes,
  publication checklists, prompt samples, or other check-only artifacts inside
  the runtime skill directory.
- Do not mix concrete test cases and review/report documents directly under the
  artifact root. Test cases belong under `test-cases/`; review and verification
  documents belong under `reports/`.
- Do not mark a repo skill verified if runtime Markdown links point outside the
  skill tree, required bundled references/scripts are missing, local
  environment paths leak into public files, or root/sub-skill routing is too
  thin to use.
- Do not treat the generated usability test cases as runtime documentation.
- Do not treat skipped native repo examples/tests as passing. Record the skip
  reason and decide whether a synthetic assertion-backed case should cover the
  same capability.
- Do not classify an unavailable required backend as an ordinary skip. Record
  `BLOCKED_REQUIRED_BACKEND`, keep the skill not fully verified, and prevent
  auto-import until the backend is verified, scope is explicitly narrowed, or
  the user manually accepts the final limitation.
- Do not use synthetic assertions, CPU imports, source inspection, or docs as a
  substitute for required GPU/accelerator runtime evidence. They may validate
  guidance while the runtime block remains visible.
- Do not run original repo native examples/tests before the generated skill has
  been fully integrated across all sub-skills; native ground-truth checks are a
  final verification gate, not a sub-skill drafting shortcut.
- Do not import a skill before high or critical verification failures are fixed
  or explicitly accepted by the user.
- Do not treat an earlier acceptance to continue partial drafting as final
  import approval. Ask again after the exact native backend gaps are known.
- Do not import a skill through an unlocked or manually assembled copy/update
  sequence. Use `scripts/import_repo_skill.mjs`; its lock covers staging,
  runtime skill replacement, router creation from the template when missing,
  structured metadata reads, managed router rebuild, stale-file removal, final
  checks, and failure rollback.
- Do not update `repo-skills-router` by free-form Markdown editing during an
  import. The dedicated importer owns the lower-level
  `scripts/update_repo_skills_router.mjs` call.
- Do not treat `auto-import` as permission to overwrite an unrelated existing
  managed skill. If the target import directory already exists and this workflow
  is not explicitly updating that exact skill, ask before replacing it or choose
  a non-conflicting import name when that is consistent with the generated skill
  id policy.
- Keep the final report clear about what was verified, what was revised, where
  artifacts were written, and what risk remains.

## Output Summary

By the end, the user should have:

- A verified or explicitly-not-verified runtime repo skill directory.
- Usability case directories plus `index.md` under
  `<artifact-root>/test-cases/`.
- One or two difficult synthetic cases for each sub-skill, plus one or two
  integrated difficult cases under `<artifact-root>/test-cases/integration/`.
- Optional self-refine notes and a clean review package under
  `<artifact-root>/reports/`.
- Native repo test/example candidate and verification reports under
  `<artifact-root>/reports/verification/` when original repo examples/tests
  were available.
- A reconciled backend verification result that names prepared environments,
  required backend passes, optional skips, alternatives, and every
  `BLOCKED_REQUIRED_BACKEND` item.
- A final skill coverage report comparing original repo capabilities,
  generated skill coverage, native verification results, and remaining
  long-tail gaps.
- A concise verification handoff with full, partial, or blocked import
  readiness and a
  `repo-skills-router` routing update when import is approved or auto-authorized.
