---
name: scientific-agent-skills
description: "Maintains the Scientific Agent Skills repository: adding or
  updating Agent Skills, validating SKILL.md frontmatter and repo tests,
  planning isolated skill suites, running or triaging security scans, and
  keeping catalog/release evidence aligned. Use for
  K-Dense-AI/scientific-agent-skills checkout tasks, skills-ref validate,
  tests/_meta, tests/run_all.py, scan_pr_skills.py, scan_skills.py,
  metadata.version, allowed-tools, openclaw/hermes metadata, docs/skills.md, and
  scanner findings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Scientific Agent Skills Repository Maintenance

Use this repo skill when the user is editing, reviewing, validating, testing, or preparing a pull request for the `K-Dense-AI/scientific-agent-skills` repository. It is a maintainer skill for the skill collection itself; it is not the route for using RDKit, Scanpy, Paperclip, or any other scientific workflow skill.

## First decision

| User intent | Read |
|---|---|
| Add a new skill, update an existing skill, fix frontmatter/metadata, decide whether content belongs in `references/`, `scripts/`, or `assets/`, or update catalog/diagram artifacts | `sub-skills/skill-authoring/SKILL.md` |
| Choose validation commands, run `skills-ref`, diagnose `tests/_meta`, add `tests/<skill>/`, edit `tests/skill-requirements.toml`, or use `tests/run_all.py --isolated` | `sub-skills/validation-testing/SKILL.md` |
| Run changed-skill or weekly security scans, handle missing `SKILL_SCANNER_LLM_API_KEY`, interpret scanner findings, or update `docs/security-triage.md` | `sub-skills/security-scanning/SKILL.md` |
| Check repository layout, source snapshot, selected evidence, or staleness before refreshing this generated repo skill | `references/repo-overview.md`, `references/repo-provenance.md` |
| Diagnose cross-cutting repo failures or confusing policies before touching files | `references/troubleshooting.md` |

## Repository setup defaults

1. Work from the repository root of a target checkout.
2. Prefer the repository's `uv` workflow for Python 3.13 tooling:

   ```bash
   uv sync --python 3.13
   ```

3. Do not install every scientific dependency into the project environment. Individual skills have mutually incompatible package pins; use `tests/run_all.py --isolated <skill>` for skill-specific suites.
4. Treat generated scan reports, diagrams, caches, and local environments as outputs, not source evidence.
5. Before a PR, run the smallest checks that cover the changed skill and then escalate to repo-wide checks when shared contracts, runner logic, or many skills changed.

## Common route patterns

- **New skill with scripts**: start in `skill-authoring`, then use `validation-testing` to add a suite and isolated requirements entry, then use `security-scanning` to plan the PR scan.
- **Existing skill update**: read the current skill first, bump `metadata.version`, test only changed examples/scripts, and run focused validation before broad checks.
- **CI failure**: identify whether it came from skill spec validation, repo-specific metadata rules, `tests/_meta`, a per-skill suite, or the security scanner; then enter the matching sub-skill.
- **Scanner finding**: never fix from the finding text alone. Inspect the cited files, verify whether they exist, compare behavior to the skill's documented service, and check the triage reference for known false-positive classes.

## Safety and scope boundaries

- Do not make medical, scientific, or regulatory claims by editing a skill without evidence from the package/service docs and tests that skill targets.
- Do not put tests, fixtures, scratch data, or generated reports inside a runtime `skills/<name>/` package.
- Do not add secrets, private URLs, unpublished data, local paths, or environment names to skill files.
- Do not run networked security scans, upload reports, create releases, or mutate tags unless the user explicitly authorizes that side effect.
- Avoid using this skill when the task is ordinary scientific analysis with an installed package; route to the package-specific scientific skill instead.

## Provenance and refresh

Read `references/repo-provenance.md` before relying on this generated repo skill for a checkout at a different commit, branch, version, or dirty state. If the repository policy files, CI workflows, test contract, scanner scripts, or catalog layout have changed, refresh this repo skill before using it for high-stakes maintenance.
