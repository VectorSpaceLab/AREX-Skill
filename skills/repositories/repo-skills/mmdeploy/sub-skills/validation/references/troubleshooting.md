# Validation Troubleshooting

## Purpose

Use this before classifying a validation, profiling, regression, or supported-table issue as a model defect. Each row lists symptoms, likely causes, recovery steps, and stop conditions owned by this validation sub-skill.

## Install/import and optional dependency failures

| Symptom | Likely cause | Recovery | Stop when |
| --- | --- | --- | --- |
| `ModuleNotFoundError: mmdeploy`, `mmengine`, `mmcv`, `torch`, or `onnx` | MMDeploy or core OpenMMLab runtime is not importable in the active Python environment. | Activate/install a package environment that imports MMDeploy and the relevant OpenMMLab codebase; rerun a one-line import check before validation. | The user forbids environment changes and no importable environment exists. |
| `ModuleNotFoundError: pandas`, `openpyxl`, `yaml`, `prettytable`, or `tqdm` | Helper-only dependency missing for reports, YAML parsing, or TimeCounter tables. | Install the specific missing package needed by the chosen helper; do not install broad backend stacks for a pure report/table task. | Package installation is outside budget or policy. |
| Backend manager says a backend package is unavailable | Optional backend runtime is absent or custom ops were not built. | If backend installation is in scope, route to the backend workflow. If not, record an unavailable-backend skip/block and narrow validation to installed backends. | The task requires that backend and there is no verified runtime/hardware. |
| TorchScript available but custom ops unavailable | Minimal CPU environment can import TorchScript but did not build MMDeploy custom ops. | Use TorchScript only for workflows that do not require custom ops, or rebuild/install the required custom ops through the backend workflow. | Custom op execution is required for the user's model. |

## Config, data, and artifact failures

| Symptom | Likely cause | Recovery | Stop when |
| --- | --- | --- | --- |
| `FileNotFoundError` for a deploy config, model config, matrix YAML, metafile, or backend model file | Path was resolved from the wrong current directory, a codebase checkout is missing, or the backend artifact set is incomplete. | Use absolute paths or the helper's checkout/root option; verify the backend model-file table in [evaluation](evaluation.md); ensure multi-file backends include every companion file. | The selected codebase repository, config, or artifact does not exist. |
| Profiler reports `No image files found` | `image_dir` is empty, image suffixes are unsupported, or path points at the wrong directory. | Pass a directory containing images and adjust `--img-ext` if needed. | No representative images are available and synthetic inputs would not answer the user's task. |
| `Input_shape should not be None` during profiling | The deploy config does not declare a static input shape and no `--shape HxW` was supplied. | Supply `--shape` or choose a static deployment config appropriate for the backend. | The backend engine was built for an unknown or incompatible shape range. |
| Evaluation/profiling fails only when `--batch-size` is greater than 1 | Exported engine, static shape config, dynamic shape range, or codebase dataloader does not support that batch size. | Re-run with `--batch-size 1`; if a larger batch is required, reconvert with a compatible shape range and validate again. | The user requires the larger batch and conversion/backend setup is out of scope. |
| Visualization fails on a remote/headless host | `--show` needs a display backend. | Use `--show-dir` instead and inspect saved images. | The task requires interactive display and no display server is available. |

## CLI/API misuse

| Symptom | Likely cause | Recovery | Stop when |
| --- | --- | --- | --- |
| User asks for accuracy metrics but only profiler output exists | `profiler.py` is latency-only. | Run `test.py` for metric-aware validation or `regression_test.py --performance` for matrix metrics. | Required datasets/evaluators are missing and cannot be obtained. |
| User asks for latency with custom iterations but uses `test.py --speed-test` | `test.py` times within evaluation and exposes warmup/log interval, not measured iteration count. | Use `profiler.py --warmup --num-iter --batch-size` for latency-only timing. | The model cannot be loaded by profiler because conversion/backend setup is missing. |
| `--cfg-options` parsing fails | MMEngine `DictAction` requires exact `key=value` syntax; list/tuple values need quoting and no spaces. | Quote values like `model.test_cfg="[a,b]"` or split overrides into separate key-value pairs. | The desired override changes unsupported model or backend assumptions. |
| Backend file suffix does not match deploy config | Passing an ONNX file to a TensorRT config, missing ncnn pair, or stale work directory artifacts. | Match file rules in [evaluation](evaluation.md), clear stale output directories, and validate one model/backend at a time. | The model must be reconverted and conversion is out of this sub-skill's scope. |

## Regression-specific failures

| Symptom | Likely cause | Recovery | Stop when |
| --- | --- | --- | --- |
| Full regression run begins downloading many checkpoints | Defaults or broad filters selected too many models/codebases. | Interrupt if needed; rerun with explicit `--codebase`, `--backends`, `--models`, and an existing `--checkpoint-dir`. | User did not authorize network, long runtime, or storage use. |
| Checkpoint download fails | Network, URL, or cache permission problem; selected model checkpoint is not already present. | Populate the checkpoint cache manually, retry with network allowed, or choose a cached subset. | Network is unavailable and the selected checkpoint is not cached. |
| `No empty space included in work_dir/checkpoint_dir` | Runner asserts path strings must not contain spaces. | Move `--work-dir` and `--checkpoint-dir` to space-free paths. | Policy requires a path with spaces and the runner cannot be patched safely. |
| Backend row is absent from report | Backend was not selected, not present in the matrix pipelines, or not in the runner's backend-file map. | Check `--backends`, the matrix pipelines, and the supported backend names in [regression](regression.md). | The matrix does not define that backend and adding it would require conversion-scope work. |
| `Conversion Result` is `False` | Conversion helper failed for the pipeline. | Inspect the pipeline's conversion log, confirm deploy/model config pair, sample image, backend runtime, and calibration config for int8. | Fix requires backend install/build or conversion redesign outside validation. |
| `Test Pass` is `False` but conversion succeeded | Backend metric differs from PyTorch baseline beyond tolerance, evaluator key mismatch, wrong dataset, precision drift, or postprocessing mismatch. | Check the metric column, `metric_key`, `tolerance`, `metric_tolerance`, dataset/task names, and rerun a single `test.py` validation. | Large mismatch remains on a verified backend/config/data path. |
| SDK row fails while backend row passes | SDK packaging/runtime differs from direct backend execution. | Route SDK runtime/package inspection to the SDK workflow after recording validation symptoms. | The user asks to debug SDK graph internals rather than validation output. |

## Backend skip versus fail

- **Skip** means the selected native check deliberately did not run because the backend package, plugin, hardware, or dependency variant is unavailable. Record the skip reason; do not report it as pass.
- **Fail** means the backend/runtime was available and the command returned an error or mismatched output. Diagnose with the relevant reference and logs.
- **Blocked required backend** means the user's task explicitly requires a backend whose runtime/hardware is unavailable. Do not substitute CPU evidence for TensorRT, RKNN, Ascend, SNPE, or other accelerator-specific behavior.
- **Convert-only pass** means conversion completed but metrics were not tested. It is not equivalent to precision validation.

## Expensive and network-bound runs

Regression matrices and benchmark-style profiling can consume large storage, download checkpoints, or require accelerator hardware. Before starting them, confirm:

1. codebase/backend/model subset;
2. whether checkpoint downloads are allowed;
3. where checkpoints and work outputs should be stored;
4. whether backend hardware/runtime is actually available;
5. whether metric validation or convert-only coverage is sufficient.

If any item is unresolved and the run would be expensive or network-bound, stop and ask rather than guessing.
