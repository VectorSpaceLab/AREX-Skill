# Repository Overview

## When to read

Read this when you need a compact map of the `scientific-agent-skills` repository before editing a skill, choosing tests, or triaging a security finding.

## What this repository is

`scientific-agent-skills` is a public collection of Agent Skills for scientific and research workflows. The repository is mostly skill packages under `skills/<skill-name>/`, a repository-level test harness under `tests/`, generated documentation under `docs/`, and CI/security tooling around the Agent Skills specification.

The repo skill you are reading is for **maintaining the collection**, not for using one of the scientific skills. If the user asks to run Scanpy, RDKit, Paperclip, BIDS, or another domain workflow, route to that specific skill instead.

## Layout map

| Path | Role |
|---|---|
| `skills/<name>/SKILL.md` | Required runtime documentation for one canonical repository skill. Directory basename and frontmatter `name` must match. |
| `skills/<name>/references/` | Optional long-form docs loaded only when needed. Keep links relative to the skill root. |
| `skills/<name>/scripts/` | Optional helpers the agent may run. Script-bearing skills need repository-level tests and a `skill-requirements.toml` entry. |
| `skills/<name>/assets/` | Optional templates/static assets that the skill loads. |
| `tests/<name>/` | Per-skill tests for `skills/<name>/scripts/`; never put tests under `skills/<name>/`. |
| `tests/_meta/` | Repo-wide structural and coverage guard; parses every canonical skill without importing skill code. |
| `tests/_contract/` | Shared assertions for frontmatter, links, scripts, bytecode, office/schematic shared copies, and CLI/demo helpers. |
| `tests/run_all.py` | Runs one pytest process per skill, or one isolated `uv` environment per skill with `--isolated`. |
| `tests/skill-requirements.toml` | Per-skill isolated dependency manifest. Use `packages = []` for standard-library-only scripts. |
| `scan_pr_skills.py` | Changed-skill security scan/report helper used by PR workflow. |
| `scan_skills.py` | Weekly/full scanner with incremental cache that writes `docs/security-report.md` and `.json`. |
| `docs/skills.md` | Catalog of included skills and descriptions. Update when new skills change the public index. |
| `docs/security-triage.md` | Human verdicts on automated scanner findings and known false-positive classes. |
| `.github/workflows/` | CI source of truth for validation, tests, security scan, and release behavior. |

## Maintenance task boundaries

- **Skill authoring** owns content placement, scope, frontmatter, metadata, versioning, catalog/diagram decisions, and no-secret rules.
- **Validation/testing** owns `skills-ref`, repo-specific metadata checks, `tests/_meta`, per-skill tests, and isolated environments.
- **Security scanning** owns scanner commands, credentials, generated reports, and finding triage.

When a task spans all three, handle them in that order: author/update the skill, validate/test it, then scan/triage it.

## Evidence cautions

- `docs/security-report.*` and `docs/images/*.png` are generated outputs; use them as output examples, not as primary policy.
- The repository policy references diagram-generation tooling, but this snapshot did not include the generator script. Do not invent diagrams; check the target checkout and record the blocker if the required tool is absent.
- The top-level `skills/` directory is the canonical skill collection. Generated DisCo repo-skill output under `skills/disco/` and review artifacts under `skills/tests/` are construction outputs, not canonical collection entries.
