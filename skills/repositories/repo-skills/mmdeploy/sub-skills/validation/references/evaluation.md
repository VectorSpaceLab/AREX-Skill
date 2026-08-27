# Backend Evaluation with `test.py`

## Purpose

Read this when a user wants to validate an already exported backend model against an OpenMMLab model config, obtain evaluator metrics, save visual outputs, or collect speed-test logs during evaluation. Use the bundled [test helper](../scripts/test.py); it is adapted from MMDeploy's validation CLI.

## What this helper validates

`test.py` loads a deployment config and a model config, builds the corresponding task processor, constructs the test dataset/dataloader from the model config, builds a backend model from `--model`, and runs the codebase test runner. If `--speed-test` is enabled, it wraps the runner in MMDeploy's `TimeCounter` instrumentation.

Metric names and evaluator behavior come from the codebase model config and dataset evaluator. In the inspected implementation, the helper itself does **not** expose a separate `--metrics`, `--metric-options`, `--out`, or `--format-only` switch; use the model config/dataset settings or codebase-native evaluation hooks when a user needs custom evaluator routing. Treat the bundled script's `--help` output as the authoritative flag list.

## Command shape

```bash
python path/to/validation/scripts/test.py \
  <deploy-cfg> \
  <model-cfg> \
  --model <backend-model-file> [<extra-backend-file> ...] \
  --device <cpu-or-backend-device> \
  --work-dir <evaluation-work-dir> \
  [--cfg-options key=value ...] \
  [--show] [--show-dir <painted-output-dir>] \
  [--log2file <log-file>] \
  [--batch-size <n>] \
  [--speed-test --warmup <n> --log-interval <n>]
```

Use absolute paths or run from a checkout where config/model paths resolve. Keep output directories outside the runtime skill tree.

## Backend model-file rules

`--model` accepts one or more files. Pass the artifact set that matches the deployment backend, not just the first file in the output directory.

| Backend family | Typical files to pass | Notes |
| --- | --- | --- |
| ONNX Runtime | `end2end.onnx` | CPU or GPU depends on installed ONNXRuntime package and `--device`. |
| TensorRT | `end2end.engine` | Requires CUDA/TensorRT runtime on the target host. Use a TensorRT deploy config whose dynamic/static shape range matches the exported engine. |
| OpenVINO | `end2end.xml` plus the companion binary in the same directory | The wrapper generally receives the XML path; keep the BIN file adjacent. |
| ncnn | `end2end.param end2end.bin` | Order matters: pass both model structure and weights. |
| PPLNN | `end2end.onnx end2end.json` | Pass both the ONNX file and generated algorithm JSON. |
| TorchScript | `end2end.pt` | CPU TorchScript is the lightweight backend most likely to be available in a minimal environment. |
| SDK packaged model | SDK model directory or backend artifacts required by its deploy config | SDK runtime and graph analysis are owned by the SDK workflow; use this route only for validation output. |

## Important flags

| Flag | Use it for | Gotchas |
| --- | --- | --- |
| `deploy_cfg` | Deployment/backend config. | Must match the backend model files. A mismatch can produce wrapper import errors or silently wrong preprocessing. |
| `model_cfg` | OpenMMLab model config that defines task, dataset, preprocessing, and evaluator. | Missing codebase package, dataset files, or evaluator config will fail before meaningful backend validation. |
| `--model` | Backend artifact files. | Multi-file backends need every required file. |
| `--device` | Device string such as `cpu`, `cuda`, or `cuda:0`. | Some backends force a device class; TensorRT needs CUDA, while OpenVINO/ncnn paths are usually CPU-side. |
| `--work-dir` | Evaluation work directory for runner artifacts. | Keep it separate from the skill tree and use a path without accidental reuse of stale results. |
| `--cfg-options` | Override model config values with `key=value` pairs. | Quote list/tuple values exactly as MMEngine `DictAction` expects, e.g. `key="[a,b]"`; no whitespace inside list strings. |
| `--show` | Display painted results interactively. | Avoid on headless machines unless a display backend is available. |
| `--show-dir` | Save painted results. | Safe alternative to `--show` for remote/headless validation. |
| `--interval`, `--wait-time` | Control visualization cadence and display time. | Only relevant when visualization is enabled. |
| `--log2file` | Persist evaluation and speed-test logs. | Useful for regression comparisons and audit trails. |
| `--batch-size` | Override test dataloader batch size. | Many exported backends or static-shape configs only support batch size 1; see troubleshooting before using larger batches. |
| `--speed-test` | Time inference while running the evaluation loop. | Enables TimeCounter logs but still runs the evaluator path. Use `profiler.py` for latency-only measurements. |
| `--warmup`, `--log-interval` | Control speed-test warmup and log cadence. | These only matter with `--speed-test`. |

## Interpreting results

- **Metrics:** successful runner output means the backend model executed through the codebase evaluator. Compare backend metric values with the PyTorch baseline, benchmark documentation, or regression report tolerance for the same model/config/dataset.
- **Visual outputs:** `--show-dir` output is qualitative evidence. It does not replace metric comparison, but it helps diagnose wrong preprocessing, label mapping, or postprocessing.
- **Speed-test logs:** TimeCounter prints per-count latency and FPS during evaluation. Because the evaluator still runs, timing can include dataloader/evaluator overhead depending on the codebase. Use [profiling](profiling.md) when the user wants a dedicated latency benchmark.
- **Batch-size changes:** increasing `--batch-size` changes the dataloader and TimeCounter normalization. Verify that the deploy config, backend engine, and model support that batch size before interpreting metrics or speed.
