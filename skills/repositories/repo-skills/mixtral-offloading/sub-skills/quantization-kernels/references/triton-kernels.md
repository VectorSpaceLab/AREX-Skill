# Triton kernel reference

The repository exposes Python wrappers around Triton JIT kernels for quantized
matrix multiplication with transposed packed weights.

## Wrapper signatures

- `triton_matmul4_transpose(groupsize, a, qweight, scales, zeros, bias=None)`
- `triton_matmul2_transpose(groupsize, a, qweight, scales, zeros, bias=None)`
- `triton_matmul3_transpose(groupsize, a, qweight, scales, zeros, N, bias=None)`

Common contract:

- `a` is a contiguous CUDA float16 tensor with trailing dimension `K`.
- `qweight` is a CUDA integer tensor whose second dimension is `K`.
- `scales` and `zeros` have matching second dimension `K`.
- Output is allocated on CUDA as float16 and reshaped to `a.shape[:-1] + (N,)`.
- Optional `bias` is added after the kernel result.

`N` is inferred as `qweight.shape[0] * 2` for 4-bit and
`qweight.shape[0] * 4` for 2-bit. The 3-bit wrapper requires an explicit `N`
and asserts that `qweight.shape[0] * 10 - N` is between 0 and 9.

## Shape and grouping cautions

The Triton kernels use tuned block sizes with `BLOCK_SIZE_N=32` and
`BLOCK_SIZE_K=32` in the retained configs. Tiny smoke checks should therefore
use `K=32` and `N=32` to avoid confusing kernel-shape issues with environment
failures.

For grouped scales/zeros, `groupsize` controls `G = N // groupsize`. A simple
smoke can set `groupsize=1` and use `scales`/`zeros` with shape `(N, K)`. Real
Mixtral metadata may use different grouping; follow the stored HQQ metadata.

## Tiny CUDA smoke strategy

The bundled `check_triton_kernel_smoke.py` does two things:

1. It verifies that PyTorch can see CUDA and that Triton imports.
2. If `--repo-root` points at a user checkout, it imports `src.triton_kernels`
   and calls `triton_matmul4_transpose` on a tiny zero-packed fixture.

This smoke is not a substitute for full Mixtral generation. It only proves that
CUDA/Triton can compile and launch a representative small kernel.

## When not to run it

- No CUDA device is visible and the user did not pass `--skip-if-no-cuda`.
- The environment is shared and changing PyTorch/Triton versions would be
  unsafe.
- The task is only about reading API guidance and no backend verification is
  required.
