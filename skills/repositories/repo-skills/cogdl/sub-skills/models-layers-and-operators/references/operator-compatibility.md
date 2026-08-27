# Operator Compatibility

## Purpose

Read this when sparse/message operators, optional CUDA kernels, or third-party
graph-library examples are the part of CogDL that matters to the task.

## What is verified in the installed package

The installed checkout exposes CPU-testable operator helpers in
`cogdl.operators` and accompanying source kernels under `cogdl/operators/`.
The repository tests exercise these helpers on toy graphs without requiring
datasets or training.

Representative operator families include:

- tensor-message helpers such as `s_add_t`, `s_sub_t`, `s_mul_t`, `s_div_t`,
  and `s_dot_t`
- edge-aggregation helpers such as `s_add_e_sum`, `s_sub_e_mean`, and
  related sum/mean variants
- sparse matrix multiplication and scatter-style kernels used by GNN layers

## Compatibility notes

| Surface | CPU-safe? | Optional backend notes |
| --- | --- | --- |
| Pure tensor helpers in tests | Yes | Useful for regression checks and toy smoke tests |
| Sparse/GNN kernels under `cogdl/operators/` | Usually yes for the CPU path | CUDA kernels may require a compatible PyTorch/CUDA build and, if you rebuild from source, `nvcc`/toolkit support |
| PyG examples under `examples/pyg/` | No, not as a core dependency | Require PyG and are reference-only for this skill |
| Jittor example under `examples/jittor/gcn.py` | No, not as a core dependency | Requires Jittor and is reference-only for this skill |

## Decision rules

- Use the CPU path first when the user only needs model/layer guidance.
- Treat CUDA as an acceleration surface, not a requirement, unless the user
  explicitly asks for GPU/operator behavior.
- If a task depends on PyG, Jittor, DGL, or another external graph stack,
  mention the extra dependency explicitly instead of pretending the base CogDL
  install covers it.
- Keep the bundled smoke script focused on toy graphs so it can run without
  downloads or benchmark data.
