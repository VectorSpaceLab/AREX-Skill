# Change Detection And Staleness Audit

## Purpose

Read this before editing. The goal is to compare the existing skill against the
current repository and identify exactly which public skill claims need to stay,
change, or be removed.

## Resolve Current And Baseline State

Capture:

- `skill_dir`: existing skill directory.
- `repo_path`: current repository checkout and branch.
- `current_repo_state`: current commit when available, dirty status summary, and
  relevant package version.
- `provenance`: existing `references/repo-provenance.md` snapshot when present.
- `baseline`: fallback optional commit, branch, tag, release, previous generated
  skill handoff, or user-stated date when provenance is absent.
- `inspection_python`: optional verified Python executable for live API/CLI
  checks.
- `artifact_dir`: review/test artifact directory. Use `test-cases/` below it
  for concrete usability cases and `reports/` below it for staleness audits,
  verification reports, self-refine evals, prompt samples, and benchmark notes.
  If the user did not specify it, use
  `<repository-path>/skills/tests/<skill-id>/`.

First look for `<skill_dir>/references/repo-provenance.md`. Parse the JSON block
with schema `disco.repo-provenance.v1` when present. Compare it against the
current checkout before deeper auditing:

```text
Provenance field | Current repo evidence | Decision
repository.commit | git rev-parse HEAD | same, changed, unknown
repository.working_tree and dirty_paths | git status --short | same, changed, unknown
packages[].version | package metadata / installed inspection | same, changed, unknown
evidence.* paths | current repo tree | present, moved, removed, unknown
```

Prefer running `scripts/check_repo_provenance.py` for this first comparison
when the script is available:

```bash
python scripts/check_repo_provenance.py --skill-dir /path/to/skill --repo-path /path/to/repo
```

The script returns:

- exit `0` with `status: current` when commit, dirty state, and recorded
  evidence paths match.
- exit `1` with `status: stale` when it finds commit, dirty-state, dirty-path,
  or evidence-path drift.
- exit `2` with `status: unknown` when provenance is missing, invalid, or Git
  state cannot be read.

Treat `status: current` as a fast signal, not the whole verification. If the
user reports a concrete stale behavior, continue auditing claims even when the
snapshot appears current.

If no provenance exists, treat the current skill content as the baseline and
create `references/repo-provenance.md` during the refresh. The refresh still
works by validating every material skill claim against current repo evidence,
but the review report should warn that no prior commit baseline was available.

Do not copy absolute local paths, conda prefixes, or `pip show Location` values
into public skill files. It is fine to keep them in private review artifacts
under the review/test artifact directory.

## Audit Existing Skill Coverage

Build a compact current-skill map before touching files:

```text
Skill area | Current claim or route | Evidence needed | Initial decision
root SKILL.md | routes training workflow to sub-skills/training | current CLI/docs/tests | likely keep, verify command name
references/config.md | says config key is model_path | current schema/source | stale if renamed to checkpoint
scripts/validate_config.py | imports old module path | live import check | update or replace
tests/example-basic | asks for old CLI flag | current --help | refresh prompt
```

Inspect:

- Root and sub-skill `SKILL.md` frontmatter, descriptions, triggers, routes, and
  reference/script links.
- Existing `references/`, `scripts/`, `assets/`, and `sub-skills/`.
- Existing support-workflow coverage such as validation, conversion, command
  generation, data-layout checks, optional dependency checks, environment
  diagnostics, and maintainer guidance. These often become stale or were absent
  in older generated skills even when headline API routes still look correct.
- Existing usability tests and index files.
- Review reports, generation handoffs, or staleness notes when present.
- `references/repo-provenance.md`, including commit, dirty state, package
  versions, and relative evidence paths.

Focus on public runtime skill content first. Review artifacts can explain the
change, but they should not drive future agent behavior.

## Gather Current Repository Evidence

Use current repo evidence to prove or disprove material claims:

- Source code for public APIs, class/function signatures, modules, config
  schemas, defaults, error paths, and object relationships.
- CLI definitions and `--help` output for commands, flags, subcommands, and
  examples.
- Tests and fixtures for supported behavior, edge cases, and expected failures.
- Docs, examples, notebooks, and release notes for intended workflows.
- Dependency files and package metadata for install extras, Python version,
  optional backends, and renamed packages.
- Repo scripts, tools, examples, and fixtures that can be safely distilled into
  bundled skill helpers for repeatable validation, data preparation, command
  building, layout checks, smoke tests, and optional dependency diagnostics.
- Existing repo-local skills for conventions, only if they are newer than the
  stale skill or clearly maintained with the repo.

When a Python package must be inspected live, use the verified environment from
the user or the handoff from `prepare-repo-skill-env`. Run safe
inspection only: imports, signatures, docstrings, metadata, CLI help, schema
loading, and tiny smoke tests that do not require expensive training or network
access.

## Use Git Or Release Evidence When Available

If the repository is a Git checkout, collect targeted change evidence:

- `git status --short` to understand local uncommitted changes.
- Current commit and branch.
- `git diff <provenance-commit>...HEAD -- <relevant paths>` when provenance has
  a commit and the commit exists locally.
- `git log --oneline <provenance-commit>..HEAD -- <relevant paths>` for
  high-level change themes.
- Release notes or changelog entries that match the user's stated update.

Do not require a baseline before proceeding. If provenance is absent, unknown,
dirty, or references a commit unavailable in the local clone, audit the old
skill claims directly against current source code and live inspection.

## Staleness Audit

Before editing, write a concise audit in working notes or the review/test
artifact directory:

```text
Existing claim | Current evidence | Decision | Skill file action | Verification
old import path package.foo.Model | package/model.py exports NewModel, old path removed | stale | update references/api.md and script import | python -c import smoke
CLI flag --config-path | cli.py still accepts --config-path | retain | no public edit | --help check
training docs omit new dataset registry | docs/datasets.md and tests cover registry | add because it changes existing data workflow | extend references/data.md | usability case
old skill lacks data-layout checker | docs/setup.md and tests/fixtures define required tree | add-replacement because setup failures are high-frequency | add scripts/check_data_layout.py and route from setup sub-skill | run on tiny fixture
```

Classify decisions as:

- `current`: provenance matches the current repo and no refreshed facts are
  needed after claim audit.
- `repo-drift`: commit, dirty state, package version, or evidence paths differ
  from provenance.
- `retain`: current evidence still supports the old guidance.
- `refresh`: current evidence changes names, signatures, defaults, workflows, or
  troubleshooting.
- `remove`: old guidance describes removed or unsupported behavior.
- `add-replacement`: new repo behavior replaces or materially alters an existing
  workflow.
- `add-support-workflow`: current repo evidence shows a repeatable validation,
  conversion, command-generation, data-layout, optional dependency, environment,
  or maintainer workflow that is needed for practical use and is missing or too
  shallow in the old skill.
- `defer`: evidence is ambiguous; requires user input or an explicitly accepted
  warning.

Proceed to editing only when each high-impact stale claim has an action.
