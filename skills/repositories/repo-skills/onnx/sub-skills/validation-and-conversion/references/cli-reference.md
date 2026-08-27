# ONNX CLI Reference

## `check-model`

```bash
check-model model.onnx
```

- Accepts a serialized model path and loads it before running `onnx.checker.check_model`.
- Use this when a model file already exists and a quick legality check is enough.
- For large models with external data, keep the data files next to the model or rely on the model path form.

## `check-node`

```bash
check-node node.pb
```

- Accepts a serialized `NodeProto` file and validates it with the checker.
- Use this when the failing artifact is a single node rather than a whole graph.

## `backend-test-tools`

```bash
backend-test-tools generate-data -o OUTPUT_DIR
```

- Generates backend test data from the repository's built-in ONNX backend cases.
- In this skill, treat it as a bounded helper for tiny, local smoke generation only.
- Do not assume it should be used for real-model downloads or long-running corpus generation.

## Safe usage notes

- These CLIs are wrappers around the public Python APIs in `onnx.bin.checker` and `onnx.backend.test.cmd_tools`.
- Run `--help` before relying on a flag in a future environment.
- If a command fails with a `ValidationError`, inspect the model structure first; if it fails with a path or file issue, verify external data and the file extension.
