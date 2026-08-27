# Packaged `od-expert` Skill Maintenance

Read this before editing PyOD's packaged agent skill or the generator/tests that
keep it aligned with the PyOD knowledge base and ADEngine APIs.

## Maintained structure

PyOD ships its agent skill as package data under the Python subpackage
`pyod.skills.od_expert`. The agent-facing installed directory is `od-expert`.
The maintained tree is:

```text
pyod/skills/od_expert/
  SKILL.md
  references/
    workflow.md
    pitfalls.md
    tabular.md
    time_series.md
    graph.md
    text_image.md
  __init__.py
```

`SKILL.md` is the always-loaded router and compact expert checklist. Long
workflow details, modality tables, examples, and deeper pitfall guidance live in
`references/`. Keep this split when adding content: do not turn `SKILL.md` into
a long manual.

## What counts as a safe skill edit

A safe `od-expert` edit must preserve four invariants:

1. The skill drives a complete agentic anomaly-detection workflow, not just API
   documentation.
2. Advice encodes actionable anomaly-detection expertise such as decision
   rules, pitfalls, escalation triggers, and interpretation patterns.
3. Every named detector recommendation maps to an agent-callable PyOD detector
   or ADEngine method.
4. Literature, benchmark, or practice-derived advice has enough provenance in
   comments or surrounding text for future maintainers to refresh it.

If a proposed insight requires an API or detector PyOD does not provide, record
it as a backlog/design item instead of adding a broken runtime recommendation.

## KB-derived sections

Some Markdown regions are generated from `pyod.utils.knowledge` and must not be
edited by hand. They use exact paired markers:

```markdown
<!-- BEGIN KB-DERIVED: section-name -->
... generated body ...
<!-- END KB-DERIVED: section-name -->
```

Known renderer section names in the inspected generator are:

- `tabular-detector-list`
- `time-series-detector-list`
- `graph-detector-list`
- `text-image-detector-list`
- `total-detector-count`
- `benchmark-list`

The generator renders detector names, full names, complexity, `best_for`,
`avoid_when`, required extras, and paper references from the live KB. It excludes
planned detectors from buildable detector counts so the skill does not recommend
or count unimplemented roadmap entries.

## Generator workflow

When detector KB content changes:

```bash
python scripts/regen_skill.py --check   # dry-run before the edit, optional
python scripts/regen_skill.py           # rewrite KB-derived blocks in place
python scripts/regen_skill.py --check   # confirm clean regeneration
```

Review the diff carefully. Only KB-derived blocks should change. If hand-written
prose changed, treat it as a generator bug and inspect the marker regex or file
selection logic before committing.

Important generator coupling:

- `_REQUIRES_TO_EXTRA` maps raw dependency tokens such as `torch_geometric` to
  public extras such as `pyod[graph]`. Update this mapping when package extras
  or KB `requires` tokens change.
- Unknown section names should raise errors, not silently emit empty content.
- The generator scans Markdown under `pyod/skills/`, so adding a new packaged
  skill with KB-derived sections also places it under this refresh path.

## Hand-written prose workflow

When adding a new pitfall, rule, example, or escalation trigger:

1. Decide the target file: top-level activation and critical pitfall summaries
   in `SKILL.md`; long loop details in `references/workflow.md`; modality
   depth in a modality reference; extended pitfalls in `references/pitfalls.md`.
2. Confirm detector names and methods exist. Detector names in prose should use
   inline backticks when they are canonical detector identifiers so the KB test
   validates them.
3. Do not backtick a detector-like token that is not a KB key unless it is a
   legitimate allowlisted non-detector symbol.
4. If the prose names `state.X`, `state.X['nested']`, or `engine.method(...)`,
   verify it against ADEngine behavior or run the API-reference test.
5. Run the packaged skill test stack from `references/testing-guide.md`.

## CI safety nets and what failures mean

| Test/check | Maintainer meaning |
|---|---|
| `python scripts/regen_skill.py --check` | Generated blocks are stale if it exits non-zero. Run the generator and review the diff. |
| `test_regen_skill.py` | Generator import, rendering, marker replacement, and extra mapping are broken. |
| `test_skill_kb_consistency.py` | Detector names, marker syntax, generated block freshness, count claims, or allowlist invariants are broken. |
| `test_skill_api_refs.py` | Skill prose references an ADEngine/state API that is not present in live dry-run evidence. |
| `test_cli.py` install-skill cases | Packaged skill install behavior, canonical name handling, tree copying, or agent-neutral messages regressed. |

## Installer and package-data coupling

`pyod/skills/__init__.py` owns:

- `get_skill_path(skill_name)` for locating packaged skill data.
- `install(target_dir, skill_name)` for copying a skill tree into an agent skill
  directory.
- `install_cli(...)` for the legacy `pyod-install-skill` entry point.
- `_INSTALL_DIRNAME_MAP`, currently mapping `od_expert` to `od-expert`.

The installer accepts both underscore and hyphen skill names, copies
`SKILL.md` plus `references/`, ignores Python package artifacts, and prints
agent-neutral guidance for project-local installs. If adding a packaged skill,
update package data and installer mapping together, then test both canonical
name forms and reference-tree copying.

## Docs example considerations

`docs/examples/agentic.rst` describes the `od-expert` activation paths and the
agentic demo. If examples or screenshots change, keep text, code snippets, and
figure assets synchronized. The figure-rendering helper is intentionally not a
default test because it requires Playwright and Chromium; see
`references/source-script-inventory.md` for the decision and safety boundary.
