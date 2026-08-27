# Merge-method catalog and selection

The installed registry exposes these exact method names:

`linear`, `slerp`, `nuslerp`, `multislerp`, `karcher`, `task_arithmetic`,
`ties`, `dare_linear`, `dare_ties`, `della`, `della_linear`, `breadcrumbs`,
`breadcrumbs_ties`, `sce`, `ram`, `ramplus_tl`, `model_stock`, `nearswap`,
`arcee_fusion`, and `passthrough`.

Use the method name exactly as written. A method can pass through a single
input in some implementation paths, but the cardinalities below describe the
intended safe configuration and the method's explicit failure checks.

## Selection table

| Method | Effective inputs | Base model | Main parameters and cautions |
|---|---|---|---|
| `linear` | Two or more whole models or slice sources; one is also useful for a copy | Not normally needed | Per-input required `weight`; global `normalize` defaults true |
| `slerp` | Exactly two models/tensors | Required and must be one of them | Required global `t`; rejects more than two; use for a two-way interpolation |
| `nuslerp` | Exactly two merge models | Optional, but if present is a distinct third input | Required per-input `weight`; `nuslerp_flatten` defaults true; `nuslerp_row_wise` defaults false; a zero weighted sum is invalid |
| `multislerp` | Two or more | Optional task-vector origin | Per-input `weight`; `normalize_weights` defaults true; `eps` defaults `1e-8`; balanced antipodal inputs can fail |
| `karcher` | Two or more | Not used | `max_iter` defaults 10; `tol` defaults `1e-5`; accelerator work can be expensive |
| `task_arithmetic` | One or more non-base task models | Required | Per-input `weight`; global `lambda` defaults 1.0; `normalize` and `rescale` default false |
| `ties` | Normally two or more non-base task models | Required | Per-input `weight`, `density`; global `normalize` defaults true, `rescale` false, `lambda` 1.0; optional `int8_mask` |
| `dare_linear` | Normally two or more non-base task models | Required | `density` per input; global `rescale` defaults true; random pruning needs `random-seed` for repeatability |
| `dare_ties` | Normally two or more non-base task models | Required | DARE random pruning plus TIES consensus; `density` per input; `rescale` defaults true |
| `della` | Normally two or more non-base task models | Required | `density` and `epsilon` per input; `epsilon` must leave `density - epsilon > 0` and `density + epsilon < 1`; TIES consensus |
| `della_linear` | Normally two or more non-base task models | Required | DELLA pruning without consensus; `density`, `epsilon` per input; `rescale` defaults true |
| `breadcrumbs` | Normally two or more non-base task models | Required | `density` and `gamma` per input; `gamma` removes high-magnitude outliers before the target density |
| `breadcrumbs_ties` | Normally two or more non-base task models | Required | Breadcrumbs pruning plus TIES consensus; `density`, `gamma` per input |
| `sce` | Normally two or more non-base task models | Required | Global `select_topk` defaults 1.0 and `int8_mask` defaults false; selects high-variance positions then applies sign consensus |
| `ram` | One or more non-base task models | Required | Global `epsilon` threshold is `1e-5`; designed for sparse/heterogeneous task vectors |
| `ramplus_tl` | One or more non-base task models | Required | Global `r` defaults `0.1`, `alpha` `0.2`, `epsilon` `1e-5`; tensor-local unique-contribution rescaling |
| `model_stock` | At least two non-base models plus the base (three total) | Required | `filter_wise` defaults false; computes a data-driven interpolation from model relationships |
| `nearswap` | Exactly one non-base model plus base | Required | Required global `t`; rejects more than one non-base tensor |
| `arcee_fusion` | Exactly one non-base model plus base | Required | No configurable merge parameter; uses a dynamic importance mask |
| `passthrough` | Exactly one source per output tensor | Not needed | Optional per-input `scale`; use slices for layer stacking or selective scaling |

“Normally” reflects the documented use contract, while the planner may permit a
single input and some tasks intentionally return it unchanged. Do not rely on
that shortcut to satisfy a method that conceptually needs task interference or
consensus.

## Parameter families

### Linear, interpolation, and passthrough

- `linear`: put `weight` on each model/source. `normalize: true` divides by the
  weight sum; set it false only when signed or intentionally unnormalized
  weights are required.
- `slerp`: put the interpolation factor in global `parameters.t`. A filtered
  gradient can vary `t` by tensor/layer; the base model is the `t=0` endpoint.
- `nuslerp`: `weight` is required for each of the two merge models. The effective
  interpolation factor is derived from their weights. With a base, it operates
  on task vectors relative to that distinct base.
- `multislerp`: `weight` is required for each input. `normalize_weights` and
  `eps` are global. Avoid exactly balancing antipodal vectors.
- `passthrough`: set `scale` per source when a tensor should be multiplied; a
  filtered `scale` is useful for zeroing or attenuating named layers.

### Task-vector and sparsification family

`task_arithmetic`, `ties`, `dare_linear`, `dare_ties`, `della`,
`della_linear`, `breadcrumbs`, `breadcrumbs_ties`, `sce`, `ram`, and
`ramplus_tl` require a base tensor and compute deltas for non-base inputs.
Ensure the base is present or let whole-model normalization add it.

- `weight` is a required per-input coefficient for non-base task models. The
  planner does not require it for the base input because the base is not a
  task vector.
- `density` is the fraction retained by sparsification. Do not use zero unless
  the method explicitly supports the intended degenerate case.
- `lambda` is a global scale for the summed task vector. `normalize` and
  `rescale` are global controls; method defaults differ, so state them when
  reproducibility matters.
- `int8_mask` requests an int8 consensus mask and can reduce mask memory; it is
  not a model quantization switch.
- `gamma` applies to Breadcrumbs methods and controls removal of the largest
  magnitude changes before reaching target density.
- `epsilon` is per-input for DELLA's adaptive pruning. It is global for RAM's
  “changed versus unchanged” threshold and for `ramplus_tl`; do not confuse the
  two uses.
- `select_topk` is global for SCE and retains the highest-variance fraction of
  tensor positions before sign consensus.
- `r` and `alpha` are global only for `ramplus_tl` and control its unique-vector
  rescaling.

Randomized DARE methods require a deliberate seed when comparing runs. Use
`--random-seed INTEGER`; the seed affects randomized pruning, not model
reference resolution.

### Other methods

- `model_stock` needs a base and at least two other models. `filter_wise: true`
  changes its similarity/weight calculation to row/filter granularity and is
  not a generic “filter models” switch.
- `karcher` uses equal weights internally; its `max_iter` and `tol` tune
  convergence rather than model contribution.
- `arcee_fusion` and `nearswap` are base-relative two-model methods. `nearswap`
  uses `t` to increase the pull toward the secondary tensor where it is close to
  the base; `arcee_fusion` has no user method parameter.

## Method-choice decision path

1. Need layer stacking or a no-op donor? Choose `passthrough` with `slices`.
2. Need a simple weighted average? Choose `linear` and provide every weight.
3. Need a two-way geometric interpolation? Choose `slerp`; use `nuslerp` when
   you need optional task-vector-relative interpolation or row/flatten controls.
4. Need a multi-model spherical average? Choose `multislerp`; choose `karcher`
   when iterative manifold averaging is acceptable.
5. Have a shared base and fine-tuned variants? Start with `task_arithmetic`;
   choose TIES/DARE/DELLA/Breadcrumbs/SCE based on sparsification, randomness,
   magnitude, variance, and sign-consensus needs.
6. Have sparse heterogeneous agent changes? Compare `ram` and `ramplus_tl`.
7. Need relationship-derived interpolation from a base plus two variants? Use
   `model_stock`.
8. Need selective two-model behavior? Use `nearswap` or `arcee_fusion` only
   with the exact base/non-base cardinality.

## Registered-method failure signals

- `Unimplemented merge method ...`: the spelling is not in the registry; do
  not assume a name from another mergekit version.
- `expects exactly two models`: remove extra references, including an
  accidentally distinct base; check whether whole-model normalization added a
  missing base.
- `Base model not in input tensors`: add the base to the input topology or
  confirm that its reference string exactly matches the input reference.
- `Missing required parameter weight/t/...`: put the value at a level reached by
  the effective topology and provide an unfiltered fallback.
- `weighted sum ... is zero`: change signed/antipodal weights or use a method
  that does not require the spherical weighted sum.
- `Della` validation or NaN/invalid probability errors: reduce `epsilon` so
  the density bounds are strictly inside 0 and 1.
- shape mismatch: stop method tuning and route tensor shapes, architecture
  conversion, or checkpoint compatibility to model-io-and-architecture.

Custom method registration and method evolution are outside this route; use the
extension sibling rather than inventing a YAML escape hatch.
