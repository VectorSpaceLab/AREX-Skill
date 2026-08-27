# Planning and Writing the Generated Skill

## Purpose

Read this reference after repository evidence discovery and installed-package inspection. It covers sub-skill boundaries, content inventory, coverage/depth planning, generated file writing, and common anti-patterns.

## Identify Sub-Skills

Split the repo into sub-skills only when the boundaries are useful for future agents. Good sub-skills usually map to:

- Distinct user workflows.
- Separate packages or major modules.
- Different CLIs, services, pipelines, or task families.
- Capabilities that require different references or scripts.

Keep sub-skills as functionally independent as possible. Do not group many orthogonal or relatively independent capabilities under one sub-skill just because they live near each other in the source tree.

Avoid creating sub-skills for tiny helper modules, internal-only implementation details, or arbitrary source folders.

Start from realistic task routes, not from source directory names alone. A
separate sub-skill is usually warranted when a capability is a high-frequency
user workflow with its own inputs, outputs, commands, validation steps, optional
dependencies, or failure modes. Examples include data preparation before
training, serving/runtime deployment, evaluation, environment/data-layout
setup, and maintainer workflows when those are first-class parts of the repo.

Do not hide a core workflow inside a neighboring sub-skill just because it is
upstream or downstream of that workflow. If users commonly ask for
preprocessing, validation, conversion, command generation, or data-layout
checks as standalone tasks, make those tasks discoverable from the root router
or a focused sub-skill. Conversely, merge routes when several thin branches
would force future agents through extra navigation without adding distinct
guidance, scripts, or references.

Plan the sub-skill structure before generating detailed content. The structure
plan must include:

- Root skill id and each planned sub-skill id.
- The user-facing responsibility of each sub-skill.
- Boundary notes explaining what belongs in the sub-skill and what is excluded
  or routed elsewhere.
- Evidence sources assigned to that sub-skill.
- Public APIs, CLIs, commands, configs, data formats, examples, tests, and
  troubleshooting facts that the sub-skill is expected to cover.
- Source scripts assigned to that sub-skill, with a decision for each useful
  script: copy, adapt, wrap, reference-only, or exclude with a reason.
- Troubleshooting surfaces assigned to that sub-skill, including install/import
  failures, optional dependency or backend issues, data/config validation
  errors, CLI/API misuse, and workflow-specific failure modes.
- Native test/example candidates that should later validate or stress that
  sub-skill after whole-skill integration.
- One or two new difficult synthetic usability case ideas for that sub-skill,
  separate from original repo-native tests. These should stress edge cases,
  error recovery, integration constraints, or expert API/CLI usage that the
  original repo tests may not cover.
- Expected bundled references and scripts.
- Review rubrics the main agent will use before accepting that sub-skill.
- Cross-reference requirements between sub-skills and repo-level references.

At this phase, do not draft full sub-skill prose. The structure is the contract
used by the dynamic workflow generation phase.

Sub-skill ids are part of that contract. Use canonical lowercase-hyphen ids
such as `training`, `data-preparation`, or `model-serving`. The directory
basename under `sub-skills/<id>/`, the sub-skill `SKILL.md` frontmatter `name`,
the `agent(..., { subSkill: "<id>" })` option in workflow calls, coverage/depth
matrix locations, review notes, and usability case target ids must match
exactly. Because the root skill id already carries the repository identity,
avoid repeating the repo name inside sub-skill ids unless two sibling routes
would otherwise be ambiguous.

The main agent owns this structure. Choose boundaries that make the final skill
easy for future agents to use: capabilities should be discoverable from natural
user requests, enough detail should live near the route that needs it, and
cross-links should be explicit when a workflow spans sub-skills. Do not let a
subagent redefine the planned structure, rename its sub-skill, or move files
outside its assigned subtree without main-agent approval.

## Built-In Workflow Generation

When running inside DisCo, use the built-in `workflow` tool to coordinate
sub-skill extraction and review:

1. Create one workflow phase or branch per planned sub-skill. Pass the planned
   sub-skill id in every relevant `agent()` call's `subSkill` option,
   such as `agent(prompt, { label: "draft workflow", subSkill: "training" })`,
   so the live workflow tree shows which sub-skill each subagent is writing or
   reviewing. Assign each branch to a subagent with a complete sub-skill brief,
   not a short generic prompt.
2. Run independent sub-skill branches in parallel. Each subagent should write
   only its assigned sub-skill files under the planned `sub-skills/<id>/`
   subtree, including linked `references/` and `scripts/` when needed.
   The branch result returned from `agent()` is only a review handoff. It should
   list files created or updated, evidence used, checks performed, known gaps,
   and questions. It must not contain full Markdown or script bodies that the
   main agent must later copy into the skill tree.
3. The main agent reviews every branch result before accepting it. Check
   the actual files the subagent wrote for correctness against source and installed-package evidence, identifier
   consistency, self-containment, routing quality, depth, bundled
   script/reference coverage, privacy, and link integrity.
4. When a result fails review, send precise feedback back to the same branch or
   subagent and require a revision. Do not silently patch large sub-skill bodies
   in the main agent unless the issue is small and mechanical.
5. After all sub-skills pass review, stop the parallel branch phase and run a
   single main-agent integration phase. The main agent writes the root
   `SKILL.md`, repo-level `references/`, and repo-level `scripts/`, reconciles
   all branch handoffs, and performs a whole-skill integration pass before
   handing the skill to verification.

When these workflow skills are copied into another agent without DisCo's
built-in workflow tool, follow the same coordination model manually: delegate
to subagents when available, keep independent sub-skill work isolated, review
each result against the rubrics, and iterate before integrating the root skill.

### Subagent Brief Template

For each sub-skill branch, include a brief with enough context for the subagent
to produce a complete, usable result without guessing the main agent's intent.
Use this shape and fill it with repo-specific facts:

```text
You are drafting one sub-skill for the generated <root-skill-id> repo skill.

Target identity:
- Sub-skill id: <canonical-lowercase-hyphen-id>
- Output subtree: <generated-skill-dir>/sub-skills/<id>/
- Frontmatter name: exactly <id>
- Do not include the repo name in this sub-skill id unless this brief says so.

Responsibility:
- User-facing tasks this sub-skill must enable.
- Natural trigger phrases and user roles it should support.
- Inputs, outputs, commands, APIs, configs, data layouts, and failure modes it
  must cover.

Boundaries:
- Include these capabilities: <list>.
- Exclude or route these capabilities elsewhere: <list with owning sub-skill>.
- Required cross-links to root or sibling sub-skills: <list>.

Evidence to use:
- Source/docs/examples/tests/config paths: <relative paths>.
- Source script inventory rows assigned here: <copy/adapt/wrap/reference-only/exclude decisions and targets>.
- Installed-package facts already verified: <signatures, CLI help, entry
  points, versions, optional dependencies>.
- Troubleshooting evidence and failure modes to cover: <errors, edge cases,
  common misconfigurations, optional dependency failures, invalid inputs>.
- Facts that still need direct verification before writing: <list>.
- New difficult usability cases to support later verification: <1-2 synthetic
  scenarios that go beyond original repo test cases and name the intended
  assertions, fixtures, or failure signals>.

Required output:
- `SKILL.md` as a focused router with valid YAML frontmatter.
- References to create under `references/`, with the purpose of each file.
- Scripts/templates to create under `scripts/`, with safe help or fixture
  checks to run when practical.
- A `references/troubleshooting.md` file, or a specific linked troubleshooting
  section in another nearby reference, whenever this sub-skill owns install,
  data/config, CLI/API, optional dependency, backend, or workflow failure modes.
- Any provenance notes or source-artifact-to-bundled-helper mapping needed by
  this sub-skill.
- Write these files directly to the output subtree before returning. Do not
  return their full contents as JSON, Markdown, or prose for the main agent to
  write later.

Quality bar:
- Future agents should complete the common workflows using this sub-skill and
  its bundled references/scripts without reopening the original repository.
- Guidance must be concrete: commands, options, data assumptions, API names,
  expected outputs, validation steps, and troubleshooting signals.
- Claims must cite or clearly derive from the assigned evidence.
- Runtime links must point inside the generated skill tree.
- Do not mention private environment paths, local checkout paths, or check-only
  artifact directories.

Return:
- Files created/updated.
- Evidence consulted.
- Verification performed.
- Proposed difficult synthetic usability cases for this sub-skill, including
  why the original repo tests/examples are insufficient on their own.
- Known gaps or questions for main-agent review.
```

If a subagent returns only a README-style summary, a few vague bullets, a JSON
object containing draft file bodies, or a sub-skill that lacks the expected
references/scripts on disk, treat that as a failed branch. Send a revision
prompt that names the missing workflows, evidence, files, commands, examples,
or troubleshooting details and requires the subagent to write the assigned
runtime files directly.

### Main-Agent Review Rubric

Before accepting a sub-skill branch, the main agent must verify these points
against the planned structure and evidence:

- Identity: `sub-skills/<id>/SKILL.md` exists, frontmatter `name` is exactly
  `<id>`, the id is lowercase-hyphen, and the id matches the workflow
  `subSkill` option and coverage/depth matrix.
- Direct file ownership: the branch created or revised the expected files on
  disk under `sub-skills/<id>/`; the main agent is not expected to transcribe
  full sub-skill content from a returned JSON/text draft.
- Scope: included capabilities are covered, excluded capabilities are not
  duplicated, and cross-links route shared workflows to the correct owning
  sub-skill or repo-level reference.
- Usability: a future agent can answer novice and expert prompts for the
  assigned workflow from the sub-skill plus linked bundled files.
- Depth: workflows include concrete steps, commands, parameters, configs,
  inputs/outputs, data/schema assumptions, validation checks, and common
  failure handling when those facts exist in the evidence.
- Script bundling: useful repo-maintained scripts assigned to this branch were
  copied, adapted, or wrapped into the appropriate bundled `scripts/` location,
  or were marked `reference-only`/`exclude` with a concrete safety, size,
  environment, generated/vendor, credential, or relevance reason.
- Troubleshooting: expected failure modes are covered in the nearest
  `references/troubleshooting.md` or clearly linked troubleshooting section,
  with symptoms, likely causes, and concrete recovery or validation steps.
- Evidence: public API, CLI, config, and runtime claims are backed by source,
  docs, tests, examples, or installed-package inspection instead of guesswork.
- Self-containment: no runtime instruction depends on opening, linking, or
  executing original repo files; relevant repo artifacts are distilled into
  bundled references or adapted into bundled scripts.
- Executability: any bundled script or template is linked from the nearest
  `SKILL.md`, has safe defaults, and has at least a help/parser/tiny-fixture
  check when practical.
- Structure: `SKILL.md` remains router-like, and bulky API tables, long
  examples, troubleshooting matrices, or workflow details live in nearby
  references or scripts.
- Privacy and artifact boundary: generated runtime files do not mention local
  Python executables, conda prefixes, machine-specific paths, review/test
  artifacts, or private credentials.

## Whole-Skill Integration Gate

Do not hand a repo skill to `verify-repo-skill` immediately after
parallel sub-skill branches finish. A main-agent integration pass is mandatory
because subagents optimize local sub-skill quality and can miss cross-skill
gaps, duplicate guidance, conflicting terminology, broken root routing, or
long-tail omissions.

During integration, read every accepted sub-skill, reference, script, and
subagent handoff together. Then write or update:

- Root `SKILL.md` route map and install/import guidance.
- Repo-level `references/` and `scripts/` shared across sub-skills.
- `references/repo-provenance.md`.
- Review/test artifact `reports/integration/integration-notes.md`.
- Review/test artifact `reports/integration/coverage-depth-matrix.md`.
- Review/test artifact `reports/integration/source-script-import-map.md`.
- Review/test artifact `reports/integration/troubleshooting-coverage-map.md`.
- Review/test artifact `reports/integration/long-tail-gap-register.md`.
- Review/test artifact `reports/integration/native-ground-truth-candidates.md` or
  equivalent JSON/Markdown candidate map when native examples/tests were found.
- Review/test artifact `reports/integration/difficult-case-plan.md` that
  records the one or two proposed difficult cases for each sub-skill and the
  final one or two integrated difficult cases for the whole skill.

The integration notes should record:

- Accepted sub-skills and their owners.
- Capabilities each sub-skill covers.
- Evidence sources used by each sub-skill.
- Native test/example candidates associated with each capability.
- Cross-references added or changed by the main agent.
- Source scripts copied, adapted, wrapped, left reference-only, or excluded,
  with their final owner and rationale.
- Troubleshooting coverage by root or sub-skill owner, including remaining
  known gaps.
- Duplicate or conflicting content removed.
- Gaps that were fixed before verification.
- Remaining long-tail gaps and why they were not included.
- Difficult test coverage plan: per-sub-skill synthetic cases, native evidence
  they complement, and integrated whole-skill cases selected from repo-native
  tests/examples or explicitly synthesized when no repo-native candidate fits.

The integration gate must check:

- Every planned primary workflow has a root route or focused sub-skill.
- Every non-trivial support workflow is reachable from a root route or nearest
  owning sub-skill.
- Every documented maintainer workflow selected for extraction has focused
  guidance.
- Every generated sub-skill links to its nearest references/scripts.
- Repo-level references/scripts are shared material, not a dumping ground for
  sub-skill-specific depth.
- Every useful source script selected for extraction is either bundled in root
  or sub-skill `scripts/`, or has a documented `reference-only`/`exclude`
  rationale in the source script import map.
- Every primary workflow and non-trivial support workflow has actionable
  troubleshooting guidance for likely install/import, optional dependency,
  data/config, CLI/API, backend, or workflow errors.
- Route descriptions use consistent repo terminology and are broad enough for
  natural user requests.
- Cross-links resolve within the generated runtime skill directory.
- Runtime skill content does not link to original repo docs, examples,
  notebooks, tests, scripts, or absolute checkout paths.
- The native test/example candidate map still matches the integrated
  capability owners.
- Every sub-skill has one or two planned difficult synthetic cases in addition
  to any original repo-native tests selected for that sub-skill.
- The whole-skill plan includes one or two integrated difficult cases that
  exercise multiple sub-skills or root routing plus a sub-skill. Prefer
  adapting existing repo tests/examples for these integrated cases; create new
  synthetic cases only when the native candidate map lacks a suitable
  cross-capability scenario.

If this gate finds a missing or weak area, send targeted feedback to the
relevant subagent or run a focused revision pass. Do not cover substantial
sub-skill gaps by patching only the root router; the owning sub-skill must be
deep enough to complete realistic tasks.

## Build a Content Inventory

Before writing generated skill files, create a short content inventory from the research:

- User-facing workflows discovered in README, docs, examples, tests, notebooks, CLIs, and package metadata.
- Important public APIs, classes, functions, config objects, command-line entry points, and runtime facts verified from the installed package.
- Existing repo scripts or example programs that future agents could reuse only after they are copied, adapted, or wrapped into the generated skill.
- Repeatable support workflows that make the main workflows usable, such as
  data validation, hard-negative or sample generation, schema conversion, data
  splitting, command construction, data-layout checks, optional dependency
  checks, and environment smoke tests.
- Public constraints, optional dependencies, required services, credentials, data files, Python versions, package extras, or hardware assumptions documented by the repo or verified from package metadata.
- Contributor or maintainer rules from files such as `AGENTS.md`,
  `CONTRIBUTING.md`, docs style guides, duplicated-code policies, paper or
  citation indexes, and test-selection guidance when the repo exposes
  maintainer-facing workflows.
- Troubleshooting knowledge from issues in docs, test failure patterns, error messages, or user-provided notes.
- Failure modes inferred from public APIs, CLIs, configs, optional dependency
  branches, validation code, exception messages, tests, examples, and scripts,
  even when the repo does not have a dedicated troubleshooting document.

## Coverage/Depth Matrix

Turn the inventory into a coverage/depth matrix before writing:

```text
Capability | Kind | Evidence source | Native candidate | Output location | Depth check | Verification expectation
inference CLI | primary workflow | README, tests/test_cli.py | pytest tests/test_cli.py -q | sub-skills/inference + references/cli-reference.md | enough commands, flags, inputs, outputs, and troubleshooting to use without reopening repo docs | native selected or help-only CLI check
training data validation | support workflow | docs/data.md, scripts/validate.py | python scripts/validate.py --help | sub-skills/data-preparation + scripts/validate_jsonl.py | bundled validator exists, examples match script flags, invalid data failures are clear | synthetic assertion case plus parser/help check
model training | primary workflow | docs/training.md, examples/train.py | examples/train.py marked skip-expensive | sub-skills/training + scripts/train_smoke_test.py | enough config, data format, API, and failure notes to run/adapt safely | native skipped with reason, synthetic fixture case required
repo maintenance | maintainer workflow | AGENTS.md, CONTRIBUTING.md, tests | pytest focused maintainer tests if safe | sub-skills/repo-development + references/contributor-guidance.md | enough policy and test guidance to edit duplicated or generated areas safely | selected native or documented skip
```

Also maintain a source script import map:

```text
Source script | Decision | Bundled target | Owner | Reason | Check
scripts/validate.py | adapt | sub-skills/data-preparation/scripts/validate_jsonl.py | data-preparation | reusable validator, remove repo-local imports | --help + invalid fixture
scripts/train.py | reference-only | sub-skills/training/references/workflows.md | training | long training side effects and repo-local config assumptions | synthetic config case
```

And maintain a troubleshooting coverage map:

```text
Failure surface | Evidence | Owner | Runtime location | Recovery guidance | Verification expectation
optional CUDA backend missing | imports/tests/docs | sub-skills/inference | references/troubleshooting.md | detect ImportError, select CPU fallback or install extra | assertion case checks missing-backend advice
invalid JSONL training data | scripts/validate.py, tests | sub-skills/data-preparation | scripts/validate_jsonl.py + references/troubleshooting.md | run bundled validator and fix missing fields | tiny invalid fixture
```

Use this matrix to catch:

- Breadth failure: a public workflow, CLI, API family, documented example, test-backed behavior, or major module has no place in the generated skill tree.
- Depth failure: a capability is named, but the sub-skill lacks enough workflow steps, parameters, examples, bundled scripts, data/config assumptions, or troubleshooting for a future agent to use it without reopening source code or original docs.
- Misclassified workflow failure: a core workflow is buried as a paragraph in a
  different sub-skill, or many tiny routes exist without distinct user
  triggers, scripts, or references.
- Tooling failure: a repeatable validation, command-building, data-layout,
  environment, or smoke-test task is described only in prose even though a safe
  bundled script, template, or checker could make it directly executable.
- Script import failure: a useful repo-maintained script is reduced to Markdown
  prose without a concrete reason instead of being copied, adapted, or wrapped
  into the generated skill tree.
- Troubleshooting failure: a major workflow lacks symptoms, likely causes, and
  concrete recovery steps for predictable user-facing failures.
- Validation failure: a capability has no realistic assertion-backed usability
  case and no native test/example candidate, or the native candidate exists but
  the generated skill has no owner for it.

Classify each inventory item as one of:

- `primary workflow`: a task users naturally ask for directly, such as
  inference, training, evaluation, serving, local prediction, data preparation,
  or Docker/data setup.
- `support workflow`: a task that makes a primary workflow reliable, such as
  validation, conversion, command generation, optional dependency checks,
  environment checks, or data-layout checks.
- `maintainer workflow`: repo editing, contributor policy, duplicated
  implementation rules, documentation updates, focused tests, or release
  maintenance.
- `minor detail`: helper behavior that can live inside a nearby reference
  instead of getting a route.

Every `primary workflow` must have a root route or focused sub-skill. Every
non-trivial `support workflow` must have either a route from the nearest
sub-skill or an explicitly linked bundled reference/script. Every
`maintainer workflow` that the repo documents as important should have focused
guidance instead of being lost inside a generic troubleshooting page.

Every capability row should also name the best available validation path. Use
native examples/tests as ground-truth candidates when safe, and use
assertion-backed synthetic usability cases when native execution is unsafe,
expensive, or not available. A native candidate that is skipped for safety can
still strengthen coverage by anchoring the synthetic case to real repo
behavior.

## Target File Tree

Draft the target file tree before writing final bodies. For every planned file, include one sentence explaining its purpose:

```text
repo-name/
  SKILL.md - router, install, sub-skill map
  references/repo-provenance.md - source repository snapshot and refresh baseline
  references/troubleshooting.md - cross-cutting install/import/runtime failures
  scripts/check_env.py - verifies importability and optional backend availability
  sub-skills/inference/SKILL.md - routes inference workflows
  sub-skills/inference/references/api-reference.md - verified inference signatures and parameters
  sub-skills/inference/scripts/smoke_test.py - minimal inference smoke test
```

Map each inventory item to exactly one output location. If an item is tightly coupled to one sub-skill, place it under that sub-skill's `references/` or `scripts/`, not the repo root. Use repo-level `references/` and `scripts/` only for material shared across multiple sub-skills.

When the inventory mentions an original repo path, the target file tree must also name the bundled skill file that replaces it. If a repo script is too large, unsafe, or environment-specific to bundle, extract the reusable parts into a smaller skill script or a reference recipe, and note any omitted side effects or prerequisites.

Use this mapping for every source repo script, example, notebook, tool, or config
that remains relevant:

```text
Source repo artifact | Runtime need | Bundled skill replacement | Link owner
scripts/train.py | safe training smoke-test logic | sub-skills/training/scripts/train_smoke_test.py | sub-skills/training/SKILL.md
examples/infer.py | inference recipe, not full script | sub-skills/inference/references/workflows.md | sub-skills/inference/SKILL.md
scripts/hn_mine.py | data-preparation recipe and safe argument validation | sub-skills/data-preparation/scripts/mine_hard_negatives.py | sub-skills/data-preparation/SKILL.md
```

If a source repo artifact has no bundled replacement, do not tell future agents
to open, run, or adapt it. It may remain in `references/repo-provenance.md` as
evidence, but not as a runtime dependency.

If a useful repo-maintained script is small and safe enough to preserve, prefer
copying it with minimal normalization over rewriting it as prose. If direct
copying would preserve unsafe side effects, repo-local imports, absolute paths,
large downloads, or credential assumptions, adapt or wrap the safe reusable
parts instead. Put script-specific helpers under the owning sub-skill's
`scripts/`; put only genuinely shared helpers under the root `scripts/`.

When a bundled script adapts or renames a source repo artifact, distinguish the
two names precisely. Do not say the source repository provides the bundled
wrapper's filename unless it actually does. In references, label tables as
`Source repo artifact` versus `Bundled skill helper` so future agents do not
try to run a nonexistent repo path.

## Write Generated `SKILL.md` Files

For the generated repo skill:

- Keep the root `SKILL.md` concise and router-like.
- Include package installation instructions, required extras, editable install notes when useful, public prerequisites, and a minimal import check.
- Link `references/repo-provenance.md` from the root `SKILL.md` with guidance
  to read it when checking whether the skill matches the current repository or
  before running `refresh-repo-skill`.
- Cover all user-facing repo capabilities across the root skill, sub-skills, references, and scripts.
- Give every sub-skill a focused `SKILL.md` with clear trigger scenarios.
- Make each sub-skill frontmatter `name` exactly match its `sub-skills/<id>/`
  directory basename. Keep sub-skill ids focused on the capability, not the
  repository name, unless disambiguation within the same root skill requires it.
- Put long API notes, usage examples, and domain references in `references/*.md`.
- Include `troubleshooting.md` in repo-level or sub-skill `references/` for
  every primary workflow or non-trivial support workflow that has predictable
  install/import, optional dependency, backend, data/config, CLI/API, or
  runtime failure modes. If no dedicated file is justified, include a linked
  troubleshooting section in the nearest workflow/config/API reference and
  record why that is sufficient.
- Put reusable checks, introspection helpers, adapted repo examples, smoke tests, or workflow automation in `scripts/`.
- Use the repo's own terminology consistently.
- Prefer verified package facts over inferred behavior.

Every generated root and sub-skill `SKILL.md` must include valid YAML
frontmatter:

```markdown
---
name: repo-or-sub-skill-name
description: "Specific third-person description with trigger terms broad enough for natural user requests."
disable-model-invocation: true
metadata:
  disco-role: operating
---
```

Always double-quote `description` values, even when the text does not contain
YAML-sensitive characters. If the quoted string itself contains double quotes,
escape them as `\"`. Quote other string values with double quotes whenever they
contain a colon, hash, bracket, brace, leading special character, or other
YAML-sensitive content.

Generated repo skills use `repo-skills-router` for discovery. Include
`disable-model-invocation: true` in every generated root and sub-skill
frontmatter by default so bulk imported repo skills do not flood DisCo
Researcher's or compatible exported agents' model-visible skill lists. Also include
`metadata.disco-role: operating` in every root and sub-skill so the generated
skill graph is visible in Researcher mode and excluded from Creator mode. The
live `repo-skills-router` has the same `operating` role and follows the user's
DisCo router policy: the updater must preserve either an enabled router or
`disable-model-invocation: true`. Canonical and exported routers remain
model-visible. Codex exports add target-side
`agents/openai.yaml` policy files during `import-repo-skills-to-agent`; do not
add those files to the source repo skill during creation.

## Write Repo Provenance

Every generated repo skill must include `references/repo-provenance.md`. This
file is the baseline used later by `refresh-repo-skill` to decide whether
the skill is aligned with the current repository.

Use this shape:

````markdown
# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "repository": {
    "name": "project-name",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "40-character-sha-or-null",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "distribution-name",
      "version": "package-version-or-null",
      "import_names": ["package_name"]
    }
  ],
  "evidence": {
    "source_roots": ["src/package_name"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["configs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ, run
  `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit,
  run `refresh-repo-skill`.
````

Use `null` for unknown values. Keep paths relative to the repository root. Do
not include local absolute paths, conda prefixes, virtualenv names, Python
executables, cache paths, API keys, or `pip show Location` values. If the remote
URL is private or unclear, write `omitted-private-or-unknown`.

## Write References

For `references/`:

- Create reference files before or alongside the nearest `SKILL.md`, not as an afterthought.
- Use descriptive names such as `api-reference.md`, `workflows.md`, `cli-reference.md`, `configuration.md`, `data-formats.md`, `model-overview.md`, `benchmarks.md`, and `troubleshooting.md`.
- Structure reference files for future agent use: short purpose, when to read, verified facts, examples, and gotchas.
- Prefer distilled, task-oriented reference material over verbatim copies of long repo docs.
- Keep example commands copyable against the generated skill tree. If an
  example invokes a bundled helper, verify every shown option name against that
  helper's parser or shell interface. Prefer the helper's actual spelling
  consistently, such as hyphenated `--input-file` or underscored
  `--input_file`, rather than mixing styles between docs and scripts.
- For public API, CLI, configuration, data schema, optional dependency, and
  backend facts, include the source of verification in prose when useful: source
  file, installed signature inspection, CLI help, schema check, test, or docs.
  Do not present broad parameter lists from memory.
- Troubleshooting references should be actionable, not generic. For each covered
  failure mode, include observable symptoms or error fragments, likely causes,
  the bundled script/reference to use next, concrete recovery steps, and when to
  stop because credentials, network, hardware, or large data are required.

## Write Scripts

For `scripts/`:

- Prefer copying, adapting, or wrapping proven repo scripts and examples over
  inventing new helpers from scratch. Do not discard a useful script into
  prose-only Markdown when it can reasonably become a safe bundled helper.
- Bundle every script that a generated `SKILL.md` tells future agents to run.
- For every useful source script selected in the source script inventory, either
  create the planned bundled script or record the reference-only/exclude
  rationale in the integration artifacts.
- Ensure linked script paths resolve inside the generated skill directory, not inside the original repo checkout.
- If a generated Markdown file links to a local runtime file, verify that the
  link resolves within the generated skill directory and that the target exists.
- Include a shebang when appropriate and a top-level comment or docstring with purpose, prerequisites, and example invocation.
- Keep scripts deterministic and safe by default. Avoid network calls, downloads, training runs, destructive writes, or credential use unless the user explicitly wants that behavior.
- Link each script from the nearest `SKILL.md` and say whether future agents should run it, read it, or adapt it.
- Design diagnostic scripts to be runnable from arbitrary current working
  directories. If a script needs to import the target package from a local
  checkout, accept an explicit `--repo-root` or similar option and add that path
  to `sys.path` inside the script before importing. Do not rely on the script's
  own directory being inside the original repo checkout.
- When a script wraps a repo CLI or imports optional modules, catch common
  `ImportError` and missing-executable failures and report the missing package,
  extra, binary, or backend explicitly. A diagnostic helper should explain
  "missing optional dependency" instead of leaving a raw traceback as the main
  user interface.
- For every bundled script or template, run at least a safe help, parser, or
  tiny fixture check when practical. Verify that documented examples use exactly
  the accepted option names and that scripts return non-zero for genuine
  validation failures.

## Anti-Patterns

Avoid:

- A single-file repo skill for a repo with multiple user-facing workflows.
- A 400+ line sub-skill `SKILL.md` with thin or missing `references/`.
- A README summary that lacks verified API details, practical workflows, scripts, or troubleshooting.
- A prose-only description of a useful repo-maintained script that could have
  been safely copied, adapted, or wrapped into `scripts/`.
- Missing troubleshooting coverage for predictable install/import, optional
  dependency, data/config, CLI/API, backend, or workflow errors in a primary
  workflow.
- Reference links that point to files that were not created.
- Instructions that require future agents to run or read scripts, docs, examples, notebooks, or configs from the original repo checkout instead of bundled skill files.
- Mentions of the user's temporary Python environment.
- Publishing Python cache files such as `__pycache__/`, `*.pyc`, or
  `*.pyo`, downloaded caches, build outputs, or other generated runtime debris
  inside the skill directory.
- `evals/`, `review/`, `tests/`, verification reports, human-review notes,
  publication checklists, prompt samples, or other check-only artifacts inside
  the generated runtime skill directory. Put concrete cases under the
  review/test artifact directory's `test-cases/` subtree and reports under its
  `reports/` subtree instead.
- Generated root or sub-skill `SKILL.md` frontmatter missing
  `disable-model-invocation: true`.
- Generated root or sub-skill `SKILL.md` frontmatter missing
  `metadata.disco-role: operating`.
- A canonical or exported `repo-skills-router` `SKILL.md` that includes
  `disable-model-invocation: true`. Only a live DisCo router may contain this
  field after an explicit user `router disable` command.
- Uppercase, underscored, dotted, spaced, or otherwise invalid skill identifiers in generated directory names, frontmatter `name` fields, or `reports/self-refine/evals.json` `skill_name` under the review/test artifact directory.
- Sub-skill frontmatter `name` values that differ from the `sub-skills/<id>/`
  directory basename, workflow `subSkill` option, or usability target id.
- Sub-skill ids that redundantly repeat the root repo skill id, such as
  `repo-name-training`, when `training` would be clear inside that root skill.
- Invalid YAML frontmatter, especially unquoted string values containing colons.
- Copying entire docs pages into `SKILL.md` instead of restructuring them for agent use.
