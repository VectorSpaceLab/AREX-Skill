---
name: repo-build-test
description: "Guides Waymo Open Dataset maintainer workflows for Bazel, Docker,
  wheel packaging, requirements updates, focused tests, and contributor
  diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Repo Build and Test

Use this sub-skill when the task is about maintaining or building the Waymo Open Dataset repository: Bazel targets, full/focused tests, PyPI wheel generation, Docker or Jupyter tutorial containers, requirements updates, package metadata, issue-reporting logs, and contributor workflow.

Read:

- [references/build-and-test.md](references/build-and-test.md) for Bazel, wheel, Docker/Jupyter, requirements, focused test, and log-capture commands.
- [references/contributor-guidance.md](references/contributor-guidance.md) for maintainer and issue-reporting expectations.
- [references/troubleshooting.md](references/troubleshooting.md) for Bazelisk, Python/JAX wheel, TensorFlow/custom-op, Docker path, and requirements update failures.

Run [`scripts/inspect_wod_package_metadata.py`](scripts/inspect_wod_package_metadata.py) to print the distilled package metadata and optional installed distribution version.

Route user-facing data conversion, metrics, motion, latency, or camera workflows to their specialized sub-skills unless the task explicitly edits/builds/tests the repository checkout.
