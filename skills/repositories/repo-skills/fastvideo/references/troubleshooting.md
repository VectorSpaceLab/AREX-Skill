# Cross-cutting troubleshooting

Use the nearest focused route for the workflow, then apply these package-wide
rules:

1. Establish the exact FastVideo/package revision and isolated Python version.
2. Separate package import, backend readiness, model-weight access, and workload
   correctness; passing one does not prove the others.
3. Preserve the smallest reproducible config, prompt/data sample, seed, model
   revision, backend, and error output.
4. Do not retry credentialed, network-heavy, destructive, multi-GPU, or long
   training operations blindly.

## Common gates

- Check nested config shape and exact field path after any `unknown field` or
  type error.
- Check `torch.version.cuda`, device availability/capability, and extension ABI
  after CUDA errors.
- Check optional module/extra requirements after an import error; use SDPA or a
  documented fallback only when the selected model permits it.
- Check output path, codec, ffmpeg/PyAV, and workload-specific extension for
  missing media.
- For server failures, check `/health`, port, model startup, request schema,
  and operator defaults separately.
- For training/data failures, validate manifests/schema before encoding or
  starting distributed workers.
- For quality/performance regressions, compare fixed inputs and exclude model
  load, compilation warmup, and unrelated I/O from the claimed measurement.

Stop and report rather than weakening a required backend, silently skipping
missing model/data files, embedding credentials, or treating a synthetic/mock
check as proof of a real model result.
