# KDA workflows

This reference summarizes KDA-specific operator, layer, model, gate, backend, and validation knowledge. It is self-contained and does not require opening upstream source files or tests during normal use.

## When to choose KDA

Choose the KDA route when the task involves Kimi Delta Attention's per-key-dimension gate. KDA differs from scalar-gate delta-rule operators because the forget gate has shape `[B, T, HV, K]` and acts per key dimension. That per-dimension gate changes both the WY representation and context-parallel preprocessing, so generic gated-delta-rule guidance is not sufficient for KDA gate or CP work.

Use KDA-specific guidance for:

- KDA operator calls: `chunk_kda`, `fused_recurrent_kda`, gate helpers, KDA backward/intra paths.
- KDA layers and models: `KimiDeltaAttention`, `KDAConfig`, `KDAModel`, `KDAForCausalLM`.
- Safe-gate numerical behavior, raw versus precomputed gates, FlashKDA, TileLang KDA backward, and Triton-Ascend KDA.
- Distributed KDA context parallel and intra-card context-parallel prefill.

## Package and runtime prerequisites

- Python requirement: `>=3.10`.
- Base project dependencies include `transformers>=4.45.0` and `einops`; `torch` and `triton` are selected through backend extras.
- Backend extras exposed by package metadata: `cuda`, `rocm`, `xpu`, `npu`, `cpu`, `tilelang`, `conv1d`, `benchmark`, and `test`.
- KDA kernels are Triton/backend-oriented. CPU installations are useful for import/signature checks, but operator correctness/performance claims usually need a supported accelerator.
- Ascend NPU uses the `npu` extra with `torch_npu` and `triton-ascend`; CUDA uses upstream Triton.

## `chunk_kda` operating contract

Primary signature:

```python
chunk_kda(
    q, k, v, g, beta,
    scale=None,
    initial_state=None,
    output_final_state=False,
    use_qk_l2norm_in_kernel=False,
    use_gate_in_kernel=False,
    use_beta_sigmoid_in_kernel=False,
    allow_neg_eigval=False,
    safe_gate=False,
    lower_bound=None,
    disable_recompute=False,
    return_intermediate_states=False,
    state_v_first=False,
    cu_seqlens=None,
    cu_seqlens_cpu=None,
    cp_context=None,
    **kwargs,
)
```

Required tensors and shapes:

| Argument | Shape | Notes |
| --- | --- | --- |
| `q`, `k` | `[B, T, H, K]` | Must have the same shape. If `use_qk_l2norm_in_kernel=False`, pass normalized q/k when matching KDA references. |
| `v` | `[B, T, HV, V]` | GVA is active when `HV > H`; `HV % H == 0` is required. |
| `g` | `[B, T, HV, K]` | Raw gate input when `use_gate_in_kernel=True`; precomputed log-space decay when `False`. |
| `beta` | `[B, T, HV]` | Raw logits when `use_beta_sigmoid_in_kernel=True`; post-sigmoid values when `False`. |
| `A_log` | `[HV]` | Passed through `kwargs`; required when `use_gate_in_kernel=True`. |
| `dt_bias` | `[HV * K]` or compatible flattened bias | Optional with `use_gate_in_kernel=True`; KDA layer stores this flattened. |
| `initial_state` | `[N, HV, K, V]` or `[N, HV, V, K]` with `state_v_first=True` | Must be `float32`; not supported together with `cp_context`. |
| `cu_seqlens` | `[N + 1]` | For varlen, flatten inputs to `B == 1`; `initial_state.shape[0]` must equal `N` when provided. |

Additional constraints:

- `K <= 256`.
- `chunk_size` is passed through `kwargs` and must be `32` or `64`.
- `scale` defaults to `K ** -0.5`.
- `allow_neg_eigval=True` requires `use_beta_sigmoid_in_kernel=True`; beta then uses `2 * sigmoid(beta)` instead of `sigmoid(beta)`.
- `return_intermediate_states=True` is an inference-mode feature and returns `(o, final_state, h)`; `h` has chunk-state shape `[B, NT, HV, K, V]` in normal layout and uses bf16-style state storage in the kernel path.
- `transpose_state_layout` is a deprecated alias for `state_v_first`; passing both names is rejected.

## Gate modes

### Precomputed-gate mode

Use this when the caller already computed the log-space decay tensor:

```python
o, ht = chunk_kda(q, k, v, g, beta, use_gate_in_kernel=False)
```

- `g` is already the log-space KDA decay with shape `[B, T, HV, K]`.
- `A_log`, `dt_bias`, and `lower_bound` are not used to compute the gate.
- If `safe_gate=True` is also used in this mode, make the invariant explicit: `g` must already be clamped to the safe range, usually `[-5, 0)`. The operator does not apply `lower_bound` when `use_gate_in_kernel=False`.

### Raw-gate in-kernel mode

Use this when the caller wants the operator to fuse gate activation and chunk cumsum:

```python
o, ht = chunk_kda(
    q, k, v, raw_g, raw_beta,
    A_log=A_log,
    dt_bias=dt_bias,
    use_qk_l2norm_in_kernel=True,
    use_gate_in_kernel=True,
    use_beta_sigmoid_in_kernel=True,
)
```

- `g` is raw input before KDA gate activation.
- `A_log` is required; `dt_bias` is optional.
- Non-safe activation: `-exp(A_log) * softplus(g + dt_bias)`.
- Safe activation: `lower_bound * sigmoid(exp(A_log) * (g + dt_bias))`.
- With `safe_gate=True` and `use_gate_in_kernel=True`, `lower_bound` is required and must satisfy `-5 <= lower_bound < 0`; the recommended value is `-5.0`.

### Why `safe_gate` changes more than validation

`safe_gate=True` selects KDA's safe intra path. That path uses 16-token diagonal sub-chunks and midpoint/paired decay offsets so exponentiation stays bounded under `lower_bound=-5`. Non-safe KDA uses the token-parallel intra path for the diagonal part and the shared inter/solve kernel with a different safety flag. When changing gate math, check both safe and non-safe paths unless the task is explicitly scoped to one.

## `fused_recurrent_kda` operating contract

Primary signature:

```python
fused_recurrent_kda(
    q, k, v, g, beta,
    A_log=None,
    dt_bias=None,
    scale=None,
    initial_state=None,
    output_final_state=False,
    use_qk_l2norm_in_kernel=False,
    use_gate_in_kernel=False,
    use_beta_sigmoid_in_kernel=False,
    allow_neg_eigval=False,
    lower_bound=None,
    state_v_first=False,
    cu_seqlens=None,
    **kwargs,
)
```

Use this route for recurrent/decode-style KDA when distributed `cp_context` is not needed. It supports raw gate fusion through `use_gate_in_kernel=True`, `A_log`, `dt_bias`, and `lower_bound`, plus beta sigmoid fusion and `state_v_first`. It does not expose a `safe_gate` flag, does not accept `cp_context`, and is not the training path chosen by `KimiDeltaAttention`.

## KimiDeltaAttention layer workflow

`KimiDeltaAttention` wraps KDA projections and chooses an operator mode:

```python
KimiDeltaAttention(
    hidden_size=2048,
    expand_v=1,
    head_dim=128,
    num_heads=16,
    num_v_heads=None,
    mode="chunk",
    use_short_conv=True,
    allow_neg_eigval=False,
    safe_gate=False,
    lower_bound=None,
    conv_size=4,
    conv_bias=False,
    layer_idx=None,
    norm_eps=1e-5,
)
```

Layer-specific rules:

- `num_v_heads` defaults to `num_heads`; if `num_v_heads > num_heads`, it must be divisible by `num_heads`.
- `head_v_dim = int(head_dim * expand_v)` and the product must be integer-compatible with linear and RMSNorm-gated projection dimensions.
- Supported layer modes are `chunk` and `fused_recurrent`.
- In training, the layer asserts chunk mode only.
- During non-training forward, if `q_len <= 64`, the layer uses `fused_recurrent` for decode-style execution; otherwise it uses `self.mode`.
- The layer always calls KDA operators with `use_qk_l2norm_in_kernel=True`, `use_gate_in_kernel=True`, `use_beta_sigmoid_in_kernel=True`, `A_log`, `dt_bias`, `allow_neg_eigval`, and `state_v_first=True`.
- If `safe_gate=True`, the layer initializes `A_log` to zeros; otherwise `A_log` is initialized from a log-uniform range. `dt_bias` uses the same inverse-softplus-style initialization as the operator tests.

## KDAConfig and model workflow

`KDAConfig` has model type `kda` and configures `KDAModel` / `KDAForCausalLM`. Key KDA fields:

| Field | Default | Meaning |
| --- | --- | --- |
| `attn_mode` | `"chunk"` | Passed to each `KimiDeltaAttention` unless a hybrid attention spec replaces the layer. |
| `hidden_size` | `2048` | Embedding and residual width. |
| `expand_v` | `1.0` | Value head-dim expansion. |
| `use_short_conv` | `True` | Enables KDA q/k/v short convolution wrappers. |
| `allow_neg_eigval` | `False` | Enables beta scaling to `[0, 2)` when beta sigmoid is fused. |
| `safe_gate` | `False` | Propagates to KDA layers. |
| `lower_bound` | `None` | Required by config validation when `safe_gate=True`; recommended `-5.0`. |
| `conv_size` | `4` | Short convolution kernel size. |
| `head_dim` | `128` | KDA key head dimension. |
| `num_heads` | `16` | q/k head count. |
| `num_v_heads` | `None` | Value/gate head count; defaults to q/k head count at layer construction. |
| `attnres_block_size` | `None` | Optional attention-residual aggregation mode; if set and not `1`, must be an even integer at least `2`. |

`KDABlock` uses normal attention instead of KDA when the hybrid attention config supplies an attention spec for that layer; otherwise it constructs `KimiDeltaAttention` with the KDA config fields above.

## Optional KDA backend gates

Use generic dispatch guidance for registry internals; this section only lists KDA-specific verifier facts.

### FlashKDA CUTLASS forward

- Env var: `FLA_FLASH_KDA`; enabled by default when the `flash_kda` package is importable. Set `FLA_FLASH_KDA=0` to force the Triton path.
- Scope: `chunk_kda` forward only, inference mode only.
- Required call shape and flags:
  - `torch.inference_mode()` / grad disabled.
  - dtype `bfloat16`.
  - `K == 128` and `V == 128`.
  - No GVA: `HV == H`.
  - `use_qk_l2norm_in_kernel=True`.
  - `use_gate_in_kernel=True` with `A_log` and optional `dt_bias`.
  - `use_beta_sigmoid_in_kernel=True`.
  - `safe_gate=True`, normally with `lower_bound=-5.0`.
  - `state_v_first=True`.
  - No `cp_context` and no `return_intermediate_states`.
- Validation comparison candidate: compare FlashKDA output/final state against high-precision `fused_recurrent_kda` using bf16 inputs, K/V head dim 128, raw gate, raw beta, `safe_gate=True`, and `state_v_first=True`; include varlen cases with flattened `B == 1` and `cu_seqlens`.

### TileLang KDA backward

- Env var: `FLA_TILELANG`; enabled by default when `tilelang` is importable and usable `nvcc` is available. Set `FLA_TILELANG=0` to force Triton.
- Scope: KDA `chunk_kda_bwd_wy_dqkg_fused` backward subpath, not the entire operator.
- Verifier rejects grouped-value/GQA cases where `v.shape[2] != k.shape[2]`. For GVA (`HV > H`), expect fallback to the default Triton path unless the caller explicitly reshapes/repeats q/k to match value heads.

### Triton-Ascend KDA backend

- Scope: Ascend NPU KDA gate, intra, WY recompute, backward, and fused recurrent forward paths.
- Availability: selected when the runtime reports NPU support; no user env var is needed for this backend.
- Verifier constraints include chunk sizes `32` or `64` for intra paths and backward subchunk alignment by `16`.
- Validation candidate: spy/record backend calls while running safe and non-safe `chunk_kda` and `fused_recurrent_kda_fwd`; confirm safe path hits gate chunk cumsum, KDA intra, WY recompute, dAv, dqkg fused, bwd intra, and gate backward; confirm non-safe path hits the token-parallel intra variant.

### Backend-dispatch master switch

`FLA_DISABLE_BACKEND_DISPATCH=1` bypasses all optional backend dispatch. Use it when you need to prove default Triton behavior or rule out verifier/fallback confusion.

## Native validation candidates

Do not run these automatically inside drafting workflows. Use them as verifier-owned candidates when the environment and hardware match the case.

1. **Chunk KDA parity grid**: forward/backward `chunk_kda` against a naive recurrent reference across dense and GVA shapes, fp16/bf16, `chunk_size` 32/64, `use_qk_l2norm_in_kernel` true/false, `use_gate_in_kernel` true/false, `safe_gate` true/false, `disable_recompute` true/false, initial/final state, and gradients for q/k/v/g/beta/A/dt_bias/h0.
2. **Varlen KDA parity**: flattened `B == 1`, ragged `cu_seqlens`, optional `cu_seqlens_cpu`, per-sequence initial states, raw-gate and precomputed-gate modes, chunk sizes 32/64, and forward/backward parity against per-sequence naive recurrent KDA.
3. **State-layout equivalence**: compare `state_v_first=True` against default `[K, V]` state layout for both `chunk_kda` and `fused_recurrent_kda`, including the deprecated `transpose_state_layout` warning/rejection behavior.
4. **Beta sigmoid and negative eigenvalues**: compare post-sigmoid beta to `use_beta_sigmoid_in_kernel=True`; when `allow_neg_eigval=True`, expected beta multiplier is `2`.
5. **Gate helper parity**: compare fused KDA gate to naive gate functions with and without `dt_bias` and with `lower_bound=-5.0`.
6. **FlashKDA inference**: bf16, K=V=128, `state_v_first=True`, raw gate/raw beta, safe-gate lower bound, no GVA, no CP; compare against high-precision fused recurrent reference.
7. **Triton-Ascend routing**: on NPU only, ensure KDA verifier acceptance actually dispatches to Ascend KDA ops and verifier rejection falls back.
