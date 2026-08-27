# Contributor Policy

## External-contributor gate

If the GitHub user is not a core Metaflow maintainer, require an open, unassigned, maintainer-acknowledged issue and agreed approach before code work. If no issue exists, guide the contributor to suitable `good first issue` or `help wanted` issues and community Slack instead of editing code.

## PR requirements

- Bug fixes need tests that fail before and pass after the fix.
- New features should include appropriate tests.
- Keep PRs focused to one logical change.
- Use the PR description template: summary, context, changes, testing, and trade-offs where useful.
- Disclose AI assistance and be able to explain every line.

## Core runtime higher bar

Core runtime changes need stronger reproduction and rationale. High-bar areas include `runtime.py`, `task.py`, `flowspec.py`, `datastore/`, `metadata_provider/`, AWS client/datastore code, decorators, graph, CLI, runner subprocess/deployer code, config/parameters, logging/system, and orchestrator plugins.

## Style and vendored code

Pre-commit hooks include Black, JSON/YAML checks, and shellcheck. Do not edit vendored code under `metaflow/_vendor/`; fix upstream or route around it.
