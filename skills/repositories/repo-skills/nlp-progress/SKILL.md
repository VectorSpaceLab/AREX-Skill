---
name: nlp-progress
description: "Routes tasks for using NLP-progress as a multilingual NLP
  benchmark/SOTA catalog, structured Markdown export source, and static-content
  maintenance workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# nlp-progress

Use this repo skill when a user asks about NLP-progress, `nlpprogress.com`, NLP benchmark/SOTA tables, multilingual NLP task catalog pages, Markdown-to-JSON export from the repository, or maintaining the repository's static Markdown benchmark content.

NLP-progress is a static Markdown/GitHub Pages knowledge base, not an installable model package. It has no public Python package import, no ML accelerator backend, and no training/inference runtime. Its only Python workflow is a standard-library structured export utility preserved in this skill.

## Route map

| User intent | Read next | Why |
| --- | --- | --- |
| Find NLP task pages, datasets, leaderboards, metrics, SOTA rows, code links, or multilingual coverage | [sub-skills/benchmark-catalog/SKILL.md](sub-skills/benchmark-catalog/SKILL.md) | Navigates language directories, heading trails, result tables, stale-leaderboard caveats, and citation patterns. |
| Export Markdown pages to structured JSON or debug `structured.json` output | [sub-skills/structured-export/SKILL.md](sub-skills/structured-export/SKILL.md) | Provides a bundled exporter adapted from the repo utility plus schema, parser assumptions, and troubleshooting. |
| Add/update result rows, dataset sections, code links, task pages, table style, or optional Jekyll preview | [sub-skills/content-maintenance/SKILL.md](sub-skills/content-maintenance/SKILL.md) | Captures contribution rules, Markdown table conventions, validation checker, and optional GitHub Pages preview notes. |

## Prerequisites and quick check

- No Python package installation is required because NLP-progress is a static Markdown repository, not an installable package.
- Use any modern Python 3 interpreter for the bundled helper scripts; the repo's structured export utility uses only the Python standard library.
- Optional site preview needs Ruby/Bundler/GitHub Pages gems and is documented in `content-maintenance`.

From the generated `nlp-progress` skill root, a minimal self-check is:

```bash
python3 scripts/smoke_check.py
```

## Shared references and scripts

- [references/corpus-overview.md](references/corpus-overview.md) — source corpus shape, language-directory inventory, support files, and evidence-to-skill mapping.
- [references/troubleshooting.md](references/troubleshooting.md) — cross-cutting issues: wrong content root, stale SOTA, optional dependencies, source-checkout independence, and route confusion.
- [references/repo-provenance.md](references/repo-provenance.md) — source commit, dirty-state baseline, package/non-package status, and refresh guidance.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) — structured metadata used by DisCo's repo-skills-router importer if this skill is imported in a later approved run.
- [scripts/smoke_check.py](scripts/smoke_check.py) — safe standard-library check for bundled script syntax/help and required metadata files.

## Typical workflows

### Benchmark lookup

1. Ask the user for the NLP-progress content root if they are working outside a checkout or copied corpus.
2. Read `benchmark-catalog`.
3. Use its inventory helper to locate language/task pages, then cite content-root-relative paths and heading trails.
4. Say “NLP-progress lists...” when you have not independently verified current leaderboard status.

### Structured export

1. Read `structured-export`.
2. Run the bundled exporter on selected Markdown files or language directories.
3. Validate the JSON shape and preserve parser warnings in the handoff.
4. Use `benchmark-catalog` first when the user has not already selected files.

### Content maintenance

1. Read `content-maintenance`.
2. Apply source-quality, dataset, code-link, and sorting rules before editing.
3. Run the bundled Markdown checker on changed files.
4. Use the structured exporter when the user needs proof that the edited row appears in JSON.
5. Treat Jekyll preview as optional unless the user explicitly asks for rendered site validation.

## Operating constraints

- Do not install ML frameworks or accelerator packages for this repository.
- Do not require the original production checkout after this skill is generated; use caller-supplied content roots and bundled scripts.
- Do not rely on source repository scripts at runtime. The useful export logic and validation helpers are bundled under this skill's `scripts/` subtrees.
- Do not claim a static NLP-progress row is current SOTA unless current external evidence was checked separately.
- Keep generated skill paths relative to the `nlp-progress` skill root when invoking bundled helpers.
