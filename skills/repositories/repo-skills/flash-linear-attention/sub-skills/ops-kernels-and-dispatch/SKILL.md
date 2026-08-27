---
name: ops-kernels-and-dispatch
description: "Maintain public fla.ops APIs, Triton operator kernels, dispatch
  backends, and correctness gates for Flash Linear Attention."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ops-kernels-and-dispatch

Use this sub-skill when the task touches Flash Linear Attention's public `fla.ops` entry points, Triton/Gluon/TileLang/Ascend operator kernels, backend dispatch registration or verifiers, operator correctness tests, or operator maintenance audits.

## Route here for

- Inspecting or changing public operator APIs such as `chunk_gla`, `chunk_linear_attn`, `chunk_kda`, `fused_recurrent_*`, `fused_chunk_*`, and `parallel_*`.
- Adding, removing, or modifying a `@dispatch('<operation>')` decorator, backend registry, backend verifier, backend env gate, or fallback path.
- Maintaining Triton kernel wrappers, autograd `Function` surfaces, `input_guard` / autocast behavior, variable-length (`cu_seqlens`) contracts, or initial/final state layouts.
- Writing or reviewing correctness coverage for forward outputs, backward gradients, dispatch routing, verifier rejection, and NaN-poisoned allocations.
- Auditing every callsite after a shared signature, state layout, kernel launch, save-for-backward tuple, or return tuple changes.

## Do not use this sub-skill for

- KDA-specific context-parallel design, inter-card protocol, or deep KDA algorithm changes; route to the KDA/context-parallel sub-skill.
- Benchmark loops, profiler work, speedup claims, or benchmark registry maintenance; route to the benchmarking/optimization sub-skill after the correctness gate is green.
- Installation-only, backend wheel selection, or environment smoke checks unless the install issue blocks an operator import; route setup questions to the setup/backends sub-skill.
- Layer/model APIs, checkpoint compatibility, or training recipes unless a layer/model callsite must be audited after an operator API change.

## Fast workflow

1. Identify the public entry point and mode. Use `references/api-and-dispatch.md` for the root export list, signature facts, shape contracts, and dispatch model. Use the bundled script when an installed package is available:

   ```bash
   python scripts/inspect_fla_ops.py --filter kda
   python scripts/inspect_fla_ops.py --signature chunk_gla --signature chunk_linear_attn --signature chunk_kda
   ```

2. Preserve the public contract before optimizing internals: q/k/v/g/beta shapes, `cu_seqlens` flattening, initial/final state layout, dtype expectations, scale defaults, return tuple shape, and deprecation behavior all matter to downstream layers and models.
3. For dispatch work, keep the decorated function as the semantic fallback. Verifiers must be cheap, deterministic, side-effect free, and return `(True, None)` or `(False, reason)`. A rejected backend must fall through to the next backend or to the default implementation.
4. For Triton kernel work, reuse shared kernels where possible, use explicit offset-vector loads/stores with full masks, cast program IDs and address arithmetic to `tl.int64`, and do not introduce `tl.make_block_ptr` or `tl.advance` in mainline Triton code. The Ascend backend is the only documented block-pointer exception.
5. For public-facing PyTorch surfaces and autograd functions, preserve `input_guard` contiguity/device behavior and paired `autocast_custom_fwd` / `autocast_custom_bwd` behavior where the operator already supports mixed precision.
6. Before calling an operator change complete, apply `references/testing-and-correctness.md`: optimized vs reference, forward and backward, deterministic seed, non-power-of-two shapes, varlen and state axes when reachable, dispatch accept/reject/fallback when relevant, and NaN-poisoning awareness.
7. Audit callsites in one pass after shared changes: public wrapper signature, private helper signatures, kernel launch argument order, saved tensors, backward returns, state tuple order, tests, layer/module/model users, and any backend implementation that mirrors the public call surface.
8. Use `references/troubleshooting.md` for shape assertion failures, silent dispatch fallback, optional backend gates, Triton compile failures, NaN failures, and torch.compile/autocast surprises.

## Key guardrails

- Do not relax tolerances or change a validated numerical algorithm to make a test pass without explicit design agreement.
- Do not claim a backend was exercised from numerical parity alone; assert that routing reached the backend or that dispatch was deliberately disabled for the fallback comparison.
- Do not promote forward-only checks for training-capable kernels; gradients and saved-state paths are part of the operator contract.
- Do not make broad public API or checkpoint-visible changes silently. If a change is breaking, keep the non-breaking part separate and flag the compatibility decision.

## Bundled assets

- `references/api-and-dispatch.md`: public op families, verified signatures, q/k/v/g/beta shape cautions, `input_guard` / autocast expectations, dispatch registry, env vars, and backend checklist.
- `references/testing-and-correctness.md`: frozen correctness contract, test axes, forward/backward template, NaN-poisoning behavior, dispatch tests, and callsite audit checklist.
- `references/troubleshooting.md`: symptom-driven recovery for operator imports, shapes, varlen state, dispatch, backend gates, Triton compile errors, NaNs, and API drift.
- `scripts/inspect_fla_ops.py`: safe installed-package helper that imports `fla.ops`, lists public ops, filters by substring, and prints signatures without executing kernels.
