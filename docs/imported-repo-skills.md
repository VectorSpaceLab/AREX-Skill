# Repository Skills Catalog

This catalog describes the current published repository-skill collection under
`skills/repositories/`. The collection contains exactly 1,000 repository skill
roots and is routed by the fixed area -> family taxonomy.

## Scope

| Metric | Value |
| --- | ---: |
| Repository skill roots | 1,000 |
| Taxonomy areas | 20 |
| Taxonomy families | 178 |
| Area-family memberships | 2,204 |
| Multi-assigned repositories | 700 |
| Unclassified / blocked / failed | 0 / 0 / 0 |

A repository can appear in multiple families when it provides distinct,
substantial capabilities supported by repository evidence. The router is not a
replacement for a repository skill; it progressively narrows a request from an
area to a family and then to the selected repository-skill root.

For a human-readable inventory of every repository grouped by area and family,
see the [Repository Catalog](repository-catalog.md). It links each entry to
the corresponding repository skill root and source repository.

## Published layout

```text
skills/
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
```

The machine-readable files are the source of truth for the catalog and router:

- [`repository-index.jsonl`](../skills/repositories/repo-skills/repository-index.jsonl)
  contains one canonical repository record per skill root.
- [`repositories.jsonl`](../skills/repositories/repo-skills-router/references/index/repositories.jsonl)
  contains the router repository view.
- [`assignments.jsonl`](../skills/repositories/repo-skills-router/references/index/assignments.jsonl)
  contains every exact `repo_id -> area -> family` membership.
- [`taxonomy.json`](../skills/repositories/repo-skills-router/references/index/taxonomy.json)
  contains the canonical taxonomy snapshot.
- [`build-metadata.json`](../skills/repositories/repo-skills-router/references/index/build-metadata.json)
  records generated counts, taxonomy hash, and index digests.

The router's generated Markdown views are available under
[`repo-skills-router/references/areas/`](../skills/repositories/repo-skills-router/references/areas/)
and
[`repo-skills-router/references/families/`](../skills/repositories/repo-skills-router/references/families/).
Use those pages for progressive disclosure; use the JSONL indexes for exact
machine-readable membership.

## Area summary

| Area | Families | Memberships |
| --- | ---: | ---: |
| Computer Vision | 21 | 312 |
| Biomedical AI | 11 | 50 |
| Generative Media | 13 | 192 |
| Speech and Audio | 5 | 55 |
| Natural Language Processing | 9 | 78 |
| LLM Applications | 16 | 323 |
| LLM Models, Training, and Alignment | 6 | 149 |
| Information Retrieval | 4 | 67 |
| MLOps | 15 | 116 |
| Model Deployment and Optimization | 4 | 114 |
| Training Infrastructure | 12 | 135 |
| Reinforcement Learning | 5 | 82 |
| Robotics and Embodied AI | 7 | 81 |
| Autonomous Driving | 3 | 38 |
| Graph Learning | 4 | 42 |
| Scientific Computing | 16 | 124 |
| Data Science | 12 | 152 |
| Time Series Analysis | 7 | 53 |
| Probabilistic and Causal Modeling | 4 | 20 |
| Responsible AI | 4 | 21 |

The family-level membership lists are intentionally generated rather than
duplicated in this document. Open the relevant area/family page or query
`assignments.jsonl` when an exact repository list is needed.

## Adding or changing a repository skill

Use `create-repo-skill` and `verify-repo-skill` to produce and verify the
runtime graph. Classification is a separate post-verification step against the
fixed taxonomy:

```text
verified repository skill
  -> exact area-family classification
  -> external routing decision with evidence
  -> minimal v2 repo-routing-metadata.json
  -> transactional import
  -> regenerated router indexes and Markdown views
```

The runtime metadata file contains only the canonical `owner/repository`
identity, skill ID, taxonomy hash, routing status, and exact assignments. Full
rationale and evidence remain outside the runtime graph, preferably under
`<repo-path>/skills/disco/routing_decision/` and in the production audit
artifacts.

If no exact family applies, use `unclassified` and ask the user whether to
import the skill. Importing an unclassified skill requires a user-approved
taxonomy extension before the normal import flow. An interrupted or
inaccessible classification is `blocked` or `failed`, not an inferred route.

Do not hand-edit generated router Markdown. Use the verified importer or the
router updater under its shared import lock.

## Installation

The recommended installation is managed by DisCo:

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

The previous `research-skills-library/` name is not part of this release.
Installation, updates, and routing use only the current `skills/repositories/`
layout.
