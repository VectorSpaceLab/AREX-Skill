---
name: repo-development
description: "Guide safe MNE-Python repository maintenance and editing while
  preserving human review, public API, documentation, test, and changelog
  rules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# MNE-Python repository development router

Use this sub-skill when the user asks for MNE-Python repository maintenance: code edits, tests, documentation, public API exposure, changelog fragments, contributor workflow, import-location checks, deprecations, optional-dependency handling, or local CI-style troubleshooting.

## Load order

1. For safe edit/test/doc/changelog workflows and the AI-assistance policy, read [references/contributor-workflows.md](references/contributor-workflows.md).
2. For lazy public API stubs, API reference entries, docstring rules, cross-references, and public API checklists, read [references/api-surface-and-docs.md](references/api-surface-and-docs.md).
3. If a local check fails, read [references/troubleshooting.md](references/troubleshooting.md).
4. When validating that `import mne` resolves to the checkout being edited, run or adapt [scripts/check_mne_checkout.py](scripts/check_mne_checkout.py) in the maintainer environment.

## Own these requests

- Planning safe MNE-Python code edits with human review checkpoints required by the project AI policy.
- Choosing focused local commands for tests, docstring checks, pre-commit, documentation builds, changelog checks, import nesting, and dataset availability.
- Adding, moving, documenting, or deprecating public functions/classes/methods while keeping lazy-loader `.pyi` stubs, `__all__`, doc API pages, tests, and changelog fragments aligned.
- Diagnosing failures caused by importing the wrong checkout, missing optional dependencies, unavailable testing/sample data, stale docs builds, changelog author names, docstring validation, deprecation warnings, or import-nesting regressions.
- Inventorying maintainer helper scripts safely: use bundled helpers here when available; treat source release/GitHub/credential automation as excluded or human-only.

## Route elsewhere

- User data analysis, file loading, preprocessing, visualization, source modeling, statistics, decoding, simulation, CLI usage, dataset caching, and runtime MNE workflows belong to the analysis-oriented sibling sub-skills.
- Release engineering, publishing, GitHub API actions, credential-bearing automation, and account/CI administration are outside this operating sub-skill unless the user provides an explicit human-supervised maintenance task.
- Do not draft issue or PR comments as if they are ready to paste. Provide technical notes that a human contributor can review, understand, test, and rewrite under their own responsibility.

## Operating rules

- Treat AI-assisted repository changes as drafts. The human contributor must review, understand, test, and disclose any AI assistance before submission.
- Do not submit or recommend submitting fully automated issues or pull requests. Do not produce unreviewed AI-generated PR descriptions or issue comments.
- Prefer small, focused patches with matching tests and documentation. Avoid unrelated refactors.
- Do not depend on the construction checkout or original evidence files at runtime. Source paths mentioned in references are provenance only; operate on the user's active MNE-Python checkout and the files in this skill subtree.
- When source guidance conflicts, preserve the style of the edited file and ask the human maintainer before broad style changes.
