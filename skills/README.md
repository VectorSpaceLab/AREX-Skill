# The AREX-Skill Library

This directory is the public runtime collection for AREX-Skill. Skills are
organized by the kind of knowledge or capability they provide. The repository
skills collection is currently populated; the `papers/` and `task-oriented/`
collections are reserved for future expansion:

```text
skills/
  README.md
  repositories/
    repo-skills/
      repository-index.jsonl
      <skill-id>/
        SKILL.md
        sub-skills/
        references/
        scripts/
    repo-skills-router/
      SKILL.md
      references/
        areas/
        families/
        index/
  papers/                 # To be added in a future version
  task-oriented/          # To be added in a future version
```

The intended collection layout is:

| Collection | Runtime skills | Collection router | Status |
| --- | --- | --- | --- |
| `repositories/` | `repo-skills/` | `repo-skills-router/` | Currently populated |
| `papers/` | To be added in a future version | To be added in a future version | Reserved for future expansion |
| `task-oriented/` | To be added in a future version | To be added in a future version | Reserved for future expansion |

Each collection owns its own skills and router. The domain-specific router
names are intentional: they remain clear and globally distinguishable when
multiple collection routers are available to an agent. The existing
`repositories/` layout and the `disco repo-skills ...` commands remain the
current repository-skills interface.

## Repository skills

This collection contains the high-reuse repository skill graphs used by DisCo
Researcher and the generated router that selects them:

The published collection contains 1,000 repository skill roots, 2,204 exact
area-family memberships, 20 taxonomy areas, and 178 families. A repository may
appear in multiple families when it has distinct, evidence-backed
capabilities. The router uses progressive disclosure:

```text
request -> area -> family -> repository skill root -> relevant sub-skill
```

The machine-readable router indexes under
`skills/repositories/repo-skills-router/references/index/` are the source of
truth for the generated area and family pages. The canonical taxonomy is
embedded in `taxonomy.json`; the repository and assignment ledgers are
`repositories.jsonl` and `assignments.jsonl`.

Each repository skill keeps a minimal v2
`references/repo-routing-metadata.json` containing its canonical
`owner/repository` identity, skill ID, taxonomy hash, routing status, and exact
assignments. Full classification rationale and evidence stay outside the
runtime skill graph, in the production routing-decision artifacts or the
repository's `skills/disco/routing_decision/` handoff directory.

The previous `research-skills-library/` name is not part of this release.
Runtime installation and selection use only the current
`skills/repositories/` layout.

## Install into DisCo

The recommended installation uses the CLI-managed collection:

```bash
disco repo-skills install
disco repo-skills status
disco repo-skills update
```

The managed destination is:

```text
~/.disco/agent/skills/repositories/
  repo-skills/
  repo-skills-router/
```

The repository roots and their sub-skills are registered but normally hidden
from automatic model invocation. `repo-skills-router` remains the
model-visible entry point unless the user disables it with
`disco repo-skills router disable`; explicit `/skill:repo-skills-router`
invocation remains available.

## Updating the collection

Use `create-repo-skill` and `verify-repo-skill` to produce and verify a new
runtime graph. Classification is a separate post-verification step against the
fixed taxonomy. Write the full routing decision outside the runtime skill,
write the minimal v2 metadata fragment inside the skill, and use the dedicated
transactional importer. Do not hand-edit generated router Markdown.

When no exact family applies, record `unclassified` and ask the user whether to
import it. If the user wants it included, propose a taxonomy extension and wait
for approval or correction before changing the canonical taxonomy. Interrupted
or inaccessible classification is `blocked` or `failed`, not a guessed route.

For cross-agent export, use the bundled
`import-repo-skills-to-agent` workflow. It preserves the nested repository
collection and imports a router scoped to the selected skills.
