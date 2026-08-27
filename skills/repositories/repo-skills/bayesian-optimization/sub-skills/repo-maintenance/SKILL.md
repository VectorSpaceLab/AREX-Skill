---
name: repo-maintenance
description: "Maintain a BayesianOptimization checkout with safe install, test,
  lint, docs, CI-matrix, and release-boundary guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repo Maintenance

Use this sub-skill only when the user is maintaining or editing a
`bayesian-optimization` source checkout. It covers development installs,
focused native tests, lint/format decisions, docs/notebook checks, CI matrix
expectations, and safe debugging paths.

For package usage questions, route away from maintenance:

- Optimizer construction, registration/probing, fitting, save/load, or
  prediction workflows: [`../optimizer-workflows/SKILL.md`](../optimizer-workflows/SKILL.md)
- Acquisition-function selection or exploration/exploitation controls:
  [`../acquisition-control/SKILL.md`](../acquisition-control/SKILL.md)
- Constraints, typed parameters, categorical/integer domains, sequential domain
  reduction, or advanced examples:
  [`../advanced-domain-features/SKILL.md`](../advanced-domain-features/SKILL.md)

## Maintainer workflow

1. Identify touched checkout files and choose the smallest native checks from
   [`references/development-workflows.md`](references/development-workflows.md).
2. Prefer non-mutating verification first: focused `pytest`, Ruff format check,
   and Ruff lint check.
3. Use [`scripts/select_native_checks.py`](scripts/select_native_checks.py) to
   print recommended command groups from touched paths or capability flags. The
   helper only prints commands; it does not execute them.
4. Escalate to full unit, notebook, docs, or CI-matrix coverage only when the
   touched files affect those surfaces or when preparing a broad change.
5. Use [`references/troubleshooting.md`](references/troubleshooting.md) for
   Python/NumPy marker conflicts, pre-commit or Ruff failures, notebook timeouts,
   docs build failures, import confusion, and release/publish limits.

## Safety rules

- Treat commands as checkout-maintenance commands, not runtime user guidance.
- Do not run `scripts/format.sh` unless the user explicitly wants formatting or
  automatic fixes; it mutates source files.
- Do not use `scripts/check_precommit.sh` as a routine verification shortcut; it
  installs hooks before running all files. Prefer direct non-mutating Ruff or
  pre-commit commands when verification is enough.
- Never provide credentialed publishing steps. PyPI publishing is release-only
  and guarded by repository secrets.
