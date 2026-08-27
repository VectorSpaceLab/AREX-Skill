---
name: operator-spec-maintenance
description: "Guides ONNX operator-schema maintenance, function bodies, shape
  inference, reference ops, node tests, proto regeneration, and maintainer
  gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ONNX Operator Spec Maintenance

Use this sub-skill when a task changes ONNX operator schemas, function bodies, shape inference, reference implementations, backend node tests, version-converter adapters, `.in.proto` sources, generated docs, or maintainer validation gates.

## Workflow

1. Read the operator-change checklist before editing schema files.
2. Decide whether the requested behavior belongs in a new function, a new operator version, or a helper/refactor that preserves compatibility.
3. Edit source-of-truth files first: `onnx/defs/<domain>/defs.cc`, `old.cc`, `*.h`, `.in.proto`, reference ops, or node tests.
4. Use named shape-inference helpers rather than inline lambdas when practical.
5. Add or update reference implementations and node tests for user-visible behavior.
6. Regenerate docs/protos/coverage only after the source files are correct.
7. Run the focused Python/C++/lint gates that match the change.

## Route to References and Helpers

- Read `references/operator-maintenance.md` for the edit checklist and file map.
- Read `references/shape-inference-patterns.md` for C++ inference helper patterns and test guidance.
- Read `references/onnx-text-syntax.md` for function-body and parser syntax conventions.
- Read `references/troubleshooting.md` before retrying a build, test, or generated-file failure.
- Run `scripts/operator_change_checklist.py --help` for a task-specific checklist summary.

## Scope Boundaries

- Use `model-authoring` for ordinary graph/tensor/model creation.
- Use `validation-and-conversion` for checker/parser/printer/version-converter usage on existing models.
- Use `reference-and-backend-tests` when the task is only to compare outputs, not change the spec or its implementation.
