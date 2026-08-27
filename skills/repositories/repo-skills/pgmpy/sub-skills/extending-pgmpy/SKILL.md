---
name: extending-pgmpy
description: "Extend pgmpy with canonical algorithms, CI tests, scores, metrics,
  datasets, and example models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Extending pgmpy

Use this sub-skill when the task is to add or review a new public pgmpy extension surface: a causal discovery algorithm, conditional independence test, structure score, metric, dataset, or example model. The goal is a focused contribution that follows pgmpy's canonical package layout and template contracts.

Do not use this sub-skill for routine package usage. Route ordinary modeling/factors, structure learning, inference/simulation, causal effects, and data/I/O tasks to their dedicated pgmpy sub-skills. Do not use it for release automation, broad repository maintenance, or R-based bnRep model conversion.

## Read first

- [Extension templates and base contracts](references/extension-templates.md): category-by-category destination, base class, required methods/tags, registry hooks, and template responsibilities.
- [Contributor workflows](references/contributor-workflows.md): TDD workflow, focused pytest selection, docs/examples updates, optional dependency guards, and no-commit/no-push guidance.
- [Troubleshooting](references/troubleshooting.md): deprecated estimator routing, registration failures, template/base-class drift, optional dependencies, schema validation, and test selection.
- [Static extension check script](scripts/extension_template_check.py): safe, read-only helper for checking expected template files, package placement, class/tag/method hints, and registry/test-list reminders.

## Operating procedure

1. Classify the extension category and pick the canonical package destination from [extension-templates.md](references/extension-templates.md). If the user proposes `pgmpy.estimators` for new functionality, reroute to the canonical package instead and keep legacy estimator compatibility separate.
2. Start from the matching `devtools/extension_templates` scaffold in the user's pgmpy checkout, but do not copy template text into this skill. Fill every TODO, follow existing implementations, and update the matching template whenever a base-class API or required tag changes.
3. Implement the public class contract: methods and fitted attributes for discovery algorithms, `_CITestResult` payloads for CI tests, cached `_local_score` for scores, `_evaluate` for metrics, loader/tag contracts for datasets and example models.
4. Register/export where the package expects it, update tests and public docs/examples when a user-facing API appears, and guard optional torch/Pyro, litellm/provider, plotting, or network-bound behavior.
5. Validate narrowly first: run the relevant new test file or selected existing family tests, then broaden only as needed. Run pre-commit when available. Never run `git commit` or `git push` for the user.

## Useful static check

From any working directory, after installing pgmpy or while editing a checkout, run the bundled helper with a checkout path when checking new files:

```bash
python <path-to-extending-pgmpy>/scripts/extension_template_check.py --repo <pgmpy-checkout> --category structure-score --module-name my_score --class-name MyScore --registry-name my-score
```

For a quick read-only inventory of template/package/test directories:

```bash
python <path-to-extending-pgmpy>/scripts/extension_template_check.py --repo <pgmpy-checkout> --category all
```

The script does not mutate files. Treat it as a placement/contract reminder; still inspect source and run focused tests.
