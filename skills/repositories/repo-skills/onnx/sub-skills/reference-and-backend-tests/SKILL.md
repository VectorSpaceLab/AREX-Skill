---
name: reference-and-backend-tests
description: "Guides ONNX ReferenceEvaluator usage, reference-op behavior,
  backend test corpus, and bounded backend-data generation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ONNX Reference and Backend Tests

Use this sub-skill when a task needs to execute ONNX with the pure-Python `ReferenceEvaluator`, compare outputs against expected NumPy values, inspect reference operator behavior, work with the backend test corpus, or generate small backend-test data sets.

## Workflow

1. Use `ReferenceEvaluator` when you need a local execution baseline that follows ONNX semantics rather than a framework runtime.
2. If the model already exists, load it and run a tiny, deterministic input dictionary first.
3. For backend-test corpus work, distinguish between safe local node/model cases and real model downloads. Prefer small, source-defined cases for smoke tests.
4. Keep optional dependencies optional: install `onnx[reference]` only when image-decoder/reference workflows need Pillow.
5. When a result differs from a backend/runtime, treat the ONNX spec and reference operator as the source of truth.
6. Use the bounded helper script to create a small backend-test data directory or to smoke-check a tiny model.

## Route to References and Helpers

- Read `references/reference-evaluator.md` for `ReferenceEvaluator` and debugging details.
- Read `references/backend-test-workflows.md` for backend-interface concepts and test-data generation patterns.
- Read `references/troubleshooting.md` before retrying a missing-op, optional-dependency, or download-based backend issue.
- Run `scripts/reference_eval_smoke.py --help` to see the safe tiny-model smoke options.
- Run `scripts/generate_backend_test_subset.py --help` to see the bounded backend-data generator options.

## Scope Boundaries

- Use `model-authoring` for creating or saving models and fixtures.
- Use `validation-and-conversion` for checker, parser/printer, shape inference, and opset conversion.
- Use `operator-spec-maintenance` when the task changes the reference operator implementations or backend node tests themselves.
