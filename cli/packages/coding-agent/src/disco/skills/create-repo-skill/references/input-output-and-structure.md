# Input, Output, and Structure

## Purpose

Read this reference before writing any generated skill files. It defines the required inputs, optional inputs, path resolution rules, generated skill layout, and content placement rules.

## Required and Optional Inputs

Before creating files, confirm:

- Repository path.
- Optional Python executable or environment activation command for temporary inspection only.
- Optional environment prefix/path to use if the inspection environment must be prepared automatically.
- Installed package name if it differs from the repo name.
- Target skill output path, if the user has a preference.
- Review/test artifact output path, if the user has a preference.
- Whether the skill should be personal, project-local, or exported as a standalone skill directory.
- Extra skill extraction requirements from the user, such as required workflows,
  excluded areas, preferred sub-skill names, special review criteria, or known
  capability priorities.
- Delegated decision policy. Use `extractionScope: agent-decide` when the user
  says `auto decide`, `agent decide`, asks the agent to choose the scope, or
  says not to ask for scope confirmation. Use `importAfterVerification:
  auto-import` when the user says `auto import`, `default import`, or says not
  to ask about importing the verified skill. Otherwise default both fields to
  `ask`.
- Known troubleshooting notes, common failures, confusing errors, or operational pitfalls that should be captured.

If the Python environment is missing or the package is not installed, do not
stop just to ask the user for a preinstalled environment. Resolve a private
default environment prefix up front, but do not prepare the environment until
after repository structure analysis has produced a confirmed include/exclude
evidence map. If the user did not provide a prefix, choose a private default
under `$DISCO_CODING_AGENT_DIR/envs/<chosen-skill-id>-inspection` when that
variable is set, otherwise under
`~/.disco/agent/envs/<chosen-skill-id>-inspection`. After the user confirms
or corrects the repository structure analysis, or after the agent confirms it
under an explicit `extractionScope: agent-decide` policy, use the sibling
`prepare-repo-skill-env` skill to create or repair an inspection environment
and verify the repo package. The prepare-env skill prefers Conda when available,
can use micromamba, venv, or uv when appropriate, and runs explicit terminal
commands for environment creation, package installation, and verification. On
machines with no suitable manager or Python, it identifies the required
host-level installation and asks before making that change unless the user
already authorized it. Continue normally from an `ok` handoff; use a `partial`
handoff only under the explicit limitation rule below, and do not continue from
`failed`.

When calling `prepare-repo-skill-env`, pass along the
confirmed extraction scope:

- Included directories and the workflows they represent.
- Excluded directories and why they are not needed for skill extraction.
- Package metadata, optional dependency groups, requirements files, and install
  variants discovered during structure analysis.
- The native test/example candidate map with backend requirement, backend
  criticality, CPU substitution, dependency variant, hardware prerequisites,
  and verification expectation for candidates owned by included workflows.
- The derived backend verification plan: required, optional, and alternative
  backends; the minimum environment set; hardware probes; preparation smoke
  checks; final native cases; and the consequence of unavailable required
  hardware.
- User requirements that affect dependency selection, such as a required
  backend, extra, CLI, API family, or directory that must be covered.

This scope lets environment preparation install the minimum dependency set
needed for the selected repo areas instead of installing all extras, all
requirements files, or packages tied only to excluded directories.
"Minimum" means the smallest environment set that covers every required
backend, not a CPU-only environment by default. One GPU-capable environment may
also cover CPU checks; use multiple prefixes only for conflicting variants or
an independently selected CPU fallback claim.

Treat the prepare-env handoff states explicitly:

- `ok`: continue normally and preserve the backend plan for final verification.
- `partial`: continue drafting only after the user explicitly accepts the exact
  required-backend limitation. Preserve it as a blocking final-verification
  item and disable `auto-import`.
- `failed`: stop, repair the environment, or ask the user to narrow the
  extraction scope. Do not reinterpret a CPU-only environment as success for a
  required GPU/accelerator capability.

If the user did not provide a repository path, use the current working directory.

Ask the user for more input only when a required host-level runtime or manager
installation is not already authorized, the package cannot be installed or
verified, a required backend is unavailable and the user must narrow scope or
accept partial drafting, modifying a user-provided existing environment may
break it and the user has not authorized that mutation, a safe environment
prefix cannot be chosen or used, an existing skill would be overwritten, or
the repository structure/backend analysis needs user confirmation before
extraction because `extractionScope` is still `ask`.

When `extractionScope` is `agent-decide`, the repository structure analysis must
still produce a concrete include/exclude map. It should include importable
package source roots, public APIs and CLIs, docs/examples/tutorials that show
user workflows, representative tests or fixtures, and useful repo-owned
scripts/tools/bin entries. It should exclude generated files, build/cache
outputs, vendored dependencies, large model/data artifacts, benchmarks,
release/CI infrastructure, unsafe scripts, and pure development internals unless
the user explicitly requested them or they are necessary to explain a public
workflow. Record this as an agent-confirmed extraction scope before preparing
the environment.

Do not require the user to enumerate source, docs, examples, scripts, or test directories. Discover those extraction inputs from the repository tree.

## Canonical Skill Id

Choose a canonical skill id before resolving the final file tree. It must match `^[a-z0-9][a-z0-9-]{0,63}$`:

- Lowercase letters, numbers, and hyphens only.
- Maximum 64 characters.
- No uppercase letters, underscores, spaces, dots, slashes, or leading hyphen.

Normalize by lowercasing, converting CamelCase boundaries and other separators to hyphens, collapsing repeated hyphens, and trimming hyphens. Use the canonical id as the default generated root directory basename and root `SKILL.md` frontmatter `name`.

Keep public project capitalization only in prose. For example, use `flag-embedding` as the generated skill id for a project publicly called `FlagEmbedding`, but use `FlagEmbedding` in prose when referring to the project branding.

## Generated Skill Output Path

Resolve the generated skill output path before writing files:

- If the user does not specify a target skill output path, set the active skills root to `<repository-path>/skills/`, create it if needed, and create the generated skill under that directory.
- If the default `<repository-path>/skills/` directory already exists, set the
  active skills root to `<repository-path>/skills/disco/` so DisCo
  output is clearly separated from any pre-existing repo skills or artifacts.
  Inspect the existing `skills/` content as evidence, but do not merge the new
  runtime skill into it.
- If the user gives a directory that is clearly a skills root, such as a path ending in `skills/` or a request to create the skill "under" a directory, treat that directory as the active skills root and create a new generated skill subdirectory inside it.
- If the user gives a path that is clearly the exact generated skill directory, such as an existing skill directory containing `SKILL.md` or an explicit request to update/create that exact directory, treat its parent as the active skills root.
- If the requested path does not exist and its basename already looks like the intended skill id, treat it as the generated skill directory. Otherwise treat it as the active skills root. Ask a concise clarification only when both interpretations are plausible and would write to meaningfully different places.
- If `<repository-path>/skills/` or the active skills root already exists, inspect existing skill directories as additional evidence for local conventions, useful references, prior troubleshooting notes, and expected structure, but create the new repo skill in a new normalized subdirectory and never overwrite or merge into an existing skill directory unless the user explicitly asks to update that exact skill.

If the active skills root already contains a directory with the canonical skill id, choose a new non-conflicting normalized directory name such as `<canonical-id>-repo-skill` or `<canonical-id>-2`, then use that chosen directory basename consistently as the generated root `SKILL.md` frontmatter `name` unless the user asked to update the existing skill.

## Review/Test Artifact Output Path

Resolve one artifact root for all generated material that is not part of the
runtime repo skill itself.

- If the user does not specify an artifact output path, use
  `<repository-path>/skills/tests/<chosen-skill-id>/`. Create missing
  directories as needed.
- If the user specifies a test case, review, verification, or artifact output
  path, use that directory exactly as the artifact root.
- Treat any path under `tests/` as a review/test artifact area, not as a
  generated skill directory.

All check-only or review-only outputs belong under this artifact root, but they
must be separated by purpose instead of mixed together at the top level:

```text
<artifact-root>/
  test-cases/              # concrete usability/native-backed/synthetic cases
    index.md
    sub-skills/<id>/...
    integration/...
  reports/                 # review, verification, and final handoff documents
    integration/...
    verification/...
    self-refine/...
    final/...
```

Use `test-cases/` for user-prompt case directories, their fixtures, and their
case index. Use `reports/` for self-refine eval files, automatic verification
reports, human-review notes, publication checklists, prompt samples, staleness
audits, benchmark notes, native candidate maps, native execution results, and
temporary review scratch files worth keeping.

Do not write those artifacts inside the generated skill directory. The
generated skill directory should contain only public runtime skill content:
`SKILL.md`, `references/`, `scripts/`, `sub-skills/`, and optional runtime
assets/templates that future agents need to use the skill.

The artifact root should not contain loose case directories or a catch-all
`review/` directory. Keep final deliverables clean by using the `test-cases/`
and `reports/` subdirectories above. The `verify-repo-skill` skill
owns the usability case format; see
`../../verify-repo-skill/references/usability-test-cases.md` for the
required `user_request.txt` and `README.md` files.

## Generated Skill Shape

Create the generated skill as a self-contained directory for the target repository. For repos with multiple meaningful user-facing capabilities, use this shape:

```text
repo-name/
  SKILL.md                    # Router for the whole repo skill, not a full manual.
  references/repo-provenance.md # Source commit, dirty state, evidence paths, and refresh baseline.
  references/repo-routing-metadata.json # Structured import metadata for repo-skills-router.
  sub-skills/                 # One directory per coherent sub-skill.
    sub-skill-1/
      SKILL.md                # Focused workflow router for this sub-skill.
      references/             # Markdown reference files for this sub-skill.
      scripts/                # Reusable scripts, with comments explaining usage.
  references/                 # Repo-level Markdown reference files.
  scripts/                    # Repo-level reusable shell, Python, or helper scripts.
```

For a very small repo with only one coherent user-facing workflow, it is acceptable to omit `sub-skills/` and keep one concise root `SKILL.md` plus bundled `references/` and `scripts/` when useful. Do not create artificial sub-skills just to match the tree shape.

Every root and sub-skill `SKILL.md` in this generated operating graph must
declare `metadata.disco-role: operating`. This keeps the graph available in
Researcher mode and excluded from Creator mode. Do not rely on the missing-role
Researcher fallback for DisCo-owned generated output.

Self-contained means future agents can use the generated skill after the original repository checkout is gone. Do not write generated instructions such as "run `examples/foo.py` from the repo" or "see `docs/bar.md` in the original repository." If source repo material is important, copy, distill, adapt, or wrap it into the generated skill's own `references/` or `scripts/`.

When the generated skill mentions a source repo script, example, notebook, tool,
or config as something a future agent should run, read, or adapt, the generated
skill must include a bundled replacement. Use the nearest skill-owned
`scripts/` directory for runnable helpers and the nearest `references/`
directory for distilled recipes or API details. The public runtime files must
not contain Markdown links or instructions that resolve to `../scripts`,
`../../examples`, absolute checkout paths, or any other file outside the
generated skill directory.

## Progressive Disclosure

- Root `SKILL.md`: target 80-150 lines. It should remain a router.
- Sub-skill `SKILL.md`: target 80-200 lines. If it approaches 250 lines, move detail into `references/`.
- API tables, model lists, benchmarks, long examples, CLI catalogs, troubleshooting matrices, and multi-page workflows over roughly 30 lines belong in `references/*.md`.
- Every reference or script must be linked from the nearest `SKILL.md` with one sentence explaining when to read or run it.
- Do not duplicate the same material in `SKILL.md` and references.

## Content Placement

| Content | Location |
| --- | --- |
| Repo purpose, install command, minimal import check, sub-skill routing | Root `SKILL.md` |
| Sub-skill purpose, triggers, short workflow, common decision points | Sub-skill `SKILL.md` |
| Full API signatures, parameter notes, object relationships | Nearest `references/api-reference.md` |
| End-to-end recipes, tutorials, notebooks, training or inference flows | Nearest `references/workflows.md` or a specific workflow reference |
| CLI commands, flags, config files, environment variables | Nearest `references/cli-reference.md` or `configuration.md` |
| Data formats, schemas, expected columns, dataset layouts | Nearest `references/data-formats.md` |
| Model catalogs, benchmark tables, supported backends, compatibility matrices | Nearest `references/model-overview.md`, `benchmarks.md`, or `compatibility.md` |
| Errors, confusing behavior, debugging steps, operational pitfalls | Nearest `references/troubleshooting.md` |
| Minimal v2 area/family routing projection for managed `repo-skills-router` import | Root `references/repo-routing-metadata.json` |
| Reusable environment checks, API inspection, smoke tests, repo example wrappers | Nearest `scripts/` directory |
| Cross-cutting checks used by several sub-skills | Root `scripts/` |
| Usability test case directories, fixtures, and case index | Artifact root `test-cases/`, default `<repository-path>/skills/tests/<chosen-skill-id>/test-cases/` |
| Self-refine eval artifacts, verification reports, human-review notes, publication checklists, prompt samples, staleness audits, benchmark notes, native candidate maps, final skill report | Artifact root `reports/`, default `<repository-path>/skills/tests/<chosen-skill-id>/reports/` |

Runtime content locations in the table refer to files inside the generated
skill directory. Review/test artifacts go under the artifact root and must not
be linked from generated runtime `SKILL.md` files. Original repo paths are
research inputs, not runtime dependencies for the generated skill.

`references/repo-provenance.md` is required for every generated repo skill. It
is public skill metadata, not a private setup report. It must identify the
source repo state without leaking local checkout paths or environment paths.

`references/repo-routing-metadata.json` is required for every generated repo
skill. It is consumed by
`verify-repo-skill/scripts/import_repo_skill.mjs`, which invokes the lower-level
area/family router updater inside the locked import transaction so the live
`repo-skills-router` can be rebuilt deterministically and rolled back with the
skill if necessary. Keep it concise and structured; do not put generated router
Markdown, evidence, rationale, confidence, or source checkout paths here.

Use this minimal v2 shape:

```json
{
  "schema_version": "2.0",
  "repo_id": "owner/repository",
  "skill_id": "<skill-id>",
  "taxonomy_sha256": "<current-taxonomy-sha256>",
  "routing_status": "classified",
  "assignments": [
    {
      "area": "<exact taxonomy area>",
      "family": "<exact family under that area>"
    }
  ]
}
```

The top-level `skill_id` must match the generated skill directory basename and
the root `SKILL.md` frontmatter. A repository may have multiple assignments,
but each assignment must be supported by its own evidence in the external
classification decision artifact. If no exact family is justified, write:

```json
{
  "schema_version": "2.0",
  "repo_id": "owner/repository",
  "skill_id": "<skill-id>",
  "taxonomy_sha256": "<current-taxonomy-sha256>",
  "routing_status": "unclassified",
  "assignments": [],
  "unclassified_reason": "<bounded evidence-first reason>"
}
```

Evidence and rationale belong outside the generated skill, preferably under
`<repo-path>/skills/disco/routing_decision/`. The normal import handoff is a
machine-readable `classification.json` plus a human-readable `evidence.md`.
The importer verifies that the handoff and this compact projection agree.

The machine-readable handoff must contain the provenance needed to update the
central repository index, not only the area/family assignments:

```json
{
  "schema_version": 1,
  "repo_id": "owner/repository",
  "repo_name": "repository",
  "source_url": "https://github.com/owner/repository",
  "source_commit": "<40-hex-commit>",
  "skill_id": "<skill-id>",
  "skill_root": "repo-skills/<skill-id>",
  "skill_content_sha256": "sha256:<64-hex-digest>",
  "taxonomy_sha256": "<current-taxonomy-sha256>",
  "status": "classified",
  "assignments": [
    {
      "area": "<exact taxonomy area>",
      "family": "<exact taxonomy family>",
      "confidence": "high",
      "rationale": "<assignment-specific explanation>",
      "evidence": [
        {
          "path": "README.md",
          "description": "<repository-local evidence>",
          "line_start": 1,
          "line_end": 20
        }
      ]
    }
  ]
}
```

`skill_content_sha256` is computed over the portable runtime skill tree and is
checked again during import. `confidence` is required for every classified
assignment in the external handoff and belongs to the central assignment
index; it is deliberately not copied into the runtime v2 metadata. Every
classified assignment needs at least one non-generated repository evidence
item; generated-skill prose can corroborate an assignment but cannot be its
only support. Use `status: "unclassified"`,
an empty assignment list, and a bounded `unclassified_reason` when no exact
family is justified. `blocked` and `failed` are processing outcomes and are
never importable runtime routing statuses.
