# Contributing

Auto-ML Skills treats skills as operating guidance that future agents may load
and follow. Good contributions are evidence-grounded, easy to audit, and clear
about how the skill was produced.

## Contribution Paths

You can contribute:

- new generated repo skills under
  `skills/repositories/repo-skills/<skill-id>/`;
- improvements to existing repo skills;
- router, catalog, provenance, and documentation updates;
- bundled workflow skills under
  `cli/packages/coding-agent/src/disco/skills/`;
- DisCo CLI source changes under `cli/`.

## New Repo Skills

The most important contribution type is a new runtime repo skill.

Required files:

- `skills/repositories/repo-skills/<skill-id>/SKILL.md`
- `skills/repositories/repo-skills/<skill-id>/references/repo-provenance.md`
- `skills/repositories/repo-skills/<skill-id>/references/repo-routing-metadata.json`
- sub-skills and references when the upstream repository has multiple major
  workflow areas
- small validation or preflight scripts when they make the skill safer to use

Keep runtime skill content separate from review artifacts. Publication-ready
content belongs in:

```text
skills/repositories/repo-skills/<skill-id>/
```

Test cases, review notes, and generation reports should stay outside the
runtime skill directory unless they are intentionally part of the runtime
guidance.

## Router And Catalog Consistency

When adding, deleting, renaming, importing, or materially changing a repo skill,
update the router through the verified importer/updater:

```text
skills/repositories/repo-skills-router/SKILL.md
skills/repositories/repo-skills-router/references/areas/*.md
skills/repositories/repo-skills-router/references/families/<area>/*.md
skills/repositories/repo-skills-router/references/index/
```

Router entries should help an agent choose among skills using exact area and
family scopes. They should not copy the full skill instructions or routing
evidence.

Update the public catalog when the imported skill library changes:

```text
docs/imported-repo-skills.md
```

The catalog should stay aligned with `repo-routing-metadata.json` and
`repo-provenance.md`.

## Improving Existing Repo Skills

Improvements are welcome when a skill is stale, unclear, incomplete, or too
hard for an agent to use.

Rules:

- Ground changes in source evidence, upstream docs, examples, or inspected
  package behavior.
- Preserve correct existing guidance.
- Update provenance when the source commit, package version, or evidence set
  changes.
- Update routing metadata when coverage or selection guidance changes.
- Keep scripts deterministic and safe. Avoid downloads, training, server
  startup, or destructive filesystem operations unless clearly gated.

Focused checks:

```bash
find skills/repositories/repo-skills/<skill-id> -type f -name '*.py' -print0 | xargs -0 -r python -m py_compile
find skills/repositories/repo-skills/<skill-id> -type f | sort
```

## Pull Request Requirements

For every PR that adds or modifies generated repo skills, include:

- the upstream repository URL and source commit or tag;
- the model and provider used to produce the skill;
- the reasoning or thinking level used, such as `low`, `medium`, `high`, or the
  provider-specific equivalent;
- whether the skill was produced by DisCo, by copied workflow skills, or by
  manual editing;
- the verification commands or review steps that were run;
- any known gaps, skipped checks, unavailable credentials, or environment
  limits;
- confirmation that the sibling `skills/repositories/repo-skills-router/`
  was updated when routing changed.

If multiple models or passes were used, list each model and its role, for
example generation, review, refinement, or verification.

## Documentation Changes

The root README, architecture guide, portable-meta-skill guide, contribution
guide, and Research Skills Library guide are bilingual. When changing one side
of a paired page, update the other side in the same change. The repository
catalog is one shared data page covering 1,000 roots and 2,186 memberships;
keep its localized summaries and links in the Chinese README aligned with it.

Rules:

- Keep paths relative to the Markdown file location.
- Prefer concrete commands and locations over general descriptions.
- Keep README pages concise and move detailed workflows into `docs/`.
- Use the root README files as the main language entry points instead of adding
  a language switcher to every page.
- If the catalog changes, keep its count, grouping, paths, and localized README
  summary aligned.

Useful checks:

```bash
python - <<'PY'
from pathlib import Path
for p in sorted(Path('docs').glob('*.md')):
    text = p.read_text()
    if '\t' in text:
        print(f'tab: {p}')
PY
```

## Workflow Skill Changes

`cli/packages/coding-agent/src/disco/skills/` is the single source of truth for
workflow skills bundled with DisCo and optionally copied into external agents.
The separate [meta-skill guide](docs/meta-skills-for-other-agents.md) defines
which Creator-only directories may be copied; do not copy the operating router
or repository collection as meta skills.
Keep portable instructions understandable without DisCo-only extensions.

When updating workflow skills:

- State expected inputs and outputs explicitly.
- Ask for user confirmation at expensive or destructive points unless the user
  authorized agent-decided behavior.
- Keep environment changes isolated.
- Keep generated runtime skill content separate from tests and reports.
- Keep meta-skill installation separate from deployment of the operating graph
  it later produces. Task-bound or uncertain graphs default to a trusted
  project's `.agents/skills/`; managed scope requires evidence of cross-project
  reuse, and one graph must stay in one scope.
- Keep repository graphs on their specialized
  `~/.disco/agent/skills/repositories/repo-skills/` import path with the sibling router
  rebuild; do not pass repo routing metadata through the generic graph importer.
- Update the [workflow README](cli/packages/coding-agent/src/disco/skills/README.md)
  when names, paths, defaults, or workflow boundaries change.
- Update generated templates and their generators together. In particular,
  router behavior rendered by `update_repo_skills_router.mjs` must not be
  changed only in a checked-in Markdown output.

## DisCo Source Changes

The DisCo CLI source lives under `cli/`.

Common checks:

```bash
cd src
npm ci --ignore-scripts
npm run prepublishOnly
```

`prepublishOnly` runs typechecking, the full test suite, example typechecking,
upstream provenance verification, the build, and the packed-file audit for the
standalone package.

Changes to runtime skill discovery or routing should test that managed hidden
skills are registered but omitted from the initial prompt, the live router
overrides the bundled fallback, untrusted project skills do not load, and
installed package skills remain usable.

Repository-library router rebuilds use the canonical collection and sibling
router explicitly:

```bash
node cli/packages/coding-agent/src/disco/skills/verify-repo-skill/scripts/update_repo_skills_router.mjs \
  --library-root skills/repositories
```

For publish preparation, dry-run package contents before publishing:

```bash
cd cli
npm publish --dry-run --ignore-scripts
```

Do not hand-edit generated `dist/` files or standalone binary runtime assets as
source changes.

## Final Checklist

Before handing off a change:

- README and docs links point to existing files.
- English and Chinese docs are both updated when applicable.
- Runtime skill changes include provenance and source evidence.
- Router and catalog changes are consistent with skill changes.
- PR text lists the model, provider, reasoning or thinking level, and
  verification steps.
- Scripts touched by the change have been syntax-checked or otherwise
  verified.
- The final summary states what was verified and what was not.
