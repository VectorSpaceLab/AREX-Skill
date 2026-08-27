---
name: structured-operators
description: "Route pure-Python NeuroMANCER SLiM maps, structured recurrent
  layers, differentiable projection and iterative solvers, and dimension or
  parameterization failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Structured operators

Use this route when a task needs a NeuroMANCER structured linear map, a
structured SLiM RNN, `GradientProjection`/`IterativeSolver`, a safe LOP
building block, or a small operator smoke test. Start with the tensor/key
contract and dimensions, then select a named map from
`neuromancer.slim.maps`; do not guess a class or constructor keyword.

## Route

1. Decide the map shape. A map consumes `(..., insize)` and returns
   `(..., outsize)`; square parametrizations require `insize == outsize`, and
   `trivial_nullspace` additionally requires `outsize >= insize` and
   `bias=False`.
2. Select a registry key and instantiate it with only supported kwargs. Prefer
   the pure-Python map set in the bundled smoke script. Treat `butterfly`, its
   complex mode, and factor extension as an optional route, not as a CPU
   prerequisite.
3. Check `effective_W()`, `reg_error()`, output shape, and one backward pass.
   For an orthogonal map in this release, use `bias=True` because its forward
   implementation adds `self.bias` unconditionally.
4. For a sequence, use `slim.RNNCell` or `slim.RNN`: sequence tensors are
   `(seq_len, batch, input_size)`, hidden maps are square on `hidden_size`, and
   the input map may be rectangular.
5. For a solver, keep symbolic constraint construction in the
   `symbolic-problems` route. Feed the solver a dictionary containing every
   constraint input key, preserve `requires_grad=True` for projected variables,
   and match `input_keys` to `output_keys`.
6. When embedding a map in `modules.blocks.MLP`, remember that `linear_map` is
   applied to every layer. A square map therefore requires every adjacent MLP
   width to be equal.

See [the API and shape contracts](references/api-reference.md),
[bounded workflows](references/workflows.md), and
[the failure matrix](references/troubleshooting.md). Run
`scripts/maps_smoke.py --run` for a deterministic CPU-only map and autograd
check; `--help` documents the safe invocation.

## Route out

- Ordinary MLPs, neural dynamics, and model architecture choices belong to
  `dynamics-modeling`.
- Variable/expression comparator syntax and symbolic problem graphs belong to
  `symbolic-problems`; this route only consumes their constraint objects.
- Dataset, benchmark, external-data, and download workflows are not part of
  this operator smoke.
- Native C++/CUDA butterfly factor multiplication and complex/butterfly
  benchmarking are explicitly optional and excluded from the minimum route.
