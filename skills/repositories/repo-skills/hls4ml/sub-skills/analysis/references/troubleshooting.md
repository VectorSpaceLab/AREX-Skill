# Troubleshooting analysis and tuning workflows

Use this file to classify failures before changing more knobs. Preserve the evidence level: source-documented, import-checked, CPU parity, C simulation, co-simulation, or synthesis/report.

## Profiling failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `numerical()` cannot import plotting/profiling modules | Missing `hls4ml[profiling]` dependencies such as plotting/dataframe packages | Install the profiling extra in the active runtime. This extra was available during drafting, but future environments may differ. |
| Activation profiling with `hls_model` raises that no trace exists | No layer has `Trace=True`, so `hls_model.trace(X)` returns an empty trace dictionary | Regenerate/convert with selected `config["LayerName"][name]["Trace"] = True`, then rerun `compile()`/`trace()`. |
| Keras/frontend layer names do not match HLS trace keys | hls4ml optimizer passes fused, removed, or split layers | Compare against post-optimization HLS layer names. BatchNormalization fusion is a common source of name differences. |
| Profiling looks safe but accuracy is poor | Ranges cover values, but fractional precision or lookup-table types are still too coarse | Run `compare()` to locate the divergent layer, then tune precision for that layer or table type. |
| PyTorch activation profiling misses layers | The simple activation helper follows sequential child modules | Use HLS layer tracing for the converted graph, and route frontend data-layout questions to `frontends`. |

## Automatic precision failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Model-level `Precision: auto` fails or is ignored | Automatic precision is only layer-level | Use `granularity="name"` and set `config["LayerName"][layer]["Precision"]` or a named precision variable to `"auto"`. Keep `Model.Precision.default` explicit. |
| `compile()` fails with unspecified precision | Some required type remained `auto`/unspecified after inference | Pass `backend` when generating the config, inspect the layer-specific `Precision` dictionary, and set unsupported variables manually. |
| Auto inference produces very wide types | The pass is conservative and uses bit widths rather than observed values | Add `max_precision`, then profile/compare; manually tighten non-critical weights/results if parity holds. |
| Manual precision seems ignored | `bit_exact` may be enabled and it ignores user precision | Disable `bit_exact` for manual tuning, or accept that the model-wise pass owns all precision. |

## Bit-exact failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Conversion crashes under `bit_exact=True` | Unsupported operator or unsupported layer chain | Do not claim bit exactness. Switch to layer-level `auto`/manual precision or simplify/quantize the model. |
| Bit widths explode | The model is not fully quantized, or quantizers are missing after inputs | Add explicit fixed-point quantizers between input and arithmetic layers, or disable `bit_exact`. |
| QKeras/HGQ/PQuant model only matches approximately | Quantizer choices are not fixed-point-compatible, or frontend/source support is partial | State the tolerance and evidence. Exact equality is only expected for supported fixed-point-compatible quantized flows. |
| QONNX bit-exact expectations fail | QONNX model-wise support is not guaranteed by the current source documentation | Use `granularity="name"` automatic precision and source-verified QONNX conversion paths instead of claiming `bit_exact`. |
| Softmax is the first divergent layer | Softmax table and accumulator types are special, and bit-exact softmax requires frontend support | Inspect `exp_table`, `inv_table`, and accumulator precision; compare with tolerance unless the frontend explicitly supports bit-exact softmax. |

## Resource tuning failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Changing `ReuseFactor` changes numerical parity | Different generated arithmetic exposed marginal precision | Re-profile the affected layer and widen accumulator/result precision before changing more resource knobs. |
| Backend rejects a `Strategy` value | Strategy support is backend-specific | Route to `backends`; do not assume `Latency`, `Resource`, `Unrolled`, or distributed arithmetic are all available for every backend. |
| `BramFactor` has no effect | It is model-level only, threshold is too high, or the backend does not support external weights | Set `config["Model"]["BramFactor"]` deliberately and verify generated weight storage/backend output. oneAPI does not support external weights. |
| User asks for BRAM/LUT/DSP savings from config edits only | No synthesis/report evidence exists | State that only a tuning hypothesis exists. Route synthesis/report execution to `backends`. |

## FIFO depth optimization failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Runtime error says `IOType` must be `io_stream` | FIFO optimization requires streams between layers | Regenerate as `io_stream` or do not use FIFO-depth optimization. |
| Invalid `profiling_fifo_depth` error | Value is negative, non-integer, or otherwise invalid | Use a non-negative integer such as `100_000`. |
| Optimizer says no BRAM FIFOs were found | Initial FIFO depth did not force profiled FIFOs into BRAM, or design has no eligible FIFOs | Increase `profiling_fifo_depth` only within an approved backend run, then re-run co-simulation. |
| User wants to report optimized FIFO depths | Missing co-simulation/deadlock evidence | Require reduced depth data plus a passing co-simulation report. Config edits alone are not FIFO evidence. |

## Model optimization failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `from hls4ml.optimization import optimize_keras_model_for_hls4ml` fails | The top-level optimization package does not re-export the wrapper in this checkout | Import from `hls4ml.optimization.dsp_aware_pruning` instead. |
| Optimization loop fails on missing `ortools` or tuner package | The optimization optional extra was not installed; pinned `ortools==9.4.1874` did not resolve for Python 3.11 during drafting | Prepare a Python 3.10-compatible or dependency-adjusted environment before claiming runtime verification. |
| Scheduler type error | A string was passed instead of an `OptimizationScheduler` instance | Instantiate a scheduler class such as `PolynomialScheduler(...)`. |
| Optimization changes model metrics but no HLS report exists | The API optimizes Keras-side structure/weights; it does not synthesize the HLS project | Regenerate the hls4ml model and route backend build/report evidence to `backends`. |
