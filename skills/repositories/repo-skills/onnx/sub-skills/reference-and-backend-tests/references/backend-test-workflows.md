# ONNX Backend Test Workflows

## What the backend corpus is for

The backend test suite captures expected ONNX behavior as node and model cases. Node cases are created in Python/Numpy and are also used as documentation snippets. Model cases include real model downloads and small, self-contained model fixtures.

## Safe local workflow

1. Start with a small reference model or a single node case.
2. Use `onnx.backend.test.cmd_tools.generate_data` only for bounded, local smoke generation.
3. Keep real model downloads out of ordinary smoke checks unless the task explicitly needs them.
4. If the task is about the backend interface itself, inspect `onnx.backend.base.Backend` and `BackendRep` first.

## Bounded generation pattern

The backend corpus API collects test cases from `onnx.backend.test.case.*` modules. A safe helper can import the corpus, filter to node or simple model cases, and write a tiny output directory for a selected local smoke test. That is enough to prove the generator works without downloading real models.

## When not to use it

- Do not use backend corpus generation as a substitute for ONNX validation or shape inference.
- Do not assume a backend data dump proves a runtime backend passes the full suite.
- Do not chase real-model downloads during a normal model-authoring or validation task.

## Useful package facts

- `onnx.backend.base.Device(device)` and `Backend`/`BackendRep` are the public backend base classes.
- `onnx.backend.test.cmd_tools.main()` exposes the `backend-test-tools` CLI, with `generate-data` as the available subcommand in ONNX 1.23.0.
