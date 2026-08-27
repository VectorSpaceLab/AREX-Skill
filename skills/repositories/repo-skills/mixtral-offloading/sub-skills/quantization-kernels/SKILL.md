---
name: quantization-kernels
description: "Work with mixtral-offloading's HQQ quantized layers, packing
  patches, and Triton matmul kernels."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Quantization Kernels

Use this sub-skill when the task is about HQQ quantization metadata, packed
2/3/4-bit weights, `HQQLinearTritonSavable`, or Triton kernel failures in
mixtral-offloading.

## Read this when

- The user mentions `HQQLinearTritonSavable`, `BaseQuantizeConfig`, `W_q`,
  `scale_q`, `zero_q`, or `get_hqq_meta`.
- The task involves `pack_2bit_u8_common`, `pack_3bit_i32_common`,
  `pack_4bit_u8_common`, or HQQ `Quantizer.pack/unpack` monkey patches.
- Triton wrapper calls fail with shape, dtype, contiguity, or CUDA errors.
- The user wants a tiny validation that does not load Mixtral weights.

## Route map

1. Read [references/quantization-api.md](references/quantization-api.md) for
   the HQQ layer wrapper, metadata, packing functions, and state-dict behavior.
2. Read [references/triton-kernels.md](references/triton-kernels.md) for the
   matmul wrapper contracts and tiny CUDA smoke expectations.
3. Run [scripts/check_packing_roundtrip.py](scripts/check_packing_roundtrip.py)
   to validate the bundled 2/3/4-bit pack/unpack logic without CUDA.
4. Run [scripts/check_triton_kernel_smoke.py](scripts/check_triton_kernel_smoke.py)
   to verify a CUDA/Triton environment and, when a user checkout is supplied,
   exercise the repo's Triton wrapper on a tiny tensor.
5. Read [references/troubleshooting.md](references/troubleshooting.md) for
   HQQ optional backend warnings, group-size assertions, unsupported `nbits`,
   and kernel launch failures.

## What this sub-skill owns

- HQQ quantized linear layer behavior and metadata expectations.
- Packed tensor helper behavior for 2-bit, 3-bit, and 4-bit quantized weights.
- Triton matmul wrapper input/output contracts.
- Safe smoke checks for quantization and kernel environments.

## What to route elsewhere

- Use [../inference-workflow/SKILL.md](../inference-workflow/SKILL.md) for full
  model loading, `OffloadConfig`, tokenizer, and generation workflow.
- Use [../expert-cache/SKILL.md](../expert-cache/SKILL.md) for expert storage,
  LRU cache, and SparseMoeWrapper routing.

## Safety notes

Tiny packing checks are CPU-safe. Triton checks require CUDA and may spend a
short time compiling a kernel. They must not download model weights, run the
interactive demo, or modify a user's environment.
