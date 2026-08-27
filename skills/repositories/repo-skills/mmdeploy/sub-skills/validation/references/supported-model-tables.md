# Supported Model and Backend Tables

## Purpose

Read this when a user asks for a Markdown table of which model families are covered by which MMDeploy backends. Use the bundled [table helper](../scripts/generate_md_table.py) to turn a regression matrix YAML into a support table.

## Command shape

```bash
python path/to/validation/scripts/generate_md_table.py \
  <regression-matrix-yaml> \
  <output-markdown> \
  [--backends onnxruntime tensorrt torchscript pplnn openvino ncnn]
```

The default backend columns are ONNX Runtime, TensorRT, TorchScript, PPLNN, OpenVINO, and ncnn. Pass `--backends` to produce a smaller table or to match a release note's required ordering.

## What the helper reads

The helper expects a matrix YAML with:

- `globals.repo_url`: base URL used to form model-config links;
- a top-level `models` list;
- each model entry containing `name`, `model_configs`, and `pipelines`;
- each pipeline containing a `deploy_config` that declares its backend and task.

For each model row, the helper loads every pipeline's deployment config, extracts the task type and backend type, then marks a backend column `Y` when at least one pipeline uses that backend. Backends not found in the model's pipelines remain `N`.

## Interpreting generated tables

| Table signal | Interpretation | What it does not prove |
| --- | --- | --- |
| `Y` | The regression matrix includes at least one pipeline for that model/backend pair. | It does not prove the backend package is installed on the current host or that the model passed this run. |
| `N` | No pipeline for that backend was found in the matrix used to generate the table. | It may not mean the backend can never work; it means the selected matrix does not cover it. |
| Task column | Derived from the deploy config task type. | It is only as current as the deployment configs used by the matrix. |
| Model link | Built from `repo_url` and the first model config directory. | It is documentation convenience, not validation evidence. |

Do not copy benchmark result tables verbatim into the skill. Benchmark pages mix historical hardware, precision, datasets, and hand-curated notes. The generated support table is a coverage summary; pair it with [regression reports](regression.md) for pass/fail evidence and with [profiling](profiling.md) for current latency evidence.

## Practical workflow

1. Choose the exact matrix YAML that matches the codebase/release you are summarizing.
2. Choose backend columns deliberately. Do not include a backend column only because it exists in another matrix.
3. Generate a Markdown table into a work or docs output path, not into the runtime skill tree.
4. If a row is surprising, inspect the matrix pipeline list before changing the table manually.
5. If the table is for release notes, rerun the relevant regression subset so table coverage and report status agree.

## Common table-generation pitfalls

- Missing backend column: add it to `--backends`; the helper only emits requested columns.
- All `N` values for a backend: the matrix pipelines may not include that backend or the deploy config failed to load.
- Wrong task names: check that each pipeline's deploy config is current and declares the expected codebase task.
- Broken links: verify `globals.repo_url` and the model config path conventions in the matrix before publishing.
