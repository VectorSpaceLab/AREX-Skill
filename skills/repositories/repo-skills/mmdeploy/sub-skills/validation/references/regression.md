# Regression Matrix Automation

## Purpose

Read this when a maintainer or advanced user wants to run MMDeploy regression matrices across codebases, backends, model configs, or precision modes. Use the bundled [regression helper](../scripts/regression_test.py), which preserves the repository runner's filtering, checkpoint caching, conversion-only mode, precision mode, and Excel report workflow.

## Safe command shapes

Fast convert-only subset:

```bash
python path/to/validation/scripts/regression_test.py \
  --repo-root <mmdeploy-checkout> \
  --codebase mmdet \
  --backends tensorrt \
  --models maskrcnn \
  --work-dir <work-dir> \
  --checkpoint-dir <checkpoint-cache> \
  --device cuda:0 \
  --log-level INFO
```

Precision/metric subset:

```bash
python path/to/validation/scripts/regression_test.py \
  --repo-root <mmdeploy-checkout> \
  --codebase mmdet mmpose \
  --backends onnxruntime tensorrt \
  --models resnet maskrcnn \
  --work-dir <work-dir> \
  --checkpoint-dir <checkpoint-cache> \
  --device cuda:0 \
  --log-level INFO \
  --performance
```

Avoid running a full default matrix unless the user explicitly authorizes the runtime, downloads, and backend hardware.

## Filters and modes

| Option | Behavior | Use it to |
| --- | --- | --- |
| `--codebase` | Selects one or more regression matrix identifiers. Source default covers the major OpenMMLab codebases. | Keep a run small: e.g. `--codebase mmdet`. |
| `--backends` | Selects backend names. If omitted, the source runner tries the common backend set. | Prevent unavailable backends from consuming time or producing expected skips. |
| `--models` | Selects model names. Names are normalized to lowercase alphanumeric text before matching. | Use `maskrcnn` for display names like `Mask R-CNN`; use `seresnet` for `SE-ResNet`. |
| `--work-dir` | Stores conversion outputs, per-codebase reports, and merged workbooks. | Use a clean, space-free path outside the skill tree. |
| `--checkpoint-dir` | Caches downloaded PyTorch checkpoints. | Reuse a populated cache to avoid repeated downloads. |
| `--device` | Device string for conversion and backend validation. | TensorRT requires CUDA; ncnn/OpenVINO paths are forced CPU by the runner. ONNX Runtime may be forced CPU if GPU runtime is unavailable. |
| `--performance` / `-p` | Enables backend metric/precision testing after conversion. | Omit it for convert-only smoke runs. |
| `--log-level` | Controls logger verbosity. | Use `DEBUG` for schema/path diagnosis; `INFO` for normal reports. |
| `--repo-root` | Checkout containing deployment configs, regression matrices, and conversion helper entry point. | Run this bundled helper from arbitrary current directories. |

## External downloads and caches

Regression matrices obtain checkpoint URLs from each model's codebase metafile. The runner downloads missing checkpoint files into `--checkpoint-dir` unless the matrix asks for forced redownload. If the checkpoint already exists and forced redownload is false, the runner reuses it.

A "without model downloads where possible" run means:

1. choose a narrow `--codebase`, `--backends`, and `--models` subset;
2. set `--checkpoint-dir` to an existing populated cache;
3. keep `--performance` off when conversion coverage is enough;
4. stop and report if a selected model lacks a cached checkpoint and network access is not allowed.

Downloads are unavoidable for a selected precision run when the PyTorch checkpoint is not already cached, because the runner needs the baseline model artifact for conversion and comparison.

## Report structure

The runner writes a per-codebase report workbook and a merged workbook named for the installed MMDeploy version. A companion text log is used while the run is in progress. The core workbook columns are:

| Column | Meaning |
| --- | --- |
| `Model` | Display name from the regression matrix. |
| `Model Config` | Model config used for conversion/evaluation. |
| `Task` | Codebase task name from the model metafile. |
| `Checkpoint` | Baseline checkpoint path, backend artifact path, or SDK model directory used for the row. |
| `Dataset` | Dataset name from the codebase metafile or matrix metric metadata. |
| `Backend` | `Pytorch`, backend name such as `tensorrt`, or `SDK-<backend>` for SDK validation rows. |
| `Deploy Config` | Deployment config used by the row. |
| `Static or Dynamic` | Derived from the deploy config's dynamic-shape setting. |
| `Precision Type` | Derived from the deploy config name, e.g. `fp32`, `fp16`, or `int8`. |
| `Conversion Result` | Whether conversion completed for backend rows. |
| metric columns | One column for each key in the matrix `metric_info` block. |
| `Test Pass` | Whether the backend metric stayed within tolerance, or whether convert-only mode succeeded. |

A PyTorch baseline row usually has `Conversion Result` and `Test Pass` as `-`; backend rows carry conversion and metric/SDK status.

## Regression matrix schema

Matrix YAML uses four kinds of data:

```yaml
globals:
  codebase_dir: <relative-or-absolute-codebase-directory>
  checkpoint_force_download: false
  images:
    image_anchor: <path-to-sample-image>
  metric_info:
    metric_name:
      eval_name: <evaluator-argument-name>
      metric_key: <key-found-in-test-log-json>
      tolerance: <allowed-delta>
      task_name: <metafile-task>
      dataset: <metafile-dataset>
      # optional: multi_value: 100.0
  sdk:
    sdk_anchor: <sdk-deploy-config>

<backend-name>:
  pipeline_name:
    convert_image:
      input_img: <image-used-during-conversion>
      test_img: <image-used-for-optional-visual-test>
    backend_test: true
    sdk_config: <optional-sdk-deploy-config>
    deploy_config: <deployment-config>
    # optional: metric_tolerance: {metric_name: <override>}
    # optional for int8: calib_dataset_cfg: <calibration-dataset-config>

models:
  - name: <display-name>
    metafile: <codebase-metafile>
    codebase_model_config_dir: <model-config-directory>
    model_configs:
      - <model-config-file>
    pipelines:
      - <pipeline-reference-or-inline-pipeline>
```

Key interpretation rules:

- `globals.metric_info` defines which metric columns appear in reports and how backend metrics are compared against the PyTorch baseline.
- `backend_test: false` with no `sdk_config` makes a pipeline convert-only even in a precision run.
- `sdk_config` adds SDK precision rows only in precision mode; SDK runtime ownership remains with the SDK workflow.
- `metric_tolerance` overrides default tolerance for a specific pipeline when a backend/precision mode has expected numerical drift.
- `calib_dataset_cfg` is relevant to int8 pipelines that need calibration data.

## Native checks to prefer after integration

Use native checks only after the generated skill has been integrated and the environment/backend plan says they are safe. Good validation candidates are:

- backend wrapper dispatch smoke tests for available backend managers and model-file conventions;
- timer utility tests for `TimeCounter` behavior before trusting speed logs;
- ONNX optimizer pass tests only as adjacent optimizer/export evidence when graph rewrites appear to explain validation failures; rewrite-specific ownership stays with the extensibility workflow.

Treat skipped backend-native checks as `SKIP_BACKEND_UNAVAILABLE`, not as pass. Treat missing required backend hardware as a required-backend block unless the user narrows scope or accepts a partial result.
