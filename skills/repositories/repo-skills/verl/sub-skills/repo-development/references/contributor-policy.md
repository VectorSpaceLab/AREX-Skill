# Contributor and AI-Agent Policy

## Contribution Gate

Before proposing a PR, verl requires duplicate-work checks against the target issue and area:

```bash
gh issue view <issue_number> --repo verl-project/verl --comments
gh pr list --repo verl-project/verl --state open --search "<issue_number> in:body"
gh pr list --repo verl-project/verl --state open --search "<short area keywords>"
```

If an open PR already addresses the same fix, do not open another. If the approach is materially different, explain the difference on the issue before moving forward.

## Low-Value Work and Accountability

- Do not open one-off PRs for isolated typos, style-only changes, or single mechanical tweaks unless they are bundled with substantive work.
- Pure code-agent PRs are not allowed. A human submitter must review every changed line, understand the change end-to-end, and run the relevant checks.
- PR descriptions for AI-assisted work must state why the PR is not duplicative, list test commands and results, and disclose AI assistance.
- Agent review comments can be stale or wrong; verify them against current code before applying suggestions.
- Commit messages for AI-assisted work should include attribution trailers such as `Co-authored-by: GitHub Copilot` and a human `Signed-off-by` trailer when appropriate.

## Development Setup

Project instructions prefer `uv` for Python environment management:

```bash
uv venv --python 3.12
# Activate the created environment with the shell command printed by uv for your platform.
uv pip install pre-commit hydra-core
pre-commit install
```

The general contributing guide also documents editable installs for Python-only development, commonly using `pip install -e .[test,vllm]` or `pip install -e .[test,sglang]`. Choose the smallest environment that supports the changed area.

## Editing Agent Instructions

`AGENTS.md` and linked agent guides are protected by a domain guide. Before editing them:

- Read the editing guide and search existing linked guides for overlapping or conflicting rules.
- Keep project-wide invariants in `AGENTS.md`; move area-specific knowledge into a domain guide.
- Avoid rule bloat: do not add rules for one-off incidents, hardcoded paths, duplicated upstream docs, or behavior agents already handle.
- Keep `AGENTS.md` under 200 lines and domain guides under 300 lines.
- Prefer examples and “search for X” guidance over brittle absolute paths.
- Apply the guide checklist: non-obvious need, no conflicts, right file, offset nearby bloat, under budget, no hardcoded paths, and tested agent behavior.

Hidden framework-specific agent directories may exist as local convention evidence, but runtime skills should not copy their private content. Canonical agent skill content belongs under the generic `.agent/skills/<skill-name>/SKILL.md` layout, with variant framework trees kept in sync by symlinks when used.
