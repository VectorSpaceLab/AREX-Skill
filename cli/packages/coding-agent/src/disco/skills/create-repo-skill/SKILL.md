---
name: create-repo-skill
description: "Creates a repo-specific operating Agent Skill for DisCo Researcher from a local repository by inspecting source files and an installed or auto-prepared, backend-aware Python package environment. Use when the user asks to create a skill for a repo, generate repo-specific skills, analyze a local Python package, or build a DisCo skill that may also be exported to compatible agents. If the user gives only a repo path, analyze the repository structure and native tests/examples first, confirm the extraction scope, then use prepare-repo-skill-env to create and verify the minimum CPU/GPU/backend environment set required by that scope. If the request says auto decide, agent-confirm the extraction scope; if it says auto import, import only after successful verification with no unresolved required-backend block."
metadata:
  disco-role: meta
---

# Create Repo Skill

## Purpose

Use this skill to create a high-quality, repo-specific operating Agent Skill for
DisCo Researcher. The managed DisCo copy is the primary runtime destination; a
user may separately export it to Claude Code, Codex, or another compatible
agent, but export is not required for DisCo to use it.

Repo/package guidance is intentionally treated as a high-reuse operating graph: a self-contained skill for a versioned public package can support the same repository across many checkouts, projects, and research tasks. Its approved live destination is therefore the managed repo collection at `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/`, not the current project's `.agents/skills/`. This is a specialized managed deployment: the import must also rebuild the sibling `repo-skills-router` in the same locked transaction, so never send repo output through the generic operating-graph importer.

If the user does not provide a repository path, use the current working
directory as the target repository.

The user may delegate the manual decisions in this workflow. Treat phrases such
as `auto decide`, `agent decide`, `decide the scope yourself`, `auto import`,
`default import`, or `do not ask me to confirm scope/import` as an explicit
decision policy for this create run. The policy has two independent parts:

- `extractionScope: ask` by default, or `agent-decide` when the user delegates
  scope approval.
- `importAfterVerification: ask` by default, or `auto-import` when the user
  delegates the final import decision.

This policy only skips the routine scope approval and final import approval. It
does not authorize unsafe commands, broad dependency installation, mutation of a
user-provided environment that may break it, overwriting an existing skill, or
importing a skill that failed verification. `auto-import` also does not accept
an unavailable or unverified required backend. A required-backend block must be
resolved, removed by an explicitly narrowed extraction scope, or presented for
an informed manual acceptance after final verification.

The user may also provide a temporary Python environment where the package from
that repository has already been installed for inspection. If the user does not
provide that environment, do not stop and ask for one. Defer automatic
environment preparation until after repository structure analysis and either
user confirmation of the extraction scope or agent-confirmation under an
explicit `agent-decide` policy. Then use
`prepare-repo-skill-env` to create, install, and verify the minimum private
inspection environment set whose dependencies and backend variants cover the
confirmed directories, selected workflows, required native verification
candidates, and user requirements, and continue this workflow from the handoff.
The prepare-env skill should prefer Conda when available, use micromamba,
venv, or uv when appropriate, and execute environment creation, installation,
and verification as explicit terminal commands. If no suitable manager or
Python exists, it should make the required host-level runtime installation
visible and obtain authorization before performing it rather than invoking a
bundled bootstrap helper.

The user may also provide a preferred generated-skill output path, a preferred
review/test artifact output path, a preferred environment prefix for automatic
environment preparation, the installed package name, known troubleshooting
notes, and extra extraction requirements. If no output path is provided,
default to creating the generated skill under the repository's own `skills/`
directory. If that directory already exists, create a `disco/` subdirectory
inside it as the active skills root for DisCo-generated output.

The installed Python environment is required so the agent can inspect live APIs, function signatures, modules, imports, CLI entry points, and runtime behavior instead of relying only on source-code guesses. It can be provided by the user or prepared automatically via the prepare-env skill. Treat this environment as private research context. It must not appear in the generated repo skill.

## Reference Map

Read these references as the workflow reaches each stage:

- [references/input-output-and-structure.md](references/input-output-and-structure.md): input collection, canonical skill ids, output path resolution, default runtime skill and `skills/tests/` artifact locations, generated skill tree, and content placement rules.
- [references/repository-evidence.md](references/repository-evidence.md): how to discover source roots, docs, examples, scripts, tests, configs, existing repo-local skills, extraction evidence maps, backend-classified native test/example candidates, and the backend verification plan before extracting skills.
- `../prepare-repo-skill-env/SKILL.md`: backend-aware environment preparation after repository structure analysis, including minimal dependency selection for the confirmed extraction scope, required-backend readiness, and existing-environment mutation safeguards.
- [references/installed-package-inspection.md](references/installed-package-inspection.md): read-only inspection of the user-provided or automatically prepared installed package environment and how to avoid leaking local environment details.
- [references/planning-and-writing.md](references/planning-and-writing.md): sub-skill boundaries, coverage/depth matrix, dynamic workflow generation, whole-skill integration gates, target file tree planning, generated `SKILL.md` frontmatter, references, scripts, and anti-patterns.
- `../verify-repo-skill/SKILL.md`: final assertion-backed usability test case generation, content-level self-refine, native repo test/example verification, static verification, final coverage report, review package, handoff, and import readiness after this skill has created and integrated the runtime repo skill.

## Required Workflow

Use the agent's available todo or task-list mechanism for this workflow so the
user can see the current phase, especially during repository analysis,
environment preparation, sub-skill generation, review, and handoff to
verification. If the current agent has no todo tool, maintain a visible
checklist in the conversation.

1. User request analysis:
   Read [references/input-output-and-structure.md](references/input-output-and-structure.md). Identify the repository path, Python inspection environment if provided, preferred conda prefix if provided, skill output directory, review/test artifact directory, extra extraction requirements, delegated decision policy (`extractionScope` and `importAfterVerification`), and any other information that can affect extraction. Use the current working directory when the repo path is omitted. Resolve the canonical skill id, active skills root, generated skill directory, artifact directory, and private default inspection prefix before writing files. If the user did not provide a usable Python inspection environment, do not prepare it yet; record the default prefix under `$DISCO_CODING_AGENT_DIR/envs/<chosen-skill-id>-inspection` when that variable is set, otherwise under `~/.disco/agent/envs/<chosen-skill-id>-inspection`, and defer installation until after repository structure analysis confirms which directories will be used.
2. Repository structure analysis:
   Read [references/repository-evidence.md](references/repository-evidence.md). Inspect the repository tree, package metadata, source roots, docs, examples, scripts, tests, configs, and existing repo-local skills. Build a concise extraction evidence map that names directories to include and directories to exclude from later extraction context. Also build a native test/example candidate map from repo-owned examples, tests, notebooks, CLI snippets, fixtures, and smoke scripts. Classify each candidate by workflow, safety, backend requirement (`cpu`, `cuda`, `rocm`, `mps`, accelerator-specific, or `any`), backend criticality (`required`, `optional`, or `alternative`), CPU substitution (`full`, `partial`, or `none`), dependency variant, hardware prerequisites, and verification expectation. After the extraction scope is confirmed, derive a backend verification plan for included workflows: required/optional backend coverage, minimum environment set, hardware probes, preparation smoke checks, final native cases, and the blocking consequence of unavailable required hardware. Separately build a source script inventory for repo-owned `scripts/`, `tools/`, `bin/`, example scripts, and workflow helpers, classifying each useful script as copy, adapt, wrap, reference-only, or exclude with a concrete reason. Do not run native tests/examples in this phase. If `extractionScope` is `ask`, ask the user whether the directory scope and backend plan are reasonable before continuing and incorporate any correction. If `extractionScope` is `agent-decide`, do not stop for routine approval; mark both as agent-confirmed, briefly report include/exclude and backend decisions to the user, record the decision mode and rationale under the review/test artifact directory's `reports/integration/` subtree when practical, and continue.
3. Environment preparation:
   Read and use `../prepare-repo-skill-env/SKILL.md`. Prepare or verify the Python inspection environment only after the repository structure analysis and backend verification plan are confirmed. Pass the included/excluded directories, package metadata, backend-classified native candidate map, backend verification plan, and user extraction requirements into the install plan. Install the minimum environment set that satisfies every required backend for selected capabilities, not merely the smallest CPU-importable set. Usually one GPU-capable environment can cover CPU checks; use separate prefixes only when dependency variants conflict or an independent CPU fallback claim also requires verification. Do not install optional backend packages for excluded or unselected workflows. If the user provided an existing environment and verification shows that reinstalling, upgrading, or repairing packages may mutate or break it, ask before modifying that environment. If modification is not allowed, create a new private prefix when permitted. Continue automatically only from an `ok` handoff. If a required backend is unavailable, either narrow the extraction scope with user approval, stop with a failed handoff, or continue drafting only after the user explicitly accepts a `partial` handoff; carry that block forward and disable auto-import.
4. Sub-skill structure generation:
   Read [references/installed-package-inspection.md](references/installed-package-inspection.md) and [references/planning-and-writing.md](references/planning-and-writing.md). Use repository evidence plus installed-package inspection to plan only the sub-skill structure first: canonical sub-skill ids, responsibilities, boundaries, evidence sources, target files, expected references/scripts, source-script imports or adaptations owned by each sub-skill, troubleshooting references and failure modes each sub-skill must cover, native test/example candidates relevant to each sub-skill, cross-references, and review rubrics. The main agent owns this structure and should optimize it for future usability, not for mirroring source folders mechanically. Do not write the detailed sub-skill content in this phase. Keep the planned overall generated skill shape compatible with this skill's existing root `SKILL.md`, `references/`, `scripts/`, and `sub-skills/` structure.
5. Coordinated skill generation:
   When running in DisCo, use the built-in `workflow` tool to coordinate generation. Write the workflow so each planned sub-skill id appears in the relevant phase and in each `agent()` call's `subSkill` option, making progress visible while subagents write and revise sub-skills. In other agents, use the same process with whatever task, subagent, or manual sequencing tools are available. Each subagent prompt must include a complete scope-specific brief from the structure plan: target sub-skill id, exact `sub-skills/<id>/` output subtree, frontmatter name requirement, responsibility, included and excluded capabilities, evidence files to inspect, installed-package facts to verify, required references/scripts, source scripts to copy/adapt/wrap or explicitly exclude, troubleshooting failure modes to cover, links to create, related native test/example candidates, and the acceptance rubric. Do not delegate with a short generic request. The workflow should generate sub-skills in parallel when possible, with one or more subagents extracting each planned sub-skill from its assigned evidence. Each drafting or revision subagent must write its assigned runtime files directly under the final generated skill subtree, including `SKILL.md`, bundled `references/`, and bundled `scripts/` as applicable. Do not design the workflow so subagents return full sub-skill Markdown, scripts, or JSON drafts for the main agent to write into the skill directory later. The main agent reviews and evaluates the files the subagent wrote against repo-specific rubrics, sends concrete feedback back to the relevant subagent or revision pass when a sub-skill is thin, inaccurate, poorly routed, not self-contained, incorrectly named, missing useful bundled script imports/adaptations, or missing troubleshooting coverage, and repeats until each sub-skill passes review. Each subagent or revision pass should hand back only its covered capabilities, files created or updated, evidence used, related native test/example candidates, source scripts imported/adapted/excluded with reasons, troubleshooting coverage, checks performed, intentional omissions, and uncertainties for integration notes under the review/test artifact directory.
6. Whole-skill integration and coverage reconciliation:
   After all sub-skills pass main-agent review, the main agent writes the outer `SKILL.md`, repo-level `references/`, and repo-level `scripts/`, then performs a dedicated whole-skill integration pass before verification. Reconcile the subagent outputs into one coverage/depth matrix, one native test/example candidate map, one backend verification plan, one source script import map, one troubleshooting coverage map, and one long-tail gap register under the review/test artifact directory's `reports/integration/` subtree. Recheck backend criticality whenever integration adds, removes, or changes a capability; if the minimum environment set is no longer sufficient, return to `prepare-repo-skill-env` before final native verification. Check root routing, sub-skill boundaries, cross-references, terminology, duplicate content, bundled reference/script ownership, source-repo dependency leaks, whether useful repo scripts were copied/adapted/wrapped into the appropriate root or sub-skill `scripts/` location, whether primary workflows have actionable troubleshooting guidance, and whether every user-facing repo capability has an owner or an explicit gap. Also plan one or two integrated difficult usability cases that exercise multiple sub-skills or root-plus-sub-skill routing; prefer adapting real repo tests/examples from the native candidate map, and create synthetic cases only when repo evidence has no suitable integrated candidate. If integration finds a thin, inconsistent, or missing area, send it back to the responsible subagent or run a focused revision pass before proceeding.
7. Routing decision preparation:
   After the whole skill graph is integrated and before handing it to
   `verify-repo-skill`, classify the original repository against the exact
   fixed taxonomy using the repository checkout as the primary evidence source
   and the generated skill only as navigation context. Assign zero or more
   exact area -> family paths; every assignment needs its own rationale and at
   least one non-generated repository evidence item. Reject keyword-only,
   dependency-only, optional-integration, example-only, and context-collision
   matches. If no exact family is supported, record `unclassified` with a
   bounded reason rather than inventing a weak assignment. Interrupted or
   inaccessible inspection is `blocked` or `failed`, not a guess. Write
   `skills/disco/routing_decision/classification.json` and
   `skills/disco/routing_decision/evidence.md` outside the runtime skill graph,
   then write the candidate minimal v2
   `references/repo-routing-metadata.json` from the same decision. Do not put
   evidence, rationale, confidence, source checkout paths, or scenario fields
   in the runtime JSON; `verify-repo-skill` remains the final authority and may
   repair or reject the candidate before import.
8. Content-level self-refine and usability verification:
   After the runtime skill directory, root `SKILL.md`, sub-skills, bundled references, bundled scripts, repo provenance, coverage/depth matrix, integration notes, long-tail gap register, backend verification plan, native test/example candidate map, and subagent review notes are complete, use `../verify-repo-skill/SKILL.md` for the final assertion-backed usability test cases, content-level self-refine, native repo test/example verification, static verification, final coverage report, review package, and import-readiness handoff. Pass it the generated skill directory, artifact directory, repo evidence summary, sub-skill plan, review rubrics, integration artifacts, environment-preparation handoff, backend verification plan, native candidate map, delegated `importAfterVerification` policy, and any user verification focus. Do not generate usability test cases or verification reports directly in this skill.

## Non-Negotiables

- Do not create generated skill content that depends on the original repository checkout remaining available. Copy, distill, adapt, or wrap source repo material into the generated skill's own `references/` or `scripts/`.
- Do not leave runtime instructions or Markdown links that point to source repo scripts, examples, docs, notebooks, tools, configs, or absolute checkout paths. If a source repo script is needed for future use, create a bundled replacement under the generated skill's `scripts/` or nearest `sub-skills/.../scripts/` directory and link that bundled path.
- Do not replace a useful, safe, repo-maintained script with prose-only Markdown when it can reasonably be copied, adapted, or wrapped as a bundled skill script. If a script is excluded from bundling, record a concrete reason such as unsafe side effects, external credentials, excessive size, generated/vendor status, or irrelevance to the selected workflows.
- Do not leak the user's local Python executable, activation command, virtualenv or conda name, machine-specific paths, local checkout path, or `pip show` installation location into generated public skill files.
- Do not stop solely because the user omitted a Python inspection environment. After repository structure analysis and either user confirmation or explicit agent-confirmation of the extraction scope, use `prepare-repo-skill-env` to prepare one automatically, then continue this workflow from its verified handoff.
- Do not prepare a new inspection environment before repository structure analysis has identified and confirmed the directories that will drive skill extraction, unless the user explicitly asks to prepare an environment as a standalone task.
- Do not install broad extras, all optional dependency groups, dev requirements, or backend packages when only a smaller set is needed for the confirmed extraction scope and user requirements.
- Do not equate "minimum environment" with CPU-only. Satisfy every required
  backend in the confirmed scope, and do not use a CPU import as proof of a
  GPU/accelerator capability when `CPU substitute` is `partial` or `none`.
- Do not silently discard a required native candidate because its hardware is
  unavailable. Narrow the scope, stop, or carry an explicitly accepted partial
  verification block into the final report.
- Do not let `auto-import` bypass an unresolved required-backend block. Require
  an informed manual import decision after final verification if the user
  chooses to accept that limitation.
- Do not mutate a user-provided existing environment to repair or reinstall packages without asking when that change may break the user's environment. If the user declines, use a new private inspection environment instead.
- Do not overwrite or merge into an existing skill directory unless the user explicitly asks to update that exact skill.
- Do not treat `skills/tests/` as an existing skill directory. It is the review/test artifact area.
- Do not write `evals/`, verification reports, human-review notes, publication checklists, prompt samples, staleness audits, usability test cases, or other check-only artifacts inside the generated repo skill directory. Those are owned by `verify-repo-skill` and belong under the configured review/test artifact directory, defaulting to `<repository-path>/skills/tests/<chosen-skill-id>/`, with concrete cases in `test-cases/` and reports or review documents in `reports/`.
- Do not run the original repository's native examples, tests, notebooks, or scripts as final ground-truth checks until all sub-skills have been generated, reviewed, and integrated into one coherent runtime skill. Before that point, discover and classify native candidates only.
- Prefer verified package facts over guesses. Use docs, examples, and tests for intent; use source code and installed-package inspection to confirm API and runtime claims.
- Every generated repo skill must include `references/repo-provenance.md` with the source commit, branch or tag when available, dirty state, package version, and relative evidence paths so future agents can detect staleness.
- Every generated repo skill must include a minimal v2
  `references/repo-routing-metadata.json` containing only `schema_version`,
  canonical `owner/repository` `repo_id`, `skill_id`, the current taxonomy hash,
  `routing_status`, exact `area`/`family` assignments, and an
  `unclassified_reason` only for an unclassified result. Do not put evidence,
  rationale, confidence, source checkout paths, or scenario fields in this
  runtime JSON. The detailed decision belongs in the external
  `skills/disco/routing_decision/` artifact and is validated by
  `verify-repo-skill` before import.
- Every generated root and sub-skill `SKILL.md` frontmatter must double-quote
  `description`, declare `metadata.disco-role: operating`, and include
  `disable-model-invocation: true` so imported repo skills are available only
  in Researcher mode and are routed through `repo-skills-router` in compatible
  targets instead of all appearing in the model-visible skill list. The
  `repo-skills-router` skill itself is also `operating`. Canonical and exported
  routers remain model-visible, while DisCo's live router preserves the user's
  `disco repo-skills router enable|disable` policy. Codex exports add the required `agents/openai.yaml` policy during
  `import-repo-skills-to-agent`; do not add Codex-specific files to the source
  repo skill during creation.
- Every generated package repo skill should include troubleshooting guidance for install/import, optional dependencies, data/config validation, CLI/API misuse, and workflow-specific failure modes when those surfaces exist. Put cross-cutting package issues in root `references/troubleshooting.md` and workflow-specific failures in the nearest sub-skill `references/troubleshooting.md`.
- Every generated sub-skill directory basename, `SKILL.md` frontmatter `name`, workflow `subSkill` option, coverage/depth matrix output location, and usability target id must use the same canonical lowercase-hyphen sub-skill id. Do not add the repo name to sub-skill ids unless it is truly needed to disambiguate two sibling sub-skills, because the root skill already names the repository.
- Keep generated root and sub-skill `SKILL.md` files router-like. Move API tables, workflow depth, CLI catalogs, model lists, data schemas, long examples, and troubleshooting matrices into the nearest bundled `references/`.
- After verification, follow `verify-repo-skill`'s locked import protocol: use `ask_user_question` when import approval is still set to `ask`; when the user explicitly delegated `auto-import`, import without asking again only after successful verification with no partial handoff or unresolved `BLOCKED_REQUIRED_BACKEND`. In both cases, run `verify-repo-skill/scripts/import_repo_skill.mjs` with the verified runtime skill directory and its external routing handoff. That helper stages and recursively validates the runtime tree, installs it under `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/`, rebuilds the sibling live DisCo `repo-skills-router` under the global lock, and restores the previous skill, repository index, and router if the transaction fails. Pass `--overwrite` only after approval to replace that exact existing repo skill. Do not hand-edit router Markdown or manually combine a copy command with the router updater. Do not synchronize into other agent tools during this workflow; use `import-repo-skills-to-agent` only when the user explicitly asks to export DisCo's managed skill library.
- Do not reinterpret repo-to-skills output as ordinary project-scoped output merely because construction ran inside one checkout. Its self-contained, versioned package contract is the evidence for high reuse; if a candidate is actually bound to private project state and cannot satisfy that contract, it is not import-ready for this repo library.

## Output Summary

By the end, the user should have:

- A generated self-contained repo skill directory containing `SKILL.md`, `references/repo-provenance.md`, `references/repo-routing-metadata.json`, and when useful, `sub-skills/`, additional `references/`, and `scripts/`.
- A unified review/test artifact directory path, defaulting to `<repository-path>/skills/tests/<chosen-skill-id>/`, with `test-cases/` for concrete usability/native-backed/synthetic case directories and `reports/` for integration notes, coverage/depth matrix, native test/example candidate maps, evals, verification reports, final reports, and human-review artifacts.
- A backend-classified native candidate map and backend verification plan that
  determine the minimum CPU/GPU/accelerator environment set.
- A private `ok`, explicitly accepted `partial`, or `failed`
  environment-preparation handoff when the Python inspection environment had
  to be created automatically.
- A handoff to `verify-repo-skill` that distinguishes public skill content, artifact location, repo evidence used, generated sub-skills, integration artifacts, coverage/depth matrix, native test/example candidates, long-tail gaps, and review rubrics.
- After `verify-repo-skill` completes and import is approved by the user or safely authorized by `auto-import` with no required-backend block, a DisCo user import under `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/` plus an updated sibling live `repo-skills-router` entry that DisCo Researcher can use in a new session without any cross-agent export.
