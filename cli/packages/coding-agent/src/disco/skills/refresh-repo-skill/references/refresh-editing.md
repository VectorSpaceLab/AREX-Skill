# Refresh Editing

## Purpose

Read this while editing the existing skill. Keep the skill recognizable, but
make its public guidance match the current repository.

## Preserve Identity And Shape

Keep existing root and sub-skill directory names and frontmatter `name` values
unless the user explicitly requested a rename or the current IDs are invalid.

Every `SKILL.md` frontmatter block must remain valid:

```markdown
---
name: skill-id
description: "Triggering description broad enough for natural user requests."
disable-model-invocation: true
metadata:
  disco-role: operating
---
```

Preserve or add `metadata.disco-role: operating` and
`disable-model-invocation: true` on every repo root and sub-skill. A refreshed
DisCo-owned repo skill must not depend on the missing-role fallback.

Do not add development history to public runtime guidance unless it helps future
agents choose correct current behavior. Put migration notes, stale-claim tables,
and baseline details under the review/test artifact directory instead.

## Edit In Place

Prefer these actions, in order:

1. Update the nearest existing route, decision point, or instruction.
2. Replace stale sections in the nearest existing reference file.
3. Replace stale reusable scripts with current safe inspection, validation, or
   conversion scripts.
4. Add a focused reference when current repo behavior needs more depth than the
   existing file should carry.
5. Add or promote a support-workflow route when current repo evidence shows a
   high-frequency data-preparation, validation, conversion, command-generation,
   data-layout, optional-dependency, environment-check, or maintainer workflow
   that was previously buried or missing.
6. Add a new sub-skill only when current repo behavior has distinct triggers or
   workflows that would overload existing routing.
7. Remove guidance only when current repo evidence proves it is unsupported,
   duplicated, or replaced.
8. Add or update `references/repo-provenance.md` with the current repository
   snapshot.

Avoid broad rewrites, unrelated style changes, and moving content only to make
the tree look new.

## Convert Stale Claims To Current Guidance

For each stale claim:

- Replace old API names, signatures, config keys, CLI flags, file layouts,
  dependency extras, and examples with current ones.
- Update troubleshooting so it reflects current error messages and likely
  causes.
- Update scripts so imports, commands, and schema paths match current source.
- Update copied examples so they are minimal, public, and runnable in a normal
  user environment.
- Remove references to behavior that no longer exists rather than keeping it as
  historical advice.

When a change requires migration context, write it as current actionable
guidance:

```markdown
If a user has older examples using `old_key`, translate them to `new_key`
before validation; the current config loader only accepts `new_key`.
```

Do not write:

```markdown
Previously this repo used `old_key` in commit abc123.
```

unless that history directly helps with current migration tasks.

## Maintain Self-Containment

Future agents using the refreshed skill should not need the original repo
checkout just to understand the skill. Distill current facts into bundled skill
content:

- Summarize current docs and examples into `references/*.md`.
- Adapt safe reusable checks into `scripts/`.
- Copy small schemas or templates only when needed and public.
- If a source repo script, example, notebook, tool, or config remains relevant,
  add a bundled skill-owned replacement and link that replacement from the
  nearest `SKILL.md`. Do not leave runtime links that point to the source repo
  checkout.
- Keep large notebooks, generated files, datasets, model weights, and private
  paths out of the skill.
- Keep bundled helper names and source repo artifact names precise. If the
  refreshed skill wraps `scripts/foo.py` as
  `sub-skills/bar/scripts/check_foo.py`, document that distinction instead of
  implying that the source repo has the bundled wrapper name.
- Recheck copyable command examples after editing scripts or templates. The
  documented flags, config keys, input files, and output files must match the
  current bundled helper interface.
- Remove generated debris from the runtime skill directory, including
  `__pycache__/`, `*.pyc`, `*.pyo`, build outputs, downloaded caches, and
  temporary scratch files.

It is acceptable for a repo-specific skill to instruct an agent to inspect the
user's active repo while doing a task. It is not acceptable for the skill's own
documentation to depend on private paths or stale external links for core facts.

## Update Repo Provenance

Every refreshed skill must contain `references/repo-provenance.md` after the
edit. If the old skill already has this file, replace its snapshot with the
current repository state. If it is missing, create it using the same
`disco.repo-provenance.v1` shape required by `create-repo-skill`.

The provenance update should include:

- Current commit, branch, exact tag when available, and dirty state.
- Dirty paths as repository-relative paths only, or an empty array for a clean
  checkout.
- Relevant package names, versions, and import names when available.
- Current evidence paths used by the refreshed skill, relative to the repo root.
- `remote_url: omitted-private-or-unknown` unless the remote is clearly public
  or the user explicitly wants it included.

Keep local absolute paths, conda prefixes, Python executables, private remote
URLs, cache paths, credentials, and `pip show Location` values out of the
provenance file.

## Update Usability Tests

Refresh usability tests with the same discipline as runtime skill files:

- Update prompts that mention old API names, flags, config keys, or workflows.
- Add at least one case that requires the refreshed current behavior.
- Keep at least one regression-sensitive case for a pre-existing workflow that
  remains supported.
- Keep `user_request.txt` directly copyable with no labels, headings, or test
  metadata.
- Update `index.md` so it reflects current coverage.

If the skill has no test-case directory, create one under the review/test
artifact directory's `test-cases/` subtree using the same shape required by
`create-repo-skill`.

## Review Notes

Create review notes under the review/test artifact directory's `reports/`
subtree, outside runtime skill docs, that list:

- Previous provenance used, or that no provenance was available.
- New provenance commit or non-Git source identifier.
- Current repo evidence inspected.
- Public skill files changed.
- Stale claims removed or refreshed.
- Scripts and usability cases updated.
- Verification status and accepted warnings.

These notes help the user review the refresh without polluting future skill
selection and execution.
