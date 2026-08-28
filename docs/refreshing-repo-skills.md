# Refreshing Repository Skills

Repository skills describe a specific upstream repository at a particular
source baseline. Because upstream code, APIs, documentation, examples,
dependencies, and runtime behavior change over time, a published skill should
be refreshed rather than treated as a permanent snapshot.

Use DisCo's `refresh-repo-skill` meta skill when the skill should continue to
cover the same repository but its existing guidance may be stale. Use
`extend-repo-skill` instead when the request is to add a genuinely new workflow
area or broader capability.

## Quick Start

You need:

- an existing repository skill containing a root `SKILL.md`;
- a current checkout of the upstream repository to use as evidence;
- DisCo with at least one configured model provider;
- permission to write a review or staging directory outside the live managed
  skill directory.

Start the interactive Creator CLI:

```bash
disco --creator
```

At the DisCo prompt, invoke the meta skill with the existing skill path and the
current upstream checkout:

```text
/skill:refresh-repo-skill Refresh the existing repo skill at /path/to/AREX-Skill/skills/repositories/repo-skills/<skill-id> against /path/to/upstream-repository. Preserve correct workflows, update stale guidance, run verification, and prepare a contribution-ready result without changing the skill identity.
```

For a one-shot or scripted run, the same request can be passed with `-p`:

```bash
disco --creator -p "/skill:refresh-repo-skill Refresh the existing repo skill at /path/to/skill against /path/to/upstream-repository. Preserve correct workflows, update stale guidance, run verification, and prepare a contribution-ready result."
```

The interactive form is the normal CLI workflow. `-p` / `--print` is only the
optional non-interactive mode for automation.

If the existing skill is the live managed copy under
`~/.disco/agent/skills/repositories/repo-skills/`, let the workflow create an
external working copy before editing. Do not edit the live managed copy in
place. Review the staged result and approve the exact overwrite/import only
after verification succeeds.

## What The Refresh Workflow Does

`refresh-repo-skill` performs the following sequence:

1. Resolves the existing skill, the current upstream checkout, the previous
   provenance baseline, and the review artifact directory.
2. Audits the current skill against repository evidence and separates supported
   claims, stale or removed claims, new relevant behavior, and unresolved
   unknowns.
3. Updates the existing runtime tree in place, preserving the skill and
   sub-skill identities unless an identity change is explicitly requested.
4. Rebuilds `references/repo-provenance.md` for the refreshed source revision,
   package versions, dirty state, and repository-relative evidence paths.
5. Resolves and applies the source repository license for the exact refresh
   commit to the root and every sub-skill.
6. Updates usability cases, runs static and feasible live checks, and writes
   review artifacts outside the runtime skill directory.
7. Produces the routing handoff and uses the verified importer to replace the
   managed skill only after the required approval or auto-authorized policy.

The workflow should preserve useful existing guidance, but it must remove or
rewrite claims that current repository evidence no longer supports. A refresh
is not a blind regeneration from the latest README.

## What Must Stay In Sync

A refresh is complete only after the whole repository skill tree and its
publication metadata have been reviewed. Check the following areas explicitly.

### Runtime Skill Tree

Update every affected public runtime file, not only the root `SKILL.md`:

- root `SKILL.md` descriptions, routes, workflows, validation, and
  troubleshooting;
- every affected `sub-skills/**/SKILL.md`;
- `references/` instructions, API details, configuration guidance, provenance,
  and source-derived evidence;
- `scripts/` helpers, checks, command builders, converters, and smoke tests;
- public templates or small assets that the runtime instructions actually use.

Remove stale source-repository paths, obsolete commands, old configuration
keys, unsupported APIs, downloaded caches, build output, and private local
paths. Runtime content must remain self-contained after the upstream checkout
is no longer available.

### Provenance

Refresh `references/repo-provenance.md` with the current repository state. It
should record, when available:

- the exact source commit, branch, and tag;
- clean or dirty state and repository-relative dirty paths;
- relevant package names, versions, and import names;
- repository-relative evidence paths used by the refreshed skill;
- a safe remote value, or `omitted-private-or-unknown` when the remote should
  not be published.

Do not put local absolute paths, virtual-environment names, Python executable
paths, cache locations, credentials, or private remotes in public skill files.

### License Metadata

Resolve the license once for the canonical upstream repository and the exact
source commit being refreshed. The resolver uses GitHub CLI semantics equivalent
to:

```bash
gh api "repos/<owner>/<repo>/license?ref=<source-commit>" \
  --jq '.license.spdx_id // empty'
```

The refresh workflow must then apply one repository-level value to the top-level
`license` field in the frontmatter of the root and every sub-skill:

```yaml
license: MIT
```

When GitHub CLI is unavailable, unauthenticated, unable to reach the API,
returns 404, or produces no usable value, write:

```yaml
license: NO_LICENSE
```

GitHub's `NOASSERTION` is an accepted source value and must be preserved in the
runtime tree. `NO_LICENSE` is a warning that this query did not obtain a usable
result. It is not a conclusion that the upstream repository has no legal license.
The refresh may continue to verification and import, but the final report and
user-facing handoff must list the repository, source commit, status, reason, and
required manual follow-up for `NO_LICENSE`. Never let separate sub-agents guess
different license values.

### Routing And Catalog

Compare the refreshed capability scope with the previous routing baseline:

- retain existing area-family assignments when the capability scope is still
  materially the same;
- create a new routing handoff when coverage, taxonomy, or capability scope
  changes;
- update `references/repo-routing-metadata.json` and related structured records
  when the routing decision changes;
- regenerate the repository router and indexes through the verified importer or
  updater;
- update `docs/imported-repo-skills.md` and other generated catalog views when
  the published collection changes.

Do not hand-edit generated router Markdown or silently change a skill's
classification in prose. Routing and catalog output must remain aligned with
the refreshed skill, provenance, and structured routing metadata.

### Review And Verification Artifacts

Keep check-only artifacts outside the runtime skill tree. A default location is:

```text
<upstream-repository>/skills/tests/<skill-id>/
├── test-cases/
└── reports/
```

The review package should include the staleness audit, verification report,
license-resolution report, human-review notes, publication checklist, and the
final routing handoff when applicable. The runtime tree should contain only
files that future agents need when using the skill.

## Verification Checklist

Before proposing a refresh for publication, verify that:

- root and sub-skill frontmatter is valid and has the same top-level `license`;
- `references/repo-provenance.md` reflects the refreshed source commit;
- every Markdown link points to an existing runtime file;
- public commands, APIs, configuration keys, examples, and troubleshooting
  match current source evidence;
- at least one usability case exercises refreshed behavior;
- at least one regression-sensitive case confirms a still-supported workflow;
- safe native examples, tests, CLI help, imports, or smoke checks were run when
  feasible;
- no local checkout paths, credentials, caches, build output, or temporary
  files leaked into the runtime tree;
- routing metadata, generated router views, repository indexes, and catalog
  entries are consistent;
- all `NO_LICENSE` warnings and accepted unknowns are visible in the final
  report;
- the verified runtime tree remains staged until the exact import or overwrite
  is approved.

For managed DisCo imports, use the structured
`verify-repo-skill` importer. It replaces the exact approved skill and rebuilds
the sibling router under the shared import lock. Do not manually combine copy,
overwrite, and router-update commands.

## Preparing A Pull Request

For a public contribution, place the verified runtime tree under:

```text
skills/repositories/repo-skills/<skill-id>/
```

A refresh PR should explain what changed and provide enough evidence for a
reviewer to reproduce or audit the update. Include:

- **Skill identity:** `skill-id`, repository identity, and the affected root or
  sub-skills.
- **Upstream baseline:** upstream repository URL, previous source commit or
  tag, new source commit or tag, branch, and refresh date.
- **Change summary:** stale claims removed, guidance updated, new workflows
  added, behavior removed, and any intentionally retained content.
- **Production method:** DisCo `refresh-repo-skill`, manual editing, or copied
  workflow skills; identify each method if multiple passes were used.
- **Model details:** model, provider, reasoning or thinking level, and the role
  of each model when multiple models or passes were involved.
- **Verification:** exact commands, tests, imports, CLI checks, native examples,
  usability prompts, and review steps that were run.
- **Environment limits:** skipped checks, unavailable credentials, optional
  dependencies, hardware limits, network restrictions, and known unknowns.
- **Routing impact:** whether area-family assignments were retained or changed,
  why, and whether the router, structured indexes, and public catalog were
  regenerated.
- **License result:** resolved license value or `NO_LICENSE`, exact source
  commit, query status, failure reason when applicable, and confirmation that
  root and all sub-skills use the same value.
- **Review artifacts:** paths to the staleness audit, verification report,
  license report, usability cases, and final handoff.

A concise PR summary can use this structure:

```markdown
## Refresh Summary

- skill: <skill-id>
- upstream repository: <owner>/<repo>
- previous source commit: <old-commit>
- refreshed source commit: <new-commit>
- refreshed areas: <areas>
- routing: retained | reclassified
- license: <value>

## Verification

- commands/checks: <list or report path>
- usability cases: <path>
- known gaps: <none or details>
- review artifacts: <path>
```

## Common Mistakes

- Updating only the root `SKILL.md` while leaving sub-skills or references stale.
- Keeping the previous provenance commit after changing the source baseline.
- Preserving an old license without re-querying the exact refresh commit.
- Treating `NO_LICENSE` as a legal conclusion or hiding it from the final report.
- Hand-editing generated router Markdown instead of updating structured routing
  metadata and rebuilding it.
- Putting test cases, reports, or benchmark notes inside the runtime skill.
- Using `extend-repo-skill` when the real problem is upstream drift.
- Importing an unverified working tree directly into the live managed directory.

## See Also

- [`refresh-repo-skill`](../cli/packages/coding-agent/src/disco/skills/refresh-repo-skill/SKILL.md)
  for the bundled workflow contract and references.
- [`DisCo Workflows`](disco-workflows.md) for Creator and Researcher workflow
  context.
- [`Contributing`](../CONTRIBUTING.md) for repository-wide contribution rules.
- [`Imported Repo Skills Catalog`](imported-repo-skills.md) for published
  repository graphs and upstream baselines.
