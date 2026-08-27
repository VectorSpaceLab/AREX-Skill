---
name: latency-submissions
description: "Guides real-time Waymo Open Dataset latency challenge submissions,
  wod_latency_submission modules, numpy detection inputs and outputs, Docker
  image sources, and latency result conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Latency Submissions

Use this sub-skill when the task is about the Waymo real-time 2D or 3D detection latency challenge: validating a `wod_latency_submission` module, choosing `DATA_FIELDS`, preparing pre-extracted numpy inputs, interpreting `boxes`/`scores`/`classes` outputs, packaging a challenge Docker image source, or converting latency evaluator outputs toward an Objects proto workflow.

Read:

- [references/workflows.md](references/workflows.md) for the module contract, evaluator flow, Docker image-source requirements, and result-conversion flow.
- [references/data-formats.md](references/data-formats.md) for latency numpy field names, previous-frame suffixes, result-directory layout, and 2D versus 3D output shapes.
- [references/troubleshooting.md](references/troubleshooting.md) for import errors, missing `.npy` inputs, output length mismatches, 2D camera restrictions, and objects skipped during conversion.

Useful bundled checks:

- [`scripts/validate_latency_submission.py`](scripts/validate_latency_submission.py) imports a user-provided module or file, creates tiny fake numpy arrays for its `DATA_FIELDS`, calls `initialize_model()` and `run_model(...)`, and validates the returned arrays without importing the Waymo package.
- [`scripts/make_latency_fixture.py`](scripts/make_latency_fixture.py) creates or checks a tiny latency result directory and writes a JSON summary without requiring the Waymo package.

Route ordinary metric accuracy to `metrics-evaluation`, raw `Frame` conversion to `dataset-utils`, and generic Docker/PyPI package build work to `repo-build-test`.
