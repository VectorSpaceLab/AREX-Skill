# KDA troubleshooting

Use this matrix to diagnose KDA operator, layer/model, backend, and context-parallel issues quickly.

## Import and environment issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Importing `fla` fails after a bare install | Base package metadata does not install `torch` or `triton`; a backend extra is required. | Install or activate an environment with the intended backend extra and matching PyTorch wheel source. CPU is import-oriented; accelerator checks need matching hardware. |
| CUDA KDA kernels fail to compile or import Triton | Torch/Triton/CUDA mismatch. | Confirm the environment uses a supported torch version and backend-compatible Triton. Disable optional KDA backends first so the default path is isolated. |
| NPU route does not work | Ascend requires `torch_npu` and `triton-ascend`, not upstream Triton. | Use an NPU-prepared environment and verify NPU availability before expecting Triton-Ascend KDA dispatch. |
| TileLang path never activates | `tilelang` is missing, `nvcc` is not usable, `FLA_TILELANG=0`, or verifier rejects GVA. | Verify `tilelang` import and `nvcc`; for GVA (`HV > H`), expect fallback unless q/k are reshaped to match v heads. |
| FlashKDA path never activates | Missing `flash_kda`, `FLA_FLASH_KDA=0`, grad enabled, dtype/shape/flag mismatch, CP present, or GVA. | Use inference mode, bf16, K=V=128, `HV==H`, raw gate/raw beta, `safe_gate=True`, `lower_bound=-5.0`, `state_v_first=True`, and no `cp_context`. |

## Shape and argument errors

| Error or symptom | Cause | Fix |
| --- | --- | --- |
| `q and k must have the same shape` | q/k shape mismatch. | Use `[B, T, H, K]` for both. |
| `g must have shape [B, T, HV, K]` | Gate heads or key dimension do not match v/q. | Derive `HV` from `v.shape[2]` and `K` from `q.shape[-1]`; reshape `g` accordingly. |
| `beta must have shape [B, T, HV]` | Beta head dimension does not match v/g heads. | Use one beta per value/gate head. |
| `Currently we only support key headdim <=256` | KDA key head dimension too large. | Reduce `K` or route to a different implementation if available. |
| `num_v_heads must be divisible by num_heads` or `HV % H` assertion | Invalid grouped value attention layout. | Choose `HV == H` or an integer multiple of q/k heads. |
| `chunk_size must be either 32 or 64` | Unsupported KDA chunk size. | Use `chunk_size=32` or `chunk_size=64`. |
| Varlen batch-size error | `cu_seqlens` requires flattened inputs. | Reshape ragged batches to `B == 1`, concatenate tokens along T, and pass `cu_seqlens` of length `N+1`. |
| Initial-state count error in varlen | `initial_state.shape[0]` differs from `len(cu_seqlens)-1`. | Provide one state per sequence, or omit `initial_state`. |
| `initial_state must be in float32` | State dtype is fp16/bf16. | Cast initial states to `torch.float32`; keep q/k/v/g/beta in the intended kernel dtype. |
| Layout mismatch when comparing states | `state_v_first=True` returns `[N, HV, V, K]`, default uses `[N, HV, K, V]`. | Transpose the last two state dimensions before comparing across layouts. |

## Gate and beta failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `A_log must be provided when use_gate_in_kernel=True` | Raw-gate mode missing KDA gate parameter. | Pass `A_log` with shape `[HV]`; pass `dt_bias` if the model/layer uses it. |
| `lower_bound must be specified` | `safe_gate=True` with raw in-kernel gate but no lower bound. | Pass `lower_bound=-5.0` unless a validated alternative in `[-5, 0)` is required. |
| `lower_bound must be in the safe range [-5, 0)` | Out-of-range safe-gate lower bound. | Use `-5.0 <= lower_bound < 0`. |
| Safe-gate results differ only in precomputed-gate mode | `safe_gate=True` was set but `g` was not actually clamped/proven safe. | In precomputed mode, clamp or construct `g` in `[-5, 0)` yourself and document that invariant. |
| `allow_neg_eigval=True` rejected | Beta sigmoid fusion is disabled. | Set `use_beta_sigmoid_in_kernel=True`; then beta uses `2 * sigmoid(beta)`. |
| Gate gradients for `A_log` or `dt_bias` are noisy | KDA gate derivatives are sensitive to dtype and raw gate scale. | Compare against the correct naive gate (`lower_bound` version for safe gate), use float32 reference gate math, and apply tolerance consistent with KDA native candidates. |

## Layer and model issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| Training asserts only chunk mode is supported | `KimiDeltaAttention` switched to fused recurrent while `self.training` is true. | Use `mode="chunk"` for training. |
| Decode unexpectedly uses fused recurrent | The layer switches to `fused_recurrent` when `q_len <= 64` and not training. | This is expected. If comparing routes, call the operator directly or choose sequence lengths deliberately. |
| `KDAConfig(safe_gate=True)` raises | Config requires a lower bound when safe gate is enabled. | Set `lower_bound=-5.0`. |
| `expand_v` construction error | Value dimension or per-head value dimension is not integer-compatible. | Choose `expand_v` so `num_v_heads * head_dim * expand_v` and `head_dim * expand_v` are integer-compatible. |
| KDA layer uses normal attention for some layers | Hybrid attention spec can replace KDA in `KDABlock`. | Inspect or control the config's hybrid attention field before assuming every block is KDA. |

## Context-parallel failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| CP call rejects `initial_state` or `output_final_state` | KDA CP owns cross-rank state synchronization. | Remove `initial_state` and keep `output_final_state=False` in CP mode. |
| CP call says `cu_seqlens` is required | `cp_context` was built without usable sequence metadata. | Build `cp_context` from global `cu_seqlens` before slicing; pass the context into `chunk_kda`. |
| CP result disagrees at sequence boundaries | Global `cu_seqlens`, local slicing, and rank-local context metadata are inconsistent. | Verify global boundaries first, then print rank-local `cp_context.cu_seqlens`, first/last-rank flags, and local slice ranges. |
| KDA CP gradients are much worse than expected | Wrong pre-gated tensor family, stale initial state, merge-kernel shape mismatch, or bf16 communication noise beyond expected range. | Confirm CP pre-process and main kernels both use KDA pre-gated `kg`/`qg` with `gk`; compare to per-sequence naive recurrent KDA and target roughly sub-`5e-3` norm-ratio for bf16 safe-gate unaligned cuts. |
| Distributed test hangs | Process group, rank env, or GPU assignment issue. | Do not debug through the runtime skill helper. Use a verifier-owned distributed harness with explicit `MASTER_ADDR`, `MASTER_PORT`, `RANK`, `WORLD_SIZE`, `LOCAL_RANK`, and cleanup. |
| Intra-card CP does not engage | Env var unset/zero, not in `torch.inference_mode()`, no `cu_seqlens`, or sequence too short so it early-returns. | Set `FLA_INTRACARD_CP=1`, use inference mode and varlen inputs, and choose long enough sequences only when intentionally validating this path. |

## Backend fallback confusion

- Optional backends usually fail verifier checks and then silently fall back to the default implementation.
- To isolate default KDA behavior, set `FLA_DISABLE_BACKEND_DISPATCH=1` before importing/using FLA in the process.
- To isolate a single optional path, disable unrelated gates (`FLA_FLASH_KDA=0`, `FLA_TILELANG=0`, `FLA_INTRACARD_CP=0`) and then enable only the target path.
- Backend env vars are process-level decisions. For reproducible comparisons, set them before the first relevant import/call and record them in the verification note.

## Fast safe checks

- `scripts/smoke_kda.py --help`: parser check; no imports or kernels required.
- `scripts/smoke_kda.py`: imports KDA APIs and prints signatures/config facts in the active environment.
- `scripts/smoke_kda.py --require-cuda`: runs one tiny CUDA `chunk_kda` forward smoke with raw gate, beta sigmoid, safe gate, and no distributed launch.
