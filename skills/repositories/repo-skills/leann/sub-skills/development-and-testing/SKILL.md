---
name: development-and-testing
description: "Modify and validate the LEANN monorepo with package-aware setup,
  focused tests, native-build diagnostics, documentation policy, and guarded
  packaging or release preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LEANN Development and Testing

Use this sub-skill for checkout maintenance: package architecture, `uv` setup,
focused tests, lint/pre-commit, submodules, native builds, contributor docs,
version alignment, and release planning.

## Route First

- For ordinary package-user installation or first use, return to the
  [LEANN root skill](../../SKILL.md). Do not turn a package-user issue into a
  source-build task.
- For choosing or operating HNSW, IVF, DiskANN, FlashLib, or FlashLib IVF at
  runtime, use [backends-and-storage](../backends-and-storage/SKILL.md).
- Stay here when changing the checkout, validating a patch, building wheels, or
  preparing a release checklist.

## Operating Sequence

1. Read [architecture and packages](references/architecture-and-packages.md).
   Identify every affected distribution, import namespace, native boundary,
   internal version constraint, and optional backend.
2. Read [development workflows](references/development-workflows.md). Confirm
   Python 3.10+, `uv`, submodule state, OS build prerequisites, and a clean
   understanding of editable versus wheel-installed packages.
3. Select the smallest evidence-bearing checks from the
   [testing guide](references/testing-guide.md). Start with metadata/parser/unit
   tests, then add the affected native backend or application case. Never use a
   placeholder import test as sole proof.
4. Run read-only quality checks before formatters or auto-fixers. Inspect the
   resulting diff after any mutating formatter, pre-commit hook, build, or wheel
   repair step.
5. Apply the contributor documentation rules in the development workflow. Add a
   changelog entry for a feature, breaking change, or important fix; keep the
   roadmap and long-term vision consistent with the actual scope.
6. Before release planning, invoke the bundled
   [version checker](scripts/check_package_versions.py) from its resolved skill
   directory and pass the checkout explicitly:

   ```bash
   python scripts/check_package_versions.py --repo-root "$LEANN_CHECKOUT"
   ```

   A nonzero result is a gate, not permission to bump versions. Follow
   [packaging and release safety](references/packaging-and-release-safety.md).
7. Diagnose setup, collection, native-link, dependency, version, or policy
   failures with [troubleshooting](references/troubleshooting.md).

## Hard Safety Boundaries

- Never bump versions, commit, tag, push, create a release, upload artifacts, or
  publish to PyPI/Hugging Face automatically.
- Require separate explicit authorization for each mutating release stage and
  verify credentials, target repository, exact version, commit, and artifacts
  immediately before it.
- Do not run credentialed upload helpers or the all-package build/repair helper
  as routine validation. Reproduce only the necessary safe build/test step.
- Do not claim CPU tests validate CUDA, MPS, DiskANN, or another unprepared
  native backend. Record skipped optional coverage and why.
