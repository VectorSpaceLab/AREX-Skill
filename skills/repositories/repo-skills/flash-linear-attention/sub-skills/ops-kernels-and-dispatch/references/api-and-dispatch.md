# API and dispatch facts for `fla.ops`

This reference distills the public operator surface, common tensor contracts, `input_guard` / autocast expectations, and backend dispatch rules needed to maintain FLA operators without opening source docs or native tests.

## Public operator families

The root `fla.ops` export set contains these public names grouped by execution-mode prefix:

| Mode family | Public exports |
| --- | --- |
| `chunk_*` | `chunk_abc`, `chunk_comba`, `chunk_delta_rule`, `chunk_dplr_delta_rule`, `chunk_gated_delta_rule`, `chunk_gdn`, `chunk_gla`, `chunk_gsa`, `chunk_iplr_delta_rule`, `chunk_kda`, `chunk_lightning_attn`, `chunk_linear_attn`, `chunk_log_linear_attn`, `chunk_mesa_net`, `chunk_retention`, `chunk_rwkv6`, `chunk_rwkv7`, `chunk_simple_gla` |
| `fused_recurrent_*` | `fused_recurrent_comba`, `fused_recurrent_delta_rule`, `fused_recurrent_dplr_delta_rule`, `fused_recurrent_gated_delta_rule`, `fused_recurrent_gdn`, `fused_recurrent_gla`, `fused_recurrent_gsa`, `fused_recurrent_hgrn`, `fused_recurrent_iplr_delta_rule`, `fused_recurrent_kda`, `fused_recurrent_lightning_attn`, `fused_recurrent_linear_attn`, `fused_recurrent_retention`, `fused_recurrent_rwkv6`, `fused_recurrent_rwkv7`, `fused_recurrent_simple_gla` |
| `fused_chunk_*` and fused specials | `fused_chunk_based`, `fused_chunk_delta_rule`, `fused_chunk_gla`, `fused_chunk_linear_attn`, `fused_chunk_retention`, `fused_chunk_simple_gla`, `fused_attnres` |
| `parallel_*` | `parallel_attn`, `parallel_based`, `parallel_forgetting_attn`, `parallel_nsa`, `parallel_parallax`, `parallel_path_attn`, `parallel_retention`, `parallel_simple_gla`, `parallel_wall_attn`, `parallel_wall_attn_decode` |

Mode names are conventions, not interchangeable contracts. Always inspect the target signature before substituting one mode for another.

- `chunk_*`: chunked recurrent kernels, usually state-aware and training-capable. Many support variable-length inputs through `cu_seqlens` and sometimes `cu_seqlens_cpu`.
- `fused_recurrent_*`: recurrent scan path, often used as a reference or decode route. State, reverse, and varlen support are per-op.
- `fused_chunk_*`: chunk path with extra fusion or common-kernel reuse. Some wrappers delegate through `**kwargs`; confirm before changing public kwargs.
- `parallel_*`: attention-style parallel kernels. Return type may be a tensor or a tuple, and options may include windows, block indices, or attention outputs.

## Verified signatures and shape cautions

### `chunk_gla`

```python
chunk_gla(q, k, v, g, scale=None, initial_state=None, output_final_state=False, state_v_first=False, cu_seqlens=None, cu_seqlens_cpu=None) -> (o, final_state)
```

- `q`, `k`, `g`: `[B, T, H, K]`; all three shapes must match.
- `v`: `[B, T, H, V]`; `V` does not have to equal `K`.
- `scale=None` defaults to `K ** -0.5`.
- `initial_state`: dtype `float32`, shape `[N, H, K, V]`, or `[N, H, V, K]` when `state_v_first=True`.
- `cu_seqlens`: flattened varlen mode. Input batch must be `B=1`; `cu_seqlens` has length `N+1`; `initial_state.shape[0]` must equal `N`.

### `chunk_linear_attn`

```python
chunk_linear_attn(q, k, v, scale=None, initial_state=None, output_final_state=False, normalize=True, cu_seqlens=None) -> (o, final_state)
```

- `q`, `k`: `[B, T, H, K]`.
- `v`: `[B, T, H, V]`.
- `scale=None` defaults to `K ** -0.5`.
- `normalize=False`: `initial_state` is a tensor `[B_or_N, H, K, V]`.
- `normalize=True`: `initial_state` may be `(kv_state, z_state)`; `kv_state` follows `[B_or_N, H, K, V]`, and dense `z_state` is shaped `[B, 1, H, K]`. Returned final state mirrors tensor-vs-tuple input.
- `cu_seqlens`: flattened varlen mode with `B=1`; state batch must equal `len(cu_seqlens) - 1`.

### `chunk_kda`

```python
chunk_kda(q, k, v, g, beta, scale=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, use_gate_in_kernel=False, use_beta_sigmoid_in_kernel=False, allow_neg_eigval=False, safe_gate=False, lower_bound=None, disable_recompute=False, return_intermediate_states=False, state_v_first=False, cu_seqlens=None, cu_seqlens_cpu=None, cp_context=None, **kwargs)
```

- `q`, `k`: `[B, T, H, K]`; shapes must match.
- `v`: `[B, T, HV, V]`. Grouped Value Attention uses `HV > H`; `HV % H` must be zero.
- `g`: `[B, T, HV, K]`. With `use_gate_in_kernel=False`, pass precomputed log-space decay. With `True`, pass raw gate input and provide `A_log` plus optional `dt_bias` through `kwargs`.
- `beta`: `[B, T, HV]`. With `use_beta_sigmoid_in_kernel=False`, pass post-sigmoid beta. With `True`, pass raw logits.
- `K <= 256`; `chunk_size` from `kwargs` must be `32` or `64`.
- `initial_state`: dtype `float32`, shape `[N, HV, K, V]`, or `[N, HV, V, K]` when `state_v_first=True`.
- `cu_seqlens`: flattened varlen mode with `B=1`; `initial_state.shape[0]` must equal `len(cu_seqlens) - 1`.
- `allow_neg_eigval=True` requires `use_beta_sigmoid_in_kernel=True`.
- `safe_gate=True` with `use_gate_in_kernel=True` requires `lower_bound` in `[-5, 0)`.
- `return_intermediate_states=True` is inference-only and returns `(o, final_state, h)`.
- `cp_context` overrides `cu_seqlens` and does not support `initial_state` or `output_final_state`.

KDA-specific algorithm and context-parallel details belong outside this generic ops/dispatch reference; preserve only the public API, shape, flag, dispatch, and correctness facts here.

## General q/k/v/g/beta cautions

- Do not assume `K == V`. q/k head dimension and value head dimension are intentionally separate in several ops.
- Do not assume value head count equals q/k head count. KDA uses `HV`, and optional backends can have stricter GVA constraints than the default path.
- Do not silently change raw logits to post-activation tensors. `g` and `beta` mode is part of the public contract.
- In varlen mode, the tensor batch dimension is flattened to `1`; the state batch dimension becomes the number of original sequences.
- `state_v_first=True` changes only state layout, not output tensor layout. Keep initial state, final state, and state-gradient layout consistent.
- Deprecated aliases such as `transpose_state_layout` may still be supported by selected ops. Preserve warnings and the error when both old and new names are passed.

## `input_guard` and autocast expectations

`input_guard` makes tensor inputs contiguous and enters the custom device context for the first tensor argument. Public-facing op surfaces should preserve this behavior when already present, and new public PyTorch operator surfaces should include it unless there is a deliberate reason not to.

`autocast_custom_fwd` and `autocast_custom_bwd` are device-aware wrappers for mixed-precision autograd `Function` paths. Keep forward and backward handling paired; a mixed-precision forward without the matching backward wrapper is not a complete autocast contract.

Evidence-backed patterns to keep:

- KDA chunk autograd `forward` and `backward` use `input_guard` and the paired autocast wrappers.
- GLA chunk autograd `forward` and `backward` use `input_guard`, while the public wrapper performs shape/state validation before invoking the autograd function.
- Several public wrappers and all dispatch wrappers are marked `torch.compiler.disable`; keep runtime backend selection outside compiled graphs.

## Dispatch model

FLA's generic backend dispatch system uses:

- `BaseBackend`: defines `backend_type`, optional `package_name`, optional `env_var`, `default_enable`, and `priority`.
- `BackendRegistry('<operation>')`: per-operation registry populated by the operation backend package.
- `@dispatch('<operation>')`: public wrapper decorator that lazy-imports the backend package, tries backends by priority, consults verifiers, and falls back to the original implementation when no backend handles the call.

Behavior to preserve:

1. `FLA_DISABLE_BACKEND_DISPATCH=1` bypasses dispatch and returns the original implementation.
2. Normal operation names lazy-import `fla.ops.<operation>.backends`; explicit special mappings are owned by the dispatch system.
3. Backends are considered only when `is_available()` and `is_enabled()` are both true.
4. A verifier named `<func_name>_verifier` must return `(True, None)` or `(False, reason)`. Rejection tries the next backend or default fallback.
5. Runtime dispatch avoids the cached `can_use()` path because cached wrappers are not torch.compile friendly.
6. The dispatch wrapper itself is `torch.compiler.disable`; keep backend selection in Python and compiled work inside the selected implementation.

## Dispatch-related environment variables

| Variable | Default behavior | Maintainer use |
| --- | --- | --- |
| `FLA_DISABLE_BACKEND_DISPATCH` | unset/`0` active; `1` bypasses all dispatch | Force default fallback for correctness isolation. |
| `FLA_TILELANG` | backend-specific default; explicit `0` disables and `1` enables where package/compiler probes pass | Gate TileLang backends; CUDA TileLang paths require `tilelang` and a usable compiler probe. |
| `FLA_FLASH_KDA` | enabled when `flash_kda` is importable and verifier accepts | Gate FlashKDA CUTLASS forward backend for `chunk_kda`; verifier is inference-only and shape/flag constrained. |
| `FLA_FLASH_QLA` | enabled when `flash_qla`, hardware, dtype, and flags are supported | Gate FlashQLA backend for gated delta rule. |
| `FLA_INTRACARD_CP` | disabled by default | Opt in to intra-card context-parallel backend for shared delta-rule state helpers. |
| `FLA_INTRACARD_MAX_SPLITS` | `32` | Limit intra-card CP split count and merge depth. |
| `FLA_ATTNRES_GLUON` | disabled by default | Opt in to Gluon AttnRes backend. |
| `FLA_USE_TMA` | disabled by default | Enable TMA only for supported kernels with alignment and benchmark evidence. |
| `FLA_USE_FAST_OPS` | disabled by default | Allow faster but less accurate shared math intrinsics; do not change numerical expectations silently. |
| `FLA_CACHE_MODE`, `FLA_CACHE_RESULTS`, `FLA_CONFIG_DIR`, `FLA_GPU_NAME` | configure Triton config cache/autotune behavior | Diagnose wrong config or repeated autotune. |
| `FLA_DISABLE_TENSOR_CACHE` | tensor cache enabled where used | Debug identity-based tensor cache behavior. |
| `FLA_CI_ENV` | unset/`0` | CI mode can loosen assertions; do not use it to hide local correctness failures. |

Set dispatch env vars before Python starts unless a scoped test deliberately resets caches and imports.

## Backend implementation checklist

1. Register a `BaseBackend` subclass in the operation backend package.
2. Set `backend_type`, `package_name`, `env_var`, `default_enable`, and `priority` deliberately.
3. Implement verifier methods with the same public call surface as the decorated function.
4. Keep verifiers side-effect free: no tensor mutation, environment mutation, registry mutation, RNG use, cache writes, or kernel launches.
5. Return precise rejection reasons; they are user-facing and often asserted in tests.
6. Keep optional package imports lazy inside implementation methods when absence should be supported.
7. Match fallback return values exactly.
8. Add route tests for backend acceptance, verifier rejection, and fallback. Numerical parity alone cannot prove dispatch occurred.

## Kernel implementation checklist

- Reuse shared helper kernels or validated helper patterns before duplicating per-op kernels.
- Use explicit offset vectors with plain `tl.load` / `tl.store`; mask every dimension that can overrun.
- Provide `other=` for masked loads when masked lanes enter computation.
- Assert or verify any divisibility assumption used by pointer math.
- Cast program IDs, grid-derived indices, sequence offsets, strides, and element offsets to `tl.int64` before multiplication or address arithmetic.
- Do not introduce `tl.make_block_ptr` or `tl.advance` in mainline Triton code. The Ascend backend is the documented exception.
- Treat `tl.make_tensor_descriptor` / TMA as opt-in hot-path optimization, not a default pointer model.
- Keep kernel signatures, launch argument order, autograd saves, backward return positions, and public wrapper kwargs synchronized in one edit.
