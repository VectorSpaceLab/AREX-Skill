---
name: model-authoring
description: "Guides ONNX model construction, loading, saving, serialization,
  composition, extraction, external data, and large-model utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ONNX Model Authoring

Use this sub-skill when a task needs to create or transform an ONNX `ModelProto`, `GraphProto`, `NodeProto`, or `TensorProto`; load or save model files; inspect model IO; compose or extract graphs; or manage external/large tensor data.

## Workflow

1. Choose an in-memory representation: `onnx.helper` for graphs/nodes/types, `onnx.numpy_helper` for NumPy and container values, or `onnx.parser` when a compact text fixture is easier.
2. Set explicit model inputs, outputs, initializers, and `opset_imports`. Do not rely on a guessed opset when a model will be shared.
3. Run `onnx.checker.check_model(model)` before saving or handing the model to another sub-skill.
4. Save with `onnx.save_model`/`onnx.save`; choose the format explicitly when using file-like objects or nonstandard extensions.
5. For a large initializer, use external data APIs and keep locations relative to the model file. Do not load huge external tensors into memory merely to inspect graph structure.
6. After composition, extraction, dimension updates, or constant replacement, re-run checker and, when useful, shape inference.

## Route to References and Helpers

- Read `references/api-reference.md` for verified signatures and parameter relationships.
- Read `references/workflows.md` for tiny model, format round-trip, compose/extract, symbolic-dimension, and external-data recipes.
- Read `references/data-formats.md` for protobuf/textproto/JSON/onnxtxt, graph naming, types, and external-data conventions.
- Read `references/troubleshooting.md` before retrying an IO, dtype, path, or large-model failure.
- Run `scripts/create_tiny_model.py --help` to create a deterministic fixture without a source checkout.
- Run `scripts/inspect_model_io.py --help` to inspect inputs, outputs, initializers, nodes, and optional inferred value information.

## Scope Boundaries

- Use `validation-and-conversion` for checker details, parser/printer syntax, shape/type inference, inlining, and opset conversion.
- Use `reference-and-backend-tests` when the question is whether a model computes expected values.
- Use `operator-spec-maintenance` when the task changes ONNX schemas, operator definitions, function bodies, or generated spec artifacts.
