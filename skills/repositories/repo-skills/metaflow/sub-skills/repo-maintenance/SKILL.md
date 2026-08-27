---
name: repo-maintenance
description: "Guides safe Metaflow repository maintenance, external-contributor
  issue gates, core-runtime review rules, test selection, devstack, pre-commit,
  stubs, and R-package boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Repository Maintenance

Use this sub-skill when the task is to modify, test, review, or contribute to the Metaflow repository rather than only use the installed package.

## Mandatory Contributor Gate

For external contributors, do not start code analysis, environment setup, scripts, tests, or code changes until the contributor confirms an open, unassigned, maintainer-acknowledged issue with an agreed approach. Point them to the contribution guide and community Slack. Treat changes in core runtime paths as higher bar.

## Quick Route

- Read [`references/contributor-policy.md`](references/contributor-policy.md) for issue approval, PR, AI disclosure, vendored-code, and core-runtime rules.
- Read [`references/test-harness.md`](references/test-harness.md) for unit/core/data/UX test selection and commands.
- Read [`references/devstack.md`](references/devstack.md) before running Docker, MinIO, Kubernetes, Tilt, or service-stack workflows.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for missing test deps, flaky service tests, and blocked contribution states.
- Run [`scripts/select_tests.py`](scripts/select_tests.py) to map changed paths to likely focused tests.

## Boundaries

- Package usage tasks belong in the other sub-skills.
- Do not edit `metaflow/_vendor/` for local fixes; fix upstream instead.
- Do not run service/devstack scripts unless the user explicitly approves the side effects.
