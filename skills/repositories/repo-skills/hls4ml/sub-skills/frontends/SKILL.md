---
name: frontends
description: "Convert supported Keras, PyTorch, ONNX, QONNX, quantized, spiking,
  example, serialization, and plotting inputs into hls4ml ModelGraph projects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Frontends

Use this sub-skill when the task starts with a frontend model or serialized frontend artifact and ends with an hls4ml `ModelGraph`, saved model, or conversion-ready configuration.

## Handles

- Keras v2 / TensorFlow Keras
- Keras v3
- QKeras / QKeras-v3
- HGQ / HGQ2
- Distributed-arithmetic fallback in Keras v3
- PyTorch, Brevitas export-to-QONNX flows, and PQuantML
- SNN readout markers
- ONNX / QONNX preprocessing
- Example-model helpers, serialization, plotting, and legacy config/convert routes

## Use this sub-skill for

- generating an `hls_config`
- converting a model into an hls4ml project
- inspecting the active frontend layer registry
- saving or reloading a converted model
- doing a safe conversion smoke check

## Do not use this sub-skill for

- vendor synthesis, build, or report generation -> backends
- precision or resource tuning after conversion -> analysis
- custom layer or plugin authoring -> extensions

## Operating flow

1. Identify the frontend and required optional packages.
2. Build or load the native model.
3. Create a frontend-specific config with the matching `config_from_*` helper.
4. Convert with the matching `convert_from_*` helper or a compatible YAML route.
5. Compile and run a small prediction smoke when possible.
6. If unsupported operators, conflicting quantization stacks, or vendor tools are required, route to the sibling skill instead of guessing.

## Reference map

- `references/api-reference.md`
- `references/keras-and-quantization.md`
- `references/pytorch-and-snn.md`
- `references/onnx-qonnx.md`
- `references/examples-serialization-cli.md`
- `references/troubleshooting.md`

## Safe helpers

- `scripts/smoke_convert_keras.py`
- `scripts/smoke_convert_pytorch.py`
- `scripts/inspect_supported_layers.py`

## Verified snapshot

This skill was authored against hls4ml `0.1.0.dev1+gb90fb0673` in a CPU-only inspection environment. Keras v2/TensorFlow 2.14, PyTorch, QKeras, HGQ, ONNX, qonnx, da4ml, and snntorch were available. Keras v3, HGQ2, QKeras-v3, PQuantML, and sparsepixels remain source-documented but were not live-verified in that environment.
