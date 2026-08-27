# Testing and correctness for operator work

Use this reference when adding, changing, or reviewing an FLA operator path. The goal is a frozen correctness gate: the optimized implementation must match a trusted reference for both forward values and gradients, under shape coverage that exercises the modified code path.

## Required correctness contract

An operator change is incomplete until all relevant points below are satisfied:

- Compare optimized output against a naive, recurrent, or otherwise trusted reference implementation.
- Test both forward and backward for training-capable paths. A forward-only comparison is acceptable only for an inference-only backend or a path whose public contract explicitly forbids gradients.
- Use deterministic random inputs, normally `torch.manual_seed(42)`, so failures are reproducible.
- Use the package's `assert_close` helper where available, with an explicit tolerance and separate labels for `o`, state tensors, and every gradient.
- Exercise non-power-of-two sequence lengths or dimensions when the kernel uses tiling, masks, or chunking.
- Exercise stateful paths when the operator supports `initial_state` and `output_final_state`.
- Exercise variable-length flattening when the operator supports `cu_seqlens`.
- Include backend route tests for dispatch work: accepted route, verifier rejection, and fallback to the default path.
- Preserve NaN-poisoning safety: every floating output or scratch tensor that can reach output/gradient comparisons must be fully initialized.

Do not relax numerical tolerances, skip backward, or remove shape axes to make a regression pass. If the desired change alters numerics beyond the existing tolerance, treat it as a design decision rather than a routine fix.

## Self-contained forward/backward test pattern

Adapt this pattern to the target op and reference. It intentionally checks every gradient separately and resets `.grad` between implementations.

```python
import pytest
import torch

from fla.ops.gla import chunk_gla, fused_recurrent_gla
from fla.utils import assert_close, device


@pytest.mark.parametrize(
    ("B", "T", "H", "K", "V", "dtype"),
    [
        pytest.param(1, 63, 1, 64, 64, torch.float16, id="tiny-mask-fp16"),
        pytest.param(2, 257, 3, 60, 80, torch.float16, id="ragged-dims-fp16"),
    ],
)
def test_chunk_gla_forward_backward(B, T, H, K, V, dtype):
    torch.manual_seed(42)
    q = torch.randn(B, T, H, K, dtype=dtype, device=device).requires_grad_()
    k = torch.randn(B, T, H, K, dtype=dtype, device=device).requires_grad_()
    v = torch.randn(B, T, H, V, dtype=dtype, device=device).requires_grad_()
    g = torch.randn(B, T, H, K, dtype=dtype, device=device).logsigmoid().requires_grad_()
    h0 = torch.randn(B, H, K, V, dtype=torch.float32, device=device).requires_grad_()
    do = torch.randn(B, T, H, V, dtype=dtype, device=device)
    dht = torch.randn(B, H, K, V, dtype=torch.float32, device=device)

    ref, ref_ht = fused_recurrent_gla(
        q=q.clone(), k=k.clone(), v=v.clone(), gk=g.clone(),
        initial_state=h0.clone(), output_final_state=True,
    )
    ((ref * do).sum() + (ref_ht * dht).sum()).backward()
    ref_grads = [x.grad.clone() for x in (q, k, v, g, h0)]
    for x in (q, k, v, g, h0):
        x.grad = None

    tri, tri_ht = chunk_gla(
        q=q.clone(), k=k.clone(), v=v.clone(), g=g.clone(),
        initial_state=h0.clone(), output_final_state=True,
    )
    ((tri * do).sum() + (tri_ht * dht).sum()).backward()
    tri_grads = [x.grad.clone() for x in (q, k, v, g, h0)]

    assert_close("o", ref, tri, 0.005)
    assert_close("ht", ref_ht, tri_ht, 0.005)
    for name, ref_grad, tri_grad in zip(("dq", "dk", "dv", "dg", "dh0"), ref_grads, tri_grads, strict=True):
        assert_close(name, ref_grad, tri_grad, 0.005)
```

When adapting the template, make the reference operate in the precision expected by the existing tests. For example, some chunk paths compare against a recurrent path fed with float32-converted q/k/v, while the optimized path accepts fp16/bf16 tensors.

## Coverage axes

Use the smallest set of cases that exercises the changed code path, but make the axes explicit.

| Axis | Cases to consider |
| --- | --- |
| Sequence layout | dense; flattened varlen with `cu_seqlens`; `cu_seqlens_cpu` when the op uses host lengths |
| Direction | forward; backward; state-gradient path when `initial_state` or `output_final_state` participates in loss |
| Entry point | `chunk_*`; `fused_recurrent_*`; `fused_chunk_*`; `parallel_*`; backend-specific implementation when dispatch is involved |
| State | no state; `initial_state`; `output_final_state`; `state_v_first`; deprecated layout alias when supported |
| Shape tails | non-power-of-two `T`; non-round `K` or `V`; tile-boundary cases; tiny sequence; long sequence |
| Values and dtypes | fp32 reference; fp16/bf16 optimized paths; log-space gate; raw gate when fused; raw beta logits vs post-sigmoid beta |
| Varlen state | `B=1` flattened inputs; `len(cu_seqlens)-1` states; uneven sequence lengths; final state per original sequence |
| GVA / head groups | `HV == H`; `HV > H`; reject or skip cases where `HV % H != 0` |
| KDA flags | q/k L2 norm in kernel; gate in kernel; beta sigmoid in kernel; `allow_neg_eigval`; safe gate lower bound; recompute on/off |
| Dispatch | backend accepted; verifier rejected with reason; master dispatch disabled; optional package absent; backend-specific env disabled |
| Platform | default accelerator; explicit skips for unsupported Intel/Ascend/NVIDIA/AMD paths; no direct hardware probes in tests when utility helpers exist |

## NaN memory poisoning expectations

The native FLA operator/module tests use a fixture that replaces floating `torch.empty`, `torch.empty_like`, and `Tensor.new_empty` allocations made from FLA code with NaN-filled tensors. This catches kernels that rely on uninitialized memory or forget a masked store.

Consequences for operator maintenance:

- Masked stores must cover every output lane that can be observed.
- Masked loads need safe `other=` values when masked lanes enter arithmetic.
- Scratch buffers returned to Python or saved for backward must be fully initialized.
- A test that passes without NaN poisoning can still be wrong if the kernel leaves tail tiles undefined.
- For new custom test harnesses outside the native fixture, deliberately include ragged shapes and inspect for `torch.isnan` in outputs and gradients.

## Dispatch route tests

Numerical equivalence alone cannot prove that an optional backend ran. A backend test should also prove route selection.

Route-test checklist:

1. Enable or disable the backend through its env var before the relevant import, or use a scoped monkeypatch pattern that resets any cached probe.
2. Ensure the backend package or platform probe is represented honestly: importable package, mocked availability, or explicit skip.
3. Spy on a backend implementation method or registry entry when practical, then call the public decorated function.
4. Assert that the expected backend method was called for an accepted shape.
5. Assert that an unsupported shape or flag is rejected by the verifier and falls back to the default implementation.
6. Add a master-dispatch-off comparison when isolating default Triton behavior: `FLA_DISABLE_BACKEND_DISPATCH=1` should leave the public API usable.
7. Keep verifier tests cheap by using simple tensor-like objects when only dtype, shape, and flags are checked.

Verifier tests should assert both the boolean result and the rejection reason. Rejection strings are user-facing troubleshooting data.

## Public API and callsite audit

When an operator signature, return tuple, state layout, or helper kernel signature changes, audit all affected surfaces in one pass:

- Root public export and operation package export.
- Public wrapper signature, docstring facts, default values, deprecated kwargs, and validation errors.
- Autograd `Function.forward` arguments, saved tensors, context fields, and return tuple.
- Autograd `backward` argument order and number of returned gradients.
- Private forward/backward helper signatures and kernel launch argument order.
- Backend implementation method signatures and verifier signatures for decorated functions.
- Dispatch registry name and backend package name.
- Layer/module/model callsites that call the public op.
- Correctness tests, route tests, and benchmark registry entries if the entry point name changes.
- Any state layout transformation, especially `state_v_first` vs default `[K, V]` state.

Keyword argument order matters for many kernel launches and wrapper calls. Do not update one callsite at a time.

## New operator checklist

A new operator under `fla.ops` should include:

1. Operation package with an `__init__` that exports the public API.
2. A pure PyTorch naive/reference implementation when the math is new.
3. Optimized kernels in the mode file that matches the public API (`chunk`, `parallel`, `fused_recurrent`, or `fused_chunk`).
4. Reuse of shared kernels where possible.
5. Correctness tests that compare optimized vs reference for forward and gradients.
6. Dispatch backend tests if optional backends are introduced.
7. Public documentation facts in the wrapper docstring without over-promising unsupported shapes or dtypes.

## No-go patterns

- Forward-only checks for a training path.
- Comparing two optimized paths with the same bug instead of comparing against a trusted reference.
- Using CPU import or `inspect.signature` success as proof of GPU kernel correctness.
- Hiding an unsupported shape behind a broad skip instead of a precise verifier or shape validation.
- Deleting a state/layout test because a new implementation does not support the old path.
- Relaxing tolerance or enabling `FLA_CI_ENV` to make a regression disappear.
- Updating a shared helper without sweeping every op that calls it.
