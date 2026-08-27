---
name: validation-and-conversion
description: "Guides ONNX checker, shape inference, parser, printer,
  version-converter, inliner, and CLI validation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ONNX Validation and Conversion

Use this sub-skill when a task is about checking whether an ONNX model or node is legal, inferring shapes or types, parsing or printing ONNX text, converting opset versions, or inlining model-local functions.

## Workflow

1. Start with the smallest artifact that fails: a node, graph, or complete model.
2. Validate structural legality first with `onnx.checker.check_node`, `check_graph`, or `check_model`.
3. For model shape questions, call `onnx.shape_inference.infer_shapes` on a `ModelProto`. Use `infer_shapes_path` for file paths or very large models.
4. For ONNX text, keep syntax close to the grammar in `references/cli-reference.md` and `references/workflows.md`; parse with `onnx.parser.parse_model` or `parse_graph`, then validate the result.
5. For opset changes, use `onnx.version_converter.convert_version` only when the target path is supported; otherwise keep the original opset and surface the mismatch.
6. For local functions, use `onnx.inliner.inline_local_functions` or `inline_selected_functions` and then re-run checker/inference.
7. Use the `check-model` and `check-node` CLIs when the task is about a serialized protobuf and a safe command-line check is clearer than a Python snippet.

## Route to References and Helpers

- Read `references/api-reference.md` for verified signatures and error classes.
- Read `references/cli-reference.md` for `check-model`, `check-node`, and `backend-test-tools` help output.
- Read `references/workflows.md` for validate/infer/parse/print/convert/inline recipes.
- Read `references/troubleshooting.md` before retrying a syntax, large-model, or conversion failure.
- Run `scripts/validate_convert_model.py --help` before using it on a model file or a generated tiny model.

## Scope Boundaries

- Use `model-authoring` for constructing or saving models and tensors.
- Use `reference-and-backend-tests` when the question is whether the model produces expected outputs.
- Use `operator-spec-maintenance` for schema edits, C++ shape inference, function bodies, and node-test generation.
