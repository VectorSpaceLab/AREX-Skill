# Source Script and Example Inventory

Read this before copying, adapting, wrapping, or excluding PyOD source scripts
and examples for repo-maintenance workflows. Decisions here are concrete for
this sub-skill; user-facing detector examples are owned by other PyOD sub-skills.

## Decision categories

- **copy**: preserve a small safe script nearly verbatim in this generated skill.
- **adapt**: create a smaller deterministic helper that keeps reusable logic but
  removes repo-local assumptions, side effects, or heavyweight dependencies.
- **wrap**: provide a bundled wrapper around a current-checkout command with
  validation and clearer errors.
- **reference-only**: document how and when a maintainer should use the
  current-checkout artifact, but do not bundle a stale copy.
- **exclude**: do not expose it as a runtime workflow because it is irrelevant,
  unsafe, heavyweight, generated/vendor material, or requires release authority.

## Inventory table

| Source repo artifact | Decision | Bundled target or owner | Reason | Safe check |
|---|---|---|---|---|
| `scripts/regen_skill.py` | reference-only | `references/skill-maintenance.md` and `references/testing-guide.md` | It is the authoritative in-checkout generator and mutates `pyod/skills/` by design. Bundling a copy would go stale and could regenerate the wrong tree. Maintainers should run the current checkout's script after KB or skill-marker changes. | `python scripts/regen_skill.py --check`; `python -m pytest pyod/test/test_regen_skill.py -q`. |
| `scripts/render_agentic_demo.py` | reference-only | This file's docs-rendering note and `references/troubleshooting.md` | It requires Playwright plus Chromium and writes a docs figure. The dependency and browser install are too heavy for a default safe helper. Run only when the HTML demo/figure changed and the maintainer authorizes browser prerequisites. | Import/help is not enough; use only after `pip install playwright` and `playwright install chromium` are explicitly allowed. |
| Generated helper for repo surface | adapt | `scripts/repo_surface_check.py` | PyOD did not ship a single non-mutating surface checker. The bundled helper distills package metadata, key-file, test-file, command, and optional import checks into a safe diagnostic. | `python scripts/repo_surface_check.py --help`; run against a checkout. |
| `examples/*.py` detector/ADEngine examples | route elsewhere | `classic-detectors`, `automated-lifecycle`, `specialized-modalities`, or `model-operations` | These are end-user runtime examples, not maintainer workflow scripts. They should be distilled by the owning user-facing sub-skill when needed. | Native example candidates are selected by those sub-skills, not here. |
| `examples/agentic_demo.html` | reference-only | `references/skill-maintenance.md` and docs notes | HTML demo source is relevant only to docs figure synchronization. It is not a maintainer automation script and should not be copied into this generated skill. | If changed, run the current checkout's rendering workflow with explicit browser authorization. |
| `docs/examples/*.rst` | distilled reference | `references/repo-layout.md` and `references/skill-maintenance.md` | Docs pages explain public workflows; this sub-skill distills only maintenance implications. End-user workflows route to sibling sub-skills. | Docs build or focused API tests, depending on edited snippets. |
| `pypi_build_commands.txt` | exclude | none | Release/publishing commands can involve credentials and irreversible external side effects. This sub-skill does not authorize publication. | Ask an authorized maintainer for an explicit release procedure and approval. |
| `setup.py` | exclude as script | `references/repo-layout.md` notes metadata ownership | It is only a packaging shim in this tree; maintainer decisions belong in `pyproject.toml` and package metadata tests. | Metadata/installer focused tests. |
| `.github/` workflows | exclude from runtime | none | CI infrastructure is useful context but not a public runtime skill workflow. Avoid duplicating CI internals in this sub-skill. | Use local focused tests instead of relying on CI-only paths. |

## Why `repo_surface_check.py` is bundled

Maintainer prompts often start with incomplete context: "I changed the skill
installer", "the CLI skill install tests fail", or "add a detector and refresh
od-expert". The bundled checker gives a future agent a deterministic preflight
that answers:

- Are expected source, docs, scripts, packaged skill files, and maintainer tests
  present in this checkout?
- Which optional extras and console entry points are declared in metadata?
- Are relevant commands (`python`, `pytest`, `pyod`, `pyod-install-skill`) on
  `PATH`?
- If requested, can the selected Python import `pyod` and run `pyod info`?

It never edits files, installs packages, launches servers, renders browsers, or
publishes artifacts.

## Non-bundling rationale for mutating source scripts

`regen_skill.py` and `render_agentic_demo.py` are intentionally kept as
current-checkout commands because they are tightly coupled to PyOD's source tree
and generated artifacts. This skill provides the decision rules, focused checks,
and troubleshooting steps; the maintained source scripts remain authoritative
for actual mutation of PyOD files.
