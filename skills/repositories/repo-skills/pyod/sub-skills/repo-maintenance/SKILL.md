---
name: repo-maintenance
description: "Maintainer workflow router for editing PyOD source, tests, docs,
  packaging metadata, CLI entry points, and the packaged od-expert skill
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# PyOD Repo Maintenance

Use this sub-skill when the user is contributing to PyOD itself: editing source
layout, package metadata, docs examples, CLI wiring, tests, or the packaged
`od-expert` agent skill. This route is for maintainer work in a PyOD checkout,
not for running anomaly detection as an end user.

## Route here for

- Locating PyOD source roots, package data, optional extras, or entry points.
- Choosing focused tests after edits to detectors, utilities, CLI, MCP import
  safety, persistence, thresholding, documentation, or packaged skills.
- Updating the shipped `od-expert` skill or KB-derived skill sections.
- Maintaining `scripts/regen_skill.py`, `pyod/skills/__init__.py`, or the
  package-data entries that make skills installable.
- Updating docs examples, especially the agentic demo figure workflow.
- Checking repo surface health without mutating files.

## Route elsewhere

- End-user detector fitting, scoring, and tabular APIs: `classic-detectors`.
- ADEngine, `pyod info`, `pyod install skill`, or MCP usage as a user workflow:
  `automated-lifecycle`.
- Time-series, graph, text/image/audio, and optional backend use: `specialized-modalities`.
- Persistence, thresholding, score combination, and operational model artifacts:
  `model-operations`.
- Release publishing, credentials, PyPI uploads, or destructive release actions:
  do not proceed unless an authorized PyOD maintainer explicitly approves the
  exact command and target.

## First-pass maintainer workflow

1. Identify the edited area and read the closest bundled reference below.
2. Run the safe surface checker before proposing commands that assume files or
   entry points exist:

   ```bash
   python path/to/this/sub-skill/scripts/repo_surface_check.py --repo-root <pyod-checkout>
   ```

   Add `--import-check` only when importing PyOD from the checkout is intended.
3. Pick a focused test slice from `references/testing-guide.md`; do not default
   to all optional-extra tests unless the edit changed those extras.
4. For `od-expert` content, run the generator check before and after editing
   KB-derived material. Only hand-written sections should be edited directly.
5. If a workflow would publish, upload, delete, or use credentials, stop and ask
   for maintainer approval instead of inferring authorization.

## Bundled references and scripts

- `references/repo-layout.md` — read when locating source roots, package-data
  ownership, optional dependencies, or CLI entry points.
- `references/testing-guide.md` — read when selecting non-destructive, focused
  pytest/CLI/generator checks by changed area.
- `references/skill-maintenance.md` — read before editing the packaged
  `od-expert` skill, KB-derived sections, installer maps, or packaged skill
  tests.
- `references/source-script-inventory.md` — read when deciding whether a repo
  script/example should be copied, adapted, wrapped, left reference-only, or
  excluded.
- `references/troubleshooting.md` — read when a maintainer check fails, an
  optional dependency is missing, packaged skill drift is reported, or a docs
  rendering helper fails.
- `scripts/repo_surface_check.py` — safe diagnostic helper; reports key files,
  packaging metadata, relevant tests, and optional command/import availability
  without modifying the checkout.

## Guardrails

- Keep commands relative to the current PyOD checkout. Do not use private
  environment paths or machine-specific directories in public instructions.
- Prefer `python -m pytest ...` and `python -m pyod.cli ...` so the selected
  Python environment is explicit.
- Treat optional extras (`torch`, `graph`, `embedding`, `openai`, `huggingface`,
  `audio`, `mcp`, `suod`, `xgboost`, `combo`, `pythresh`) as optional unless the
  changed area requires them.
- Do not edit generated KB-derived Markdown blocks by hand; update the knowledge
  source/generator and regenerate.
- Do not bundle or duplicate the repo's release commands. Publishing requires a
  maintainer-owned release procedure and explicit approval.
