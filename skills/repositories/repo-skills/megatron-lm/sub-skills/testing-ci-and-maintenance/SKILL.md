---
name: testing-ci-and-maintenance
description: "Megatron-LM repository testing, CI, golden-value, formatting, PR,
  and maintenance workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# testing-ci-and-maintenance

Use this sub-skill when the task is about Megatron-LM repository development rather than package-user training:

- adding, selecting, or running unit tests and functional tests;
- editing CI recipe YAML, H100 or GB200 scopes, golden values, or CI labels;
- triaging CI logs, artifacts, pytest failures, golden drift, lint failures, or container/dependency CI failures;
- updating base image pins, dependency lock files, API compatibility checks, or nightly main-to-dev sync PRs;
- preparing contribution/PR steps, splitting a PR by CODEOWNERS ownership, or responding to repo issues.

Route away from this sub-skill for:

- package installation or environment setup for Megatron-LM users: use `install-and-environment`;
- research training command construction, data preprocessing, SLURM launch templates, or checkpoint training flows: use `training-cli-and-data` and, when relevant, `checkpointing-and-conversion`;
- model API or parallelism strategy questions: use `core-models-and-parallelism`.

## Mandatory read order

1. For test layout, pytest commands, recipe YAML fields, and H100/GB200 scope conventions, read `references/testing-reference.md`.
2. For CI labels, logs/artifacts, golden-value refresh, internal CI trigger safety, base-image/dependency maintenance, and nightly sync, read `references/ci-maintenance-reference.md`.
3. For PR creation, signing, draft PRs, forks, CODEOWNERS/final review, issues, and PR splitting, read `references/contribution-reference.md`.
4. For failure diagnosis, read `references/troubleshooting.md` before proposing fixes.

## Bundled scripts

- `scripts/check_golden_values.py` is a copied/adapted finite-value checker for golden JSON files. Prefer this bundled checker when validating an arbitrary golden JSON fixture outside the repo CI path.
- `scripts/summarize_recipe_scopes.py` is a non-mutating YAML summarizer for recipe scope/platform/environment coverage and broken/disabled markers.

## Operating rules

- Use `Run tests` for lightweight full-scope PR validation and `Run functional tests` when numerics, new functional cases, re-enabled cases, or golden values are involved.
- Treat `container::lts` as opt-in only. Do not add the label, edit LTS pins, or run LTS-specific maintenance unless the user explicitly asks for LTS validation or an LTS bump.
- Unit tests are distributed by default; do not run plain `pytest tests/unit_tests` as a CI-parity command when GPU/distributed context matters.
- Do not hand-edit generated lockfiles or golden JSONs. Regenerate `uv.lock` with the package manager inside the project container; refresh goldens from CI artifacts and summarize relative differences.
- Never run the internal GitLab CI trigger without a dry run first; the real trigger force-pushes the current branch to an internal `pull-request/<branch>` ref.
- Draft PRs are mandatory. Contributors push branches to forks and open draft PRs against the upstream repository; do not push contributor branches directly to upstream.
