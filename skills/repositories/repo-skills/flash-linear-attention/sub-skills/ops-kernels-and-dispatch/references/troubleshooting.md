# Troubleshooting operator, kernel, and dispatch failures

Use this table before changing code in response to an FLA operator failure. The main diagnostic split is: import/runtime environment, public shape contract, dispatch route, kernel compile/runtime behavior, or test harness behavior.

## Symptom-driven recovery

| Symptom | Likely cause | First checks | Corrective action |
| --- | --- | --- | --- |
| `import fla.ops` fails because `torch` or `triton` is missing | Backend dependencies are intentionally not base dependencies | Confirm a backend extra or backend-specific PyTorch install was selected | Fix installation through the setup/backends workflow before debugging kernels. Do not treat a bare package install as a kernel-capable environment. |
| CPU import works but every GPU op fails | CPU/import-only environment or wrong accelerator wheel flavor | Check selected backend family, device visibility, and `torch` backend availability | Use CPU import only as a package-visibility check. GPU/accelerator kernels require matching `torch`/Triton/accelerator wheels and hardware. |
| Shape assertion: q/k/g mismatch | Gate tensor follows the wrong head dimension or wrong op convention | For GLA, `q`, `k`, `g` must all be `[B, T, H, K]`; for KDA, `g` is `[B, T, HV, K]` | Fix the caller or validation. Do not silently reshape a public input unless the public API explicitly permits it. |
| Shape assertion: `v` mismatch | Value heads or value dim confused with q/k heads | Check `v` as `[B, T, H, V]` for GLA/linear attention and `[B, T, HV, V]` for KDA | Preserve output shape `[B, T, H_or_HV, V]`; do not assume `K == V`. |
| KDA rejects GVA | `HV % H != 0` or unsupported backend GVA route | Check `q.shape[2]` vs `v.shape[2]` and backend verifier reason | For default KDA, `HV` must be divisible by `H`. Optional backends may reject GVA even when default Triton supports it. |
| KDA rejects head dimension | `K > 256` for public `chunk_kda` | Inspect `q.shape[-1]` | Add a precise validation, route to a supported implementation, or document unsupported shape. Do not make a kernel launch with unsupported K. |
| Varlen path raises batch-size error | Inputs were not flattened for `cu_seqlens` mode | In varlen mode `q.shape[0]` must be `1`, and `cu_seqlens` length is `N+1` | Flatten dense batches into one packed sequence and make state first dimension equal `N`. |
| Varlen final state count mismatch | `initial_state.shape[0]` still equals dense batch size rather than number of sequences | Compare `initial_state.shape[0]` with `len(cu_seqlens) - 1` | Allocate or reshape state per original sequence count. |
| State dtype assertion | GLA/KDA chunk state passed in fp16/bf16 | Check `initial_state.dtype` | Use fp32 initial state for chunk paths that validate `initial_state.dtype == torch.float32`. |
| `state_v_first` result looks transposed | State layout changed but expected/gradient tensors stayed default | Check state and state-gradient shapes `[K, V]` vs `[V, K]` | Keep state, final state, and state-gradient tensors in the same layout. Do not transpose only the input state. |
| `transpose_state_layout` plus `state_v_first` raises | Deprecated alias and new kwarg passed together | Inspect kwargs from higher-level caller | Pass exactly one layout flag; prefer `state_v_first`. Preserve the explicit rejection. |
| KDA `safe_gate` raises | `safe_gate=True` without valid lower bound | Check `use_gate_in_kernel`, `safe_gate`, and `lower_bound` | With in-kernel gate, set `lower_bound` in `[-5, 0)` or disable safe gate. |
| KDA `allow_neg_eigval` raises | Flag used without raw beta sigmoid path | Check `use_beta_sigmoid_in_kernel` | Enable `use_beta_sigmoid_in_kernel=True` when `allow_neg_eigval=True`, or pass post-sigmoid beta without negative eigenvalue scaling. |
| `return_intermediate_states` fails or returns unexpected arity | KDA intermediate-state path is inference-only and returns a 3-tuple | Check `torch.inference_mode()` and unpacking site | Use inference mode and unpack `(o, final_state, h)`, or leave the flag false for training/autograd. |
| Backend never appears to run | Env gate off, package unavailable, verifier rejected, registry not initialized, or dispatch disabled | Inspect env vars, package availability, and verifier result; run the safe ops inspection script for public export visibility | Add a route assertion or spy in tests. Do not infer backend execution from numerical parity alone. |
| Default path needed for comparison | Optional backend intercepts public call | Check `FLA_DISABLE_BACKEND_DISPATCH` | Start a new Python process with `FLA_DISABLE_BACKEND_DISPATCH=1` to force the semantic fallback. |
| FlashKDA route rejected | FlashKDA verifier is intentionally narrow | Check inference mode, dtype bf16, `K=128`, `V=128`, `HV==H`, in-kernel q/k norm, gate, beta sigmoid, `safe_gate`, and `state_v_first=True` | Use default Triton for training, non-bf16, non-128 dims, GVA, context parallel, or intermediate-state cases. |
| TileLang route rejected or unavailable | Missing `tilelang`, unusable CUDA compiler probe, unsupported dtype/GVA/state dtype, or env disabled | Check `FLA_TILELANG`, package visibility, compiler probe, and verifier reason | Fix the optional backend prerequisites or allow fallback. Do not import optional packages at module load if absence should be supported. |
| Intra-card CP route not active | Backend opt-in off, not inference mode, or no varlen input | Check `FLA_INTRACARD_CP`, `torch.inference_mode()`, and `cu_seqlens` | Enable intentionally for inference varlen paths only; keep default disabled unless requested. |
| Triton compile error mentions block pointers in mainline code | New code used deprecated block-pointer helpers | Search the changed kernel diff for `tl.make_block_ptr` and `tl.advance` | Replace with explicit offset-vector pointer arithmetic and masks. The documented exception is triton-ascend backend code. |
| Triton compile/runtime overflow or illegal memory access on large shapes | Program IDs, strides, or offsets kept in narrow integer types | Inspect program-id casts and address arithmetic | Cast grid-derived values and all address math to `tl.int64` before multiplication or pointer offsets. |
| NaNs only under the native operator test suite | Uninitialized output/scratch memory exposed by NaN poisoning | Check masked stores, tail tiles, and scratch buffers saved for backward | Fully initialize every observable output and gradient path; add ragged shape coverage that hits tail masks. |
| Autocast result dtype or contiguity changed | Lost `input_guard` or paired autocast wrapper | Inspect public/autograd decorators and any skipped parameters | Restore `input_guard` behavior and keep `autocast_custom_fwd` / `autocast_custom_bwd` paired for mixed-precision paths. |
| torch.compile captures backend selection | Dispatch logic or env checks moved into compiled work | Check decorated wrapper and backend implementation boundaries | Keep runtime dispatch selection under `torch.compiler.disable`; compile only the selected implementation body when appropriate. |
| A layer/model breaks after op refactor | Public signature or return tuple changed without callsite sweep | Search all callsites for the public op and any private helper whose signature changed | Update every callsite, state unpack, and test in one pass; do not patch only the failing stack frame. |

## Dispatch debugging sequence

1. Decide whether you are testing the default fallback or an optional backend.
2. For fallback, start Python with `FLA_DISABLE_BACKEND_DISPATCH=1`.
3. For optional backend, set its env gate before Python starts and ensure the package/hardware probe can pass.
4. Inspect the backend verifier directly with tiny tensor-like objects when the verifier only needs shape, dtype, device flags, and option booleans.
5. If the public call returns numerically correct results but route is uncertain, add a spy around the registered backend method and assert it was called.
6. If a verifier rejects, keep the rejection reason precise; do not convert a verifier rejection into a hard error unless the public API cannot safely fall back.

## Kernel failure triage

- If a change touched masks, tiling, varlen offsets, or pointer math, prioritize ragged shapes and NaN-poisoned tests before benchmarks.
- If a change touched a shared helper, list every operation that calls that helper before running only one op's tests.
- If a change touched a backward kernel, confirm saved tensors, context fields, and backward return positions line up exactly with `forward` inputs.
- If a change touched a dtype path, check both forward output tolerance and gradient tolerance; dtype fixes often fail only in backward.
- If a change touched dispatch and kernels together, first prove fallback correctness with dispatch disabled, then prove backend routing and parity.

## Public API drift checklist

Before handing off an operator change:

- Root export still exposes the intended public name.
- Operation package export still exposes the intended public name.
- Public wrapper signature and defaults are stable unless a breaking change was explicitly approved.
- Deprecated kwargs still warn or reject exactly as intended.
- Return arity is stable for default mode; any optional three-tuple or attention tuple is covered by tests.
- Shape validation errors are precise and user-facing.
- Backend verifier signatures accept the same public call surface as decorated functions.
- Layer/module/model callsites that construct q/k/v/g/beta or state tensors still satisfy the operator contract.
- No new `tl.make_block_ptr` or `tl.advance` appears in mainline Triton code.

## Using the bundled inspection helper

The helper is safe for import and signature checks only; it does not run kernels.

```bash
python scripts/inspect_fla_ops.py --smoke
python scripts/inspect_fla_ops.py --filter linear
python scripts/inspect_fla_ops.py --signature chunk_kda
```

If the helper cannot import `fla.ops`, treat that as environment/setup evidence, not an operator correctness result.
