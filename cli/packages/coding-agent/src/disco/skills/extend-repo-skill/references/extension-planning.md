# Extension Planning

## Purpose

Read this before editing an existing skill. The goal is to preserve working guidance, identify the precise coverage gap, and decide where new material belongs.

## Capture Scope

Clarify or infer:

- The exact existing skill directory.
- Whether that path is a live managed DisCo repo skill and, if so, the external
  working-copy path with the same `<skill-id>` basename.
- The repository path and package name.
- The requested extension: new capability, deeper workflow, updated API, new CLI, new model/backend, new troubleshooting path, or improved tests/verification.
- Whether the change should be public runtime skill content, usability-test coverage, evaluation artifacts, or benchmark artifacts.
- The review/test artifact directory. If the user did not specify one, use
  `<repository-path>/skills/tests/<skill-id>/`, with concrete cases under
  `test-cases/` and reports under `reports/`.
- Whether the update is additive or replaces stale guidance.
- Whether the exact managed target already exists and therefore requires
  explicit overwrite approval before import.
- Whether the request is really asking for a high-frequency support workflow,
  such as data preparation, validation, conversion, command generation,
  data-layout checks, optional dependency diagnostics, environment checks, or
  maintainer guidance. These often deserve their own route or bundled helper
  even when they support an existing primary workflow.

Ask for clarification only when writing files would otherwise affect different skill directories or incompatible capabilities.

## Audit Current Skill

Before editing, build a short current-state map:

```text
Current area | Evidence | Keep/change decision
root SKILL.md | routes install, inference, training | keep install; add new deployment route
sub-skills/training | has workflow reference but no data validation script | add validation script and troubleshooting
test-cases/sub-skills/training/basic | covers happy path | add invalid-config troubleshooting case
```

Inspect:

- Root and sub-skill `SKILL.md` frontmatter, descriptions, routing, and reference/script links.
- Existing `references/`, `scripts/`, and `sub-skills/`.
- Existing usability test cases under the review/test artifact directory's
  `test-cases/` subtree.
- Optional self-refine artifacts when they exist under the review/test artifact
  directory's `reports/self-refine/` subtree, without treating them as runtime
  documentation.
- Prior verification reports or benchmark artifacts when available, preferably
  under the review/test artifact directory's `reports/` subtree.

Use the current skill to avoid duplicate content. If a capability already exists
but is shallow, deepen it in the resolved source or external working copy instead
of creating a parallel section. Never use this rule to edit a live managed copy
under `<agent-dir>/skills/repositories/repo-skills/` outside the importer transaction.

## Gather Targeted Repository Evidence

For the requested extension, inspect enough repository evidence to support concrete guidance:

- Source code for public APIs, signatures, configuration objects, error paths, and object relationships.
- Installed package inspection for importability, signatures, docstrings, CLI help, and safe smoke tests.
- Docs, examples, notebooks, and tests for intended workflows and edge cases.
- Configs, schemas, fixtures, and CI for data formats, optional dependencies, and operational assumptions.
- Repo scripts, examples, and tools that can be safely wrapped into bundled
  skill helpers for validation, data preparation, command generation,
  data-layout checks, optional dependency checks, environment checks, and smoke
  tests.
- Existing repo-local skills for conventions and known troubleshooting.

Do not ask the user to enumerate docs/source/examples unless automatic discovery cannot distinguish signal from unrelated generated or vendored content.

## Extension Plan

Write a concise plan before editing:

```text
Requested capability | Evidence source | Existing location | Edit action | Verification/test
streaming inference CLI | docs/serve.md, package.cli:main --help | sub-skills/inference | add cli-reference.md section and route from SKILL.md | add inference-streaming-cli case
```

Each capability should map to exactly one primary runtime location. If it needs depth, place the depth in the nearest bundled reference or script and keep `SKILL.md` router-like.

When adding or changing a bundled helper, the plan must include how its
documented examples will be checked against the actual parser or command
interface. If the helper wraps or renames a source repo script, record both the
source repo artifact and the bundled helper path so the public skill does not
misrepresent one as the other.

## Quality Checks Before Editing

Proceed only when the plan answers:

- Which existing guidance must remain unchanged?
- Which claims are stale, missing, or too thin?
- Which new files will be public skill content?
- Which new files are review/test artifacts?
- Are all new review/test artifacts planned under the review/test artifact
  directory's `test-cases/` or `reports/` subtree rather than inside the runtime
  skill directory?
- Will copyable commands in the edited references match the new or updated
  bundled scripts' real option names and paths?
- What usability prompt will prove the new capability is usable?
- What regression-sensitive prompt will prove existing behavior was not broken?
