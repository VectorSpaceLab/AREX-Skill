# KDA context parallel

This reference covers distributed `cp_context` and intra-card context parallel for KDA. It is self-contained and avoids requiring any distributed launch by default.

## Route decision

Use KDA context-parallel guidance when the task involves any of the following:

- Passing `cp_context` into `chunk_kda`.
- Splitting a long KDA sequence across multiple ranks while preserving recurrent state dependencies.
- Debugging KDA CP precision, rank-local `cu_seqlens`, gradient communication, or safe-gate CP behavior.
- Opting into the intra-card context-parallel backend for long varlen KDA inference/prefill.

Do not use `cp_context` with `fused_recurrent_kda`; KDA CP is an operator-level `chunk_kda` feature.

## Build context API

```python
from fla.ops.cp import build_cp_context

cp_context = build_cp_context(
    cu_seqlens=cu_seqlens_global,
    group=dist.group.WORLD,
    conv1d_kernel_size=None,
    cu_seqlens_cpu=None,
)
```

- `cu_seqlens_global` is the global cumulative sequence-length tensor before sequence partitioning.
- `group` is the process group used for CP communication.
- `conv1d_kernel_size` is only needed when a causal-convolution CP path also consumes the context.
- `cu_seqlens_cpu` can be supplied to avoid a device-to-host transfer when the CPU copy is already available.
- The returned `FLACPContext` contains rank-local `cu_seqlens`, optional CPU metadata, first/last-rank flags, pre/post rank counts, and convolution metadata.

## KDA `chunk_kda` CP contract

A CP call looks like this at the operator boundary:

```python
o_local, _ = chunk_kda(
    q=q_local,
    k=k_local,
    v=v_local,
    g=g_local,
    beta=beta_local,
    cp_context=cp_context,
    use_qk_l2norm_in_kernel=True,
    use_gate_in_kernel=True,
    safe_gate=True,
    lower_bound=-5.0,
    A_log=A_log,
    dt_bias=dt_bias,
)
```

Required conditions:

- Use `chunk_kda`; `fused_recurrent_kda` has no `cp_context` parameter.
- Inputs are rank-local sequence slices, commonly shaped `[1, T_local, H, K]` for q/k, `[1, T_local, HV, V]` for v, `[1, T_local, HV, K]` for g, and `[1, T_local, HV]` for beta.
- Varlen convention still applies: `B == 1` and sequence boundaries are represented by `cu_seqlens`.
- Pass global `cu_seqlens` into `build_cp_context`; the context converts it to rank-local metadata.
- Do not also pass `initial_state` or `output_final_state=True`. The operator asserts that both are unsupported in CP mode.
- `cp_context.cu_seqlens` must be present. If `cp_context.cu_seqlens_cpu` is present, the operator uses it as the CPU metadata.
- Test-style distributed runs usually require `T % world_size == 0` because they slice fixed contiguous chunks per rank. If a production partitioner differs, verify the local slicing and context metadata together.

## KDA-specific CP internals to preserve

KDA CP is not just generic state passing; it relies on KDA's per-dimension gate representation.

- KDA's gate is per key dimension: `g` has shape `[B, T, HV, K]`.
- In KDA forward, intra-chunk work computes WY matrices plus pre-gated tensors:
  - `kg = K ⊙ exp2(g_last - g)` for rows of the chunk.
  - `qg = Q ⊙ exp2(g)` for backward.
- CP pre-process and the main state kernel must receive the same tensor family:
  - Forward: pre-process uses `k=kg`, `w=w`, `u=u`, `gk=g`, then the main kernel uses the same `kg` and `gk`.
  - Backward: pre-process uses `q=qg`, `k=kg`, `w=w`, `do=do`, `dv=dv`, `gk=g`, then the main backward state kernel uses the same pre-gated tensors.
- Do not replace the KDA CP path with scalar-gate GDN assumptions. GDN gates inside the common kernel; KDA pre-gates q/k around the WY representation and only passes per-dim `gk` for chunk-level decay.

## Verification and skip guidance

Distributed KDA CP is a native, hardware-dependent candidate. Do not launch it by default from a runtime skill. Validate only when the environment is intentionally prepared for distributed CUDA/NCCL or the target accelerator stack.

Skip or mark blocked when:

- Fewer GPUs/ranks are available than the candidate requires.
- `torch.distributed` cannot initialize the required backend.
- The task is only import/API inspection and does not require CP execution.
- `FLA_DISABLE_BACKEND_DISPATCH=1` is set while the candidate depends on backend dispatch behavior.

Validation expectations distilled from native coverage:

- CP2 sequence cut: multi-sequence varlen input where a sequence crosses the rank boundary.
- CP2 boundary aligned: sequence boundaries line up with rank boundaries.
- CP4 complex distribution: several ragged sequences across four ranks.
- CP4 single long sequence: one sequence split across all ranks.
- All core KDA CP validation cases use raw-gate in-kernel mode with `safe_gate=True` and `lower_bound=-5.0`.
- Include `disable_recompute` and `state_v_first` variants when the changed code touches backward recomputation or state layout.
- A useful acceptance bar for bf16 safe-gate KDA CP with unaligned varlen cuts is roughly below `5e-3` norm-ratio per gradient against a per-token naive reference. Beta-gradient communication can be noisier and may require warning-only interpretation depending on the exact candidate.

## Reference construction for CP parity

A robust CP parity check has four stages:

1. Generate identical global q/k/v/g/beta and upstream gradient tensors on rank 0; broadcast to all ranks.
2. Build a per-sequence naive recurrent KDA reference on rank 0. For raw-gate cases, manually normalize q/k if required, apply the same KDA gate function (`lower_bound` variant for safe gate), and compute each varlen sequence independently.
3. Build `cp_context` from global `cu_seqlens`, slice local rank tensors, call `chunk_kda(..., cp_context=context, ...)`, and run backward locally.
4. All-gather outputs and gradients across ranks, concatenate by sequence dimension, and compare to the reference with CP-specific tolerances.

This construction catches mistakes in gate preprocessing, rank-local `cu_seqlens`, forward state merge, backward state merge, and gradients for q/k/v/g/beta.

## Intra-card context parallel

Intra-card CP is a separate optional backend for the shared delta-rule forward-state kernel used under KDA. It is not a `cp_context` distributed launch.

- Env var: `FLA_INTRACARD_CP`; default disabled. Set `FLA_INTRACARD_CP=1` to opt in.
- Limit env var: `FLA_INTRACARD_MAX_SPLITS`, default `32`, caps the number of sub-sequences per original sequence to control merge-chain depth and precision loss.
- Scope: inference-mode varlen prefill on a single card; no external package is required.
- Verifier conditions: `torch.inference_mode()` must be active and `cu_seqlens` must be present.
- The backend may early-return to the default path when sequences are too short to benefit from splitting.
- Long varlen sequences can trigger a cached precompute path. The cache key uses the Python object identity of `cu_seqlens`, plus split parameters and device, so repeated calls with the same `cu_seqlens` object can reuse precomputed GPU tensors.
- Use `FLA_INTRACARD_CP=0` or unset it to compare against the default path.

Intra-card KDA validation candidate:

- Use a long varlen KDA inference call with `B=1`, large `T`, `cu_seqlens` on device plus CPU copy, raw-gate in-kernel mode, and repeated calls with the same `cu_seqlens` object. Assert that outputs are stable and cache precompute occurs once. Do not use this as a generic tiny smoke because it is intentionally large and CUDA-only.

## Interaction with optional KDA backends

- FlashKDA rejects `cp_context`; do not expect FlashKDA and distributed KDA CP to combine.
- Intra-card CP can be active for KDA calls that use varlen `cu_seqlens` in inference mode because it dispatches inside the shared forward-state kernel.
- TileLang KDA backward is unrelated to distributed CP setup; it affects a KDA backward subpath when installed and verifier-accepted.
- If backend behavior is unclear, compare with `FLA_DISABLE_BACKEND_DISPATCH=1` for a default-path run, then re-enable only the target backend gate.
