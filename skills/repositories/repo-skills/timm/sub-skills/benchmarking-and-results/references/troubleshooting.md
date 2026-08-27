# Benchmarking Troubleshooting

## Timing Looks Inconsistent

- CPU, CUDA GPU, MPS, XPU, and other device timings are not directly comparable. Treat each backend as a separate benchmark population.
- GPU timing needs synchronization. The benchmark uses CUDA synchronization for CUDA devices, but CPU timing and non-CUDA accelerators may have different behavior.
- Thermal throttling, background processes, power limits, and dynamic clocks can change repeated runs.
- Use more warmup and timed iterations for publishable numbers; use low iterations only for smoke tests.

## Out of Memory

Symptoms include CUDA OOM, allocator errors, or a run that retries with smaller batch sizes.

Actions:

1. Reduce `--batch-size` aggressively, especially for train or `both` mode.
2. Switch from `--bench both` to `--bench inference` when train-step timing is not required.
3. Avoid large `--img-size` or `--input-size` overrides until the default size works.
4. Consider AMP on supported GPUs, but verify dtype support before comparing with fp32.
5. Leave benchmark retry enabled unless the exact requested batch size must fail when unsupported.

## Warmup and First-Run Effects

- Low `--num-warm-iter` is useful for debug but may under-warm kernels, caches, and autotuning.
- `torch.compile` can add large first-run compilation overhead and may change memory use. Do not include compile setup time in steady-state claims unless the user explicitly cares about cold-start latency.
- Compare compiled and eager rows separately; compiled results may depend on backend, mode, PyTorch version, and model graph support.

## Precision, AMP, and Channels-Last Issues

- `--amp` overrides `--precision` and maps to AMP fp16 or AMP bf16 based on `--amp-dtype`.
- Pure `float16` and `bfloat16` can behave differently from AMP autocast. Do not collapse them into one category.
- Channels-last (`--channels-last`) changes memory layout and is commonly represented as NHWC in result filenames; compare it only with matching layout rows.
- Some CPUs or GPUs have weak or missing support for a requested dtype. Fall back to `float32` for a sanity check.

## Optional Profilers Missing

Profile and FLOP/activation fields depend on optional packages:

- `profile_deepspeed` requires DeepSpeed's FLOPs profiler.
- `profile_fvcore` requires `fvcore`.
- If neither optional profiler is installed, profile mode cannot produce profiler results.
- In inference mode, `infer_gmacs` and `infer_macts` may be absent if profiler import or execution fails.

When profiler packages disagree, report the tool used and treat counts as estimates, not exact hardware measurements.

## CSV Interpretation Problems

- `step_time` fields are milliseconds per batch step, not milliseconds per image.
- `samples_per_sec` depends on batch size; higher batch size can improve throughput while hurting latency.
- Train-step benchmarks use synthetic labels and a simple optimizer step. They are not full data-loader, augmentation, distributed, or recipe benchmarks.
- Benchmark CSV filenames encode precision, layout, PyTorch/CUDA versions, device, and sometimes compile state. Keep those tokens in comparisons.
- Validation CSVs report dataset accuracy, not benchmark speed.

## Stale Metadata or Missing Models

- A model can exist in current `timm` while not yet appearing in `model_metadata-in1k.csv`.
- `model_metadata-in1k.csv` is a compact pretraining lookup, not a full provenance record.
- If metadata appears stale, verify live availability with `timm.list_models(pretrained=True)` and inspect the model's pretrained config before making strong claims.

## All-Model Benchmark Requests

All-pretrained or all-model benchmark requests can run hundreds or thousands of model configurations. Before launching:

1. Narrow by model family, wildcard, or reviewed model-list file.
2. Set a maximum model count and ask for explicit approval when the request remains broad.
3. Use debug iteration counts first.
4. Save to a results file and resume manually if interrupted.
5. Avoid `bulk_runner.py` unless the user accepts many subprocess launches and possible long runtime.
