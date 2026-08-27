# Runtime Deployment Troubleshooting

## Build toolchain missing

Symptoms:

- CMake cannot configure;
- compiler not found;
- libtorch, ONNX Runtime, OpenVINO, or vendor SDK headers/libraries missing.

Recovery:

- Use the runtime chooser to confirm the intended engine and prerequisites.
- Install only the SDK for the selected target.
- Verify compiler architecture matches the target (x86_64, ARM, Android, iOS,
  Raspberry Pi, or vendor accelerator).
- Do not mix libtorch artifacts with ONNX Runtime build flags.

## Wrong artifact for runtime

Symptoms:

- runtime cannot open model;
- missing encoder/ctc/decoder files;
- JIT model passed to ONNX Runtime or ONNX files passed to libtorch;
- tokenizer/units missing at runtime.

Recovery:

1. Route back to [../../model-export/SKILL.md](../../model-export/SKILL.md).
2. Match artifact type to runtime engine.
3. Copy `units.txt`, tokenizer resources, feature config, and optional
   `global_cmvn` alongside model files.
4. Run a tiny local decode before service deployment.

## Streaming or cache mismatch

Symptoms:

- cache-shape errors;
- partial results never finalize;
- streaming latency is wrong;
- non-streaming model used with streaming chunk settings.

Recovery:

- Check export metadata and runtime flags for `chunk_size` and
  `num_decoding_left_chunks`.
- Use non-streaming settings only with non-streaming exports.
- Re-export the model for the desired streaming mode instead of changing only
  runtime flags.

## GPU/TensorRT/Triton service fails

Symptoms:

- CUDA provider missing;
- TensorRT engine build fails;
- server cannot load model repository;
- client cannot connect or times out.

Recovery:

- Verify GPU allocation, driver, CUDA, TensorRT, and Triton versions.
- Confirm model repository paths and config names.
- Start with one small model and one short audio request before benchmarking.
- Check service ports and endpoint URLs; do not run clients against unknown or
  unauthorized services.

## Mobile or edge build fails

Symptoms:

- Android Gradle/Xcode/CocoaPods setup errors;
- architecture mismatch;
- mobile app cannot find model resources.

Recovery:

- Verify target architecture and mobile runtime libraries.
- Bundle model, units, tokenizer, and CMVN resources inside the app package.
- Use a CPU/mobile-compatible artifact before adding quantization or GPU/NPU
  acceleration.

## LM or context graph output is wrong

Symptoms:

- word ids do not match;
- context bias over-inserts hotwords;
- graph decoder crashes or produces empty output.

Recovery:

- Verify graph units and word table were built from the same `units.txt` and
  lexicon resources as the model.
- Start with acoustic-only decoding; then add LM/context graph files.
- Tune LM/context scores on a validation subset instead of changing multiple
  runtime settings at once.

## Vendor accelerator unavailable

Horizon BPU, Kunlun XPU, IPEX, and OpenVINO paths require vendor-specific
packages and sometimes device access. If the current host lacks that stack,
record the deployment path as planned but unverified, and run final validation
on target hardware.
