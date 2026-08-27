# Repository Provenance

Schema: `disco.repo-provenance.v1`

This repo skill was distilled from the OpenSquilla source repository plus local installed-package inspection evidence.

## Source Revision

| Field | Value |
| --- | --- |
| Repository | opensquilla/opensquilla |
| Remote | `https://github.com/opensquilla/opensquilla.git` |
| Branch at capture | `main` |
| Commit | `48b4be2bae77915e917e88b4dbd7c77b1d6e6699` |
| Package distribution | `opensquilla` |
| Package version | `0.5.3` |
| Python support | `>=3.12` |
| Dirty state | Generated `skills/` output was intentionally present; source evidence was inspected at the commit above. |
| Capture date | 2026-08-15 |

## Evidence Used

Evidence included the root package metadata and product READMEs; user documentation for quickstart, CLI, gateway, configuration, providers/models, search, channels, MCP, sessions, memory, operations, sandbox, Skills, MetaSkills, SquillaRouter, TUI, Web UI, and troubleshooting; relevant implementation roots under `src/opensquilla/`; Python tests; Web UI and desktop contract tests; and generated integration reports under `skills/tests/opensquilla/reports/integration/`.

A private CPU-only Python 3.12 inspection environment installed the checkout with the `recommended`, `mcp`, and `dev` extras. Recorded checks passed for `pip check`, package version, root CLI help, and selected CLI/gateway/provider/search/channel/Skill/MetaSkill/memory/sandbox/MCP/router imports. Local catalog inspection recorded 49 providers, 8 public channel families, and 7 search providers.

## Verification Boundaries

No live LLM provider, credentialed search, messaging provider, external MCP client, public gateway, browser UI, Electron desktop, or GPU backend was required. Catalog presence does not prove credentials or end-to-end availability. Source installer, release, live-provider, browser, Electron, and maintainer harness scripts were treated as evidence or reference-only unless explicitly adapted into this self-contained bundle.

The bundled root health script is read-only and depends only on an installed `opensquilla` executable; it does not depend on this source checkout or the private inspection environment.

## Staleness Signals

Refresh or re-verify this skill when the package version or Python range changes materially; CLI command names or JSON contracts move; gateway/Web/TUI/desktop ownership changes; provider/router/search/channel catalogs change; Skill or MetaSkill selection and proposal semantics change; or migration, sandbox, session, memory, diagnostic, and uninstall safety behavior changes.
