# Deployment backend preflight

Use this reference after choosing the model artifact family. It lists the checks
needed before claiming a PINTO_model_zoo artifact is deployable on a backend.

## Cross-backend preflight

For every backend:

1. Confirm the selected artifact exists locally or route acquisition to
   `model-acquisition`.
2. Check the selected model's license before redistribution or device shipment.
3. Record input shape, layout, dtype, color order, normalization, and output
   interpretation.
4. Separate three claims: **conversion succeeded**, **runtime loaded**, and
   **target hardware executed**. Do not merge them.
5. Route inference smoke tests, camera/display adaptation, or benchmarking to
   `inference-demos`.

## Raspberry Pi / TFLite CPU

Use for `.tflite` artifacts on Raspberry Pi or similar ARM Linux boards.

Preflight:

- artifact is a TFLite model matching the task and precision target;
- Python runtime has either TensorFlow Lite runtime or TensorFlow installed, not
  every zoo dependency;
- OS and architecture are known. README evidence notes that 64-bit aarch64 was
  much faster than older 32-bit armv7l setups for official TFLite builds;
- optional delegates are explicit: XNNPACK/CPU threads, GPU delegate, or Flex
  delegate only when the model requires them;
- camera, display, audio, or GPIO dependencies are avoided for CI smoke tests or
  explicitly provided by the user.

Safe proof levels:

- desktop interpreter load: validates basic TFLite compatibility only;
- Raspberry Pi runtime load: validates device runtime compatibility;
- Raspberry Pi benchmark/inference: validates target execution for that model,
  thread count, delegate, and input size.

Stop when the user asks for Pi performance but no Pi access is available; offer a
non-hardware interpreter check and mark performance unverified.

## EdgeTPU

Use for Coral/EdgeTPU-oriented deployment.

Preflight:

- source is full-integer TFLite, not merely INT8 weights with float I/O;
- converter used representative data matching deployment preprocessing;
- TFLite ops are compatible with EdgeTPU compiler coverage;
- compiler is installed in the environment where compilation is requested;
- EdgeTPU runtime and device are present for actual inference.

Proof levels:

- full-integer TFLite produced: conversion precondition only;
- EdgeTPU compiler produces an output file: compiler compatibility proof;
- runtime loads with EdgeTPU delegate on device: deployment proof.

Stop on unsupported ops, float inputs/outputs when full-integer is required,
missing compiler, or absent EdgeTPU hardware. Do not claim acceleration from a
CPU-only TFLite run.

## OpenVINO CPU

Use for `OV` catalog artifacts and `.xml`/`.bin` pairs.

Preflight:

- `.xml` and `.bin` share the same stem and reside together;
- selected precision and input shape are the intended ones;
- OpenVINO runtime can read the IR version;
- CPU device is selected unless the user explicitly provides another OpenVINO
  target;
- preprocessing layout and output postprocessing are known.

Proof levels:

- file-pair validation: packaging proof;
- OpenVINO model read/compile on CPU: runtime compatibility proof;
- inference with deterministic input: deployment smoke proof.

If the XML path is passed without the BIN file, or the stems differ, fix the file
selection before diagnosing runtime errors.

## Browser TensorFlow.js / WebGL

Use for `TFJS` catalog artifacts or folders containing `model.json` and weight
shards.

Preflight:

- `model.json` and every referenced shard are available;
- the model is served through a browser-safe local/static server when direct file
  loading is blocked;
- preprocessing is implemented in JavaScript with the same resize, normalization,
  color order, and dtype as the source model;
- WebGL/WebGPU acceleration is tested in the actual browser/device, not inferred
  from converter success.

Proof levels:

- manifest and shard check: packaging proof;
- browser or Node load: runtime proof;
- inference in target browser/backend: deployment proof.

Stop if only a model file is present without shards, if CORS/file loading blocks
browser access, or if the requested WebGL backend is unavailable.

## TF-TRT / NVIDIA GPU

Use only when the target is TensorFlow-TensorRT on NVIDIA GPUs.

Preflight:

- NVIDIA GPU is present and visible to the runtime;
- CUDA, TensorRT, driver, TensorFlow, and Python versions are compatible;
- input shapes and batch sizes are known because TensorRT engines may be built
  for specific profiles;
- memory headroom is available for conversion and first inference;
- fallback behavior is acceptable for unsupported segments.

Proof levels:

- graph conversion completes: conversion proof;
- engine builds for the requested shape on the GPU: backend proof;
- inference matches baseline tolerance: deployment proof.

Stop if no GPU is available or the user asks for portable CPU deployment; route
to TFLite or OpenVINO instead.

## CoreML

Use for `CM` catalog artifacts or `.mlmodel`/CoreML package outputs.

Preflight:

- target device class is known: macOS, iOS, or simulator;
- model input image/tensor metadata preserves shape, scale, bias, and channel
  order;
- outputs and postprocessing are understood;
- non-Apple systems are limited to inspection/conversion unless a compatible
  runtime is provided.

Proof levels:

- CoreML artifact exists: packaging proof;
- model loads on Apple runtime: runtime proof;
- inference on target Apple device: deployment proof.

## When to hand off

After preflight passes, hand runtime execution to `inference-demos` with:

- artifact path(s);
- backend/runtime chosen;
- expected input shape/layout/dtype;
- any delegate flags or hardware requirements;
- proof level requested by the user.
