---
name: "python-simplification"
description: "CLI and Python API workflows for simplifying ONNX models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Python Simplification

Use this sub-skill when the task is to simplify an ONNX model from a file or an
`onnx.ModelProto` with `onnxsim.simplify` or the `onnxsim` CLI.

## Covers

- Static and dynamic input shapes.
- Correctness checking with `check_n`, `check_rtol`, `check_atol`, and
  `input_fill`.
- Input data injection, optimizer skipping, and constant-folding control.
- Provider selection, including the CUDA shortcut behavior.
- External-data output and large tensor warnings.
- Target opset conversion and local function inlining.
- Custom operator schema import for validation.
- Graph diff output after simplification.

## Do not use this sub-skill for

- Custom graph rewriter design, function-rule authoring, or profiling / model
  metrics depth. Hand those off to the sibling `advanced-graph-control`
  sub-skill (`../advanced-graph-control/SKILL.md`).
- Build, install, wheel, C API, Rust, WASM, or packaging troubleshooting.
  Hand those off to the sibling `bindings-and-packaging` sub-skill
  (`../bindings-and-packaging/SKILL.md`).

## Read first

- [API and CLI summary](references/api-and-cli.md)
- [Workflow recipes](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)

## Standard flow

1. Identify whether the caller has an ONNX file or an in-memory `ModelProto`.
2. Decide how shapes and validation inputs will be supplied:
   `overwrite_input_shapes`, `test_input_shapes`, `input_data`, or
   `input_fill`.
3. Choose optimizer and folding controls:
   `skip_optimization`, `skip_constant_folding`, `skip_shape_inference`,
   `skip_fuse_bn`, `mutable_initializer`, `initializers_as_constants`, and
   `inline_functions`.
4. Decide backend and opset behavior: `providers`, `--cuda`, and
   `target_opset_version`.
5. Run simplification, then validate with `check_n` and a direct round-trip
   comparison when needed.
6. Save external data or print graph diff only when asked.

## Helper script

Use [`scripts/simplify_tiny_model.py`](scripts/simplify_tiny_model.py) for a
safe smoke run:

```bash
python scripts/simplify_tiny_model.py --help
python scripts/simplify_tiny_model.py --check-n 3 --input-fill arange --print-summary
python scripts/simplify_tiny_model.py --output tiny-simplified.onnx
```

The script builds a tiny synthetic model, simplifies it with the public API,
validates the result, and never downloads models.

## Common outcomes

- File CLI calls return a simplified ONNX path and, when requested, graph diff
  output.
- Python API calls return `(model_simp, check)`; treat `check=False` as a stop
  signal unless the caller explicitly wants an exploratory run.
- If `providers` is omitted, folding stays on CPU.
- For a fast smoke run, use the bundled helper script with `--print-summary`.

## Routing notes

- The sub-skill accepts the core simplification surface only. For custom
  rewriters and profiling / metrics depth, move to the sibling
  `advanced-graph-control` sub-skill.
- For packaging or backend installation problems, move to the sibling
  `bindings-and-packaging` sub-skill.
- If a provider request fails, consult the troubleshooting table before changing
  the model.
