# Triton kernel templates for PassNet passes

Adapt, don't copy blindly: derive sizes from tensor metadata, keep dtype-generic
(`compute fp32, store out dtype`), pass strides for any input that may be non-contiguous
(anything produced by `permute/transpose/expand/slice` upstream — check the graph).
All templates are poison-dispatch-safe (allocators + metadata only).

## 0. Conventions

```python
import torch
import triton
import triton.language as tl
```
- Load pattern: `x = tl.load(ptr + offs, mask=mask, other=0.0).to(tl.float32)`
- Store pattern: `tl.store(out_ptr + offs, y.to(out_ptr.dtype.element_ty), mask=mask)`
- Grid: `grid = (triton.cdiv(n, BLOCK),)`; BLOCK 1024 default for elementwise;
  `num_warps=4` default, 8 for BLOCK ≥ 2048.
- For 2D row kernels: one program per row (or per row-block), columns swept by
  `tl.arange(0, BLOCK_N)` with `BLOCK_N = triton.next_power_of_2(N)` when N ≤ 16384.

## 1. Fused elementwise chain (flat, contiguous)

For regions like `bn-eval → add → sigmoid → mul` (any per-element math over same-shape
tensors).

```python
@triton.jit
def _ew_chain(x_ptr, y_ptr, out_ptr, n, BLOCK: tl.constexpr):
    pid = tl.program_id(0)
    offs = pid * BLOCK + tl.arange(0, BLOCK)
    m = offs < n
    x = tl.load(x_ptr + offs, mask=m, other=0.0).to(tl.float32)
    y = tl.load(y_ptr + offs, mask=m, other=0.0).to(tl.float32)
    r = x * (1.0 / (1.0 + tl.exp(-y)))          # example: x * sigmoid(y)
    tl.store(out_ptr + offs, r.to(out_ptr.dtype.element_ty), mask=m)

def _run(x, y):
    out = torch.empty_like(x)
    n = x.numel()
    _ew_chain[(triton.cdiv(n, 1024),)](x, y, out, n, BLOCK=1024)
    return out
```

Broadcast variants: a `[C]` tensor broadcast over `[N, C]` rows → index it with
`offs % C`; a `[N, 1]` column broadcast → `offs // C`. For NCHW per-channel params
(`[C]` over `[N, C, H, W]`): channel = `(offs // (H * W)) % C` — pass `HW = H*W` and `C`.

## 2. Stride-aware elementwise (non-contiguous input / absorbing `.contiguous()`)

When an input comes from `permute/transpose/expand` (stride may be 0!) or you absorb a
`contiguous()` node: compute multi-dim indices from the flat output offset, then address
input by ITS strides.

```python
@triton.jit
def _ew_strided(x_ptr, out_ptr, n, D0, D1, D2,          # logical out shape
                sx0, sx1, sx2,                           # input strides (elements)
                BLOCK: tl.constexpr):
    pid = tl.program_id(0)
    offs = pid * BLOCK + tl.arange(0, BLOCK)
    m = offs < n
    i2 = offs % D2
    i1 = (offs // D2) % D1
    i0 = offs // (D1 * D2)
    x = tl.load(x_ptr + i0 * sx0 + i1 * sx1 + i2 * sx2, mask=m, other=0.0).to(tl.float32)
    tl.store(out_ptr + offs, x.to(out_ptr.dtype.element_ty), mask=m)
```
Wrapper passes `x.stride(0), x.stride(1), x.stride(2)`. This is also THE template for
materializing any layout chain (`permute+contiguous`, `expand`, simple `cat` reads).

## 3. BatchNorm-inference affine (matches `F.batch_norm(x, m, v, w, b, False, mom, eps)`)

```python
@triton.jit
def _bn_eval(x_ptr, mean_ptr, var_ptr, w_ptr, b_ptr, out_ptr, n, C, HW,
             EPS: tl.constexpr, BLOCK: tl.constexpr):
    pid = tl.program_id(0)
    offs = pid * BLOCK + tl.arange(0, BLOCK)
    m = offs < n
    c = (offs // HW) % C                 # NCHW; for [N, C] tensors pass HW=1 → offs % C
    x = tl.load(x_ptr + offs, mask=m, other=0.0).to(tl.float32)
    mu = tl.load(mean_ptr + c, mask=m, other=0.0).to(tl.float32)
    var = tl.load(var_ptr + c, mask=m, other=1.0).to(tl.float32)
    w = tl.load(w_ptr + c, mask=m, other=1.0).to(tl.float32)
    b = tl.load(b_ptr + c, mask=m, other=0.0).to(tl.float32)
    y = (x - mu) * (1.0 / tl.sqrt(var + EPS)) * w + b
    tl.store(out_ptr + offs, y.to(out_ptr.dtype.element_ty), mask=m)
```
Fuse adjacent matchable activations/residual-adds into `y` before the store.

## 4. Row reduction — softmax (matches method-form `x.softmax(dim=-1)`)

Eager softmax subtracts the row max — replicate EXACTLY for fp32-baseline correctness.

```python
@triton.jit
def _softmax_rows(x_ptr, out_ptr, R, N, sx_r, BLOCK_N: tl.constexpr):
    row = tl.program_id(0)
    cols = tl.arange(0, BLOCK_N)
    m = cols < N
    x = tl.load(x_ptr + row * sx_r + cols, mask=m, other=float("-inf")).to(tl.float32)
    x = x - tl.max(x, axis=0)
    e = tl.exp(x)
    y = e / tl.sum(e, axis=0)
    tl.store(out_ptr + row * N + cols, y.to(out_ptr.dtype.element_ty), mask=m)

def _run_softmax(x):
    shp = x.shape
    N = shp[-1]
    R = x.numel() // N
    out = torch.empty_like(x)
    _softmax_rows[(R,)](x, out, R, N, x.stride(-2) if x.dim() > 1 else 0,
                        BLOCK_N=triton.next_power_of_2(N), num_warps=8 if N > 1024 else 4)
    return out
```
`softmax(dim=k)` for non-last dims: either pass strides and sweep that axis, or only
absorb last-dim softmax (the common case). Fuse a preceding scale (`q @ k / sqrt(d)`'s
div) or additive mask into the load expression when those nodes are in the region.

## 5. Row reduction — LayerNorm (matches positional `F.layer_norm(x, (N,), w, b, eps)`)

Eager computes mean and rstd in fp32: `y = (x - mean) * rsqrt(var + eps) * w + b`, var is
the BIASED variance (divide by N).

```python
@triton.jit
def _layer_norm(x_ptr, w_ptr, b_ptr, out_ptr, N, EPS: tl.constexpr, BLOCK_N: tl.constexpr):
    row = tl.program_id(0)
    cols = tl.arange(0, BLOCK_N)
    m = cols < N
    x = tl.load(x_ptr + row * N + cols, mask=m, other=0.0).to(tl.float32)
    mean = tl.sum(x, axis=0) / N
    d = tl.where(m, x - mean, 0.0)
    var = tl.sum(d * d, axis=0) / N
    rstd = 1.0 / tl.sqrt(var + EPS)
    w = tl.load(w_ptr + cols, mask=m, other=1.0).to(tl.float32)
    b = tl.load(b_ptr + cols, mask=m, other=0.0).to(tl.float32)
    y = (x - mean) * rstd * w + b
    tl.store(out_ptr + row * N + cols, y.to(out_ptr.dtype.element_ty), mask=m)
```
Same skeleton handles RMSNorm chains (`pow(2).mean → rsqrt → mul → mul w`), L2-normalize
(`x / x.norm(p=2, dim=-1, keepdim=True)` — method-form `.norm` matches), and
`mean(dim=-1)`/`sum(dim=-1)` if the reduced value is the region output.

## 6. Mean over trailing spatial dims (matches `x.mean((2, 3), keepdim=True)` /
`F.adaptive_avg_pool2d(x, 1)`)

```python
@triton.jit
def _mean_hw(x_ptr, out_ptr, HW, BLOCK: tl.constexpr):
    nc = tl.program_id(0)                       # one program per (n, c)
    offs = tl.arange(0, BLOCK)
    acc = tl.zeros((BLOCK,), dtype=tl.float32)
    for start in range(0, HW, BLOCK):
        idx = start + offs
        acc += tl.load(x_ptr + nc * HW + idx, mask=idx < HW, other=0.0).to(tl.float32)
    tl.store(out_ptr + nc, (tl.sum(acc, axis=0) / HW).to(out_ptr.dtype.element_ty))
```
Typical SE-block region `mean → linear/conv1x1 → act → sigmoid → mul` can be split:
mean kernel (this) + elementwise tail kernel, two passes.

## 7. Bias + activation epilogue (after a kept-in-aten linear/conv)

Region = the ops AFTER `F.linear`/`torch.conv2d` (which stays in the graph): e.g.
`gelu(linear_out)` or `bn(conv_out) + relu-class`. Use template 1/3 with the activation:

- exact GELU (`F.gelu`, approximate='none'): `0.5 * x * (1 + tl.math.erf(x * 0.7071067811865476))`
- tanh GELU (approximate='tanh'): `0.5 * x * (1 + tl.math.tanh(0.7978845608028654 * (x + 0.044715 * x * x * x)))`
- SiLU: `x / (1 + tl.exp(-x))` ; Sigmoid: `1 / (1 + tl.exp(-x))`
- LeakyReLU(s): `tl.where(x >= 0, x, s * x)` ; ReLU: `tl.maximum(x, 0.0)`
- These match eager within 1–2 ulp in fp32 — verify with the checker's smoke test; if a
  strict fp32 variant fails, mirror eager more literally (e.g. use `tl.math.tanh`, keep
  operation order identical).

## 8. cat + elementwise (matches `torch.cat([a, b], dim) → ew-ops`)

One kernel writes the output in segments; each segment loads from its source with that
source's strides:

```python
@triton.jit
def _cat2_lastdim(a_ptr, b_ptr, out_ptr, R, NA, NB, BLOCK: tl.constexpr):
    pid = tl.program_id(0)
    N = NA + NB
    offs = pid * BLOCK + tl.arange(0, BLOCK)
    m = offs < R * N
    r = offs // N
    c = offs % N
    from_a = c < NA
    av = tl.load(a_ptr + r * NA + c, mask=m & from_a, other=0.0).to(tl.float32)
    bv = tl.load(b_ptr + r * NB + (c - NA), mask=m & (~from_a), other=0.0).to(tl.float32)
    v = tl.where(from_a, av, bv)
    # ... fused elementwise ops on v here ...
    tl.store(out_ptr + offs, v.to(out_ptr.dtype.element_ty), mask=m)
```
For cat over dim 1 of NCHW use segment offsets with H*W blocks. ≥3 inputs: extend the
`tl.where` chain, or group segments with the same indexing/work into a small number of
launches writing slices of `out`. Do not assume one branch-heavy giant kernel is always
best for heterogeneous branches; bench it against grouped launches. Avoid one launch per
tiny segment unless the output work clearly amortizes the extra launch overhead.

## 9. Embedding gather (matches positional `F.embedding(idx, weight, 0, None, 2.0, False, False)`)

```python
@triton.jit
def _embedding(idx_ptr, w_ptr, out_ptr, T, D, BLOCK_D: tl.constexpr):
    t = tl.program_id(0)
    cols = tl.arange(0, BLOCK_D)
    m = cols < D
    row = tl.load(idx_ptr + t)                  # int64 index
    v = tl.load(w_ptr + row * D + cols, mask=m, other=0.0)
    tl.store(out_ptr + t * D + cols, v, mask=m)
```

## 10. Matmul + epilogue (`tl.dot`) — use SPARINGLY

Only when the matmul is modest (K ≤ ~1024, M·N small enough that cuBLAS overhead matters)
or the epilogue chain is long; ALWAYS benchmark vs leaving matmul in aten.

```python
@triton.jit
def _mm_epilogue(a_ptr, b_ptr, c_ptr, M, N, K,
                 sam, sak, sbk, sbn,
                 BM: tl.constexpr, BN: tl.constexpr, BK: tl.constexpr):
    pm = tl.program_id(0)
    pn = tl.program_id(1)
    rm = pm * BM + tl.arange(0, BM)
    rn = pn * BN + tl.arange(0, BN)
    rk = tl.arange(0, BK)
    acc = tl.zeros((BM, BN), dtype=tl.float32)
    for k in range(0, K, BK):
        a = tl.load(a_ptr + rm[:, None] * sam + (k + rk)[None, :] * sak,
                    mask=(rm[:, None] < M) & ((k + rk)[None, :] < K), other=0.0)
        b = tl.load(b_ptr + (k + rk)[:, None] * sbk + rn[None, :] * sbn,
                    mask=((k + rk)[:, None] < K) & (rn[None, :] < N), other=0.0)
        acc = tl.dot(a, b, acc)
    # epilogue on acc here (bias add, activation, scale...)
    tl.store(c_ptr + rm[:, None] * N + rn[None, :],
             acc.to(c_ptr.dtype.element_ty),
             mask=(rm[:, None] < M) & (rn[None, :] < N))
```
Note: `F.linear(x, w, b)` = `x @ w.T + b` — pass `w` with transposed strides
(`sbk = w.stride(1)...` i.e. read W[k-th col]) instead of materializing a transpose.
fp16/bf16 accumulate in fp32 (as cuBLAS does) — that's what `acc` does. `tl.dot` needs
block dims ≥16 and (for older Triton) M/N/K blocks multiples of 16 — mask handles edges.

## 11. Two-kernel split for reduce→broadcast regions

`y = f(x, g(reduce(x)))` where the reduction axis is large: kernel 1 computes the per-row
statistic into a small temp (`torch.empty((R,), ...)`), kernel 2 does the elementwise
combine. Both launched from ONE wrapper (still one pass / one route).

## 12. In-wrapper scalar plumbing

Pattern literals (eps, scales, dims) are fixed per pass — bake them as `tl.constexpr`
defaults or pass as kernel args from the wrapper. NEVER recover them from tensors.
If a region needs the same kernel with different constants per pass, parameterize via the
route string: `"bn_eps1e-05"` → parse in dispatch (string ops are fine in the wrapper).

## 13. Reduced heavy ops — when a conv/matmul collapses to a cheaper primitive

The vendor library is near-optimal for the *generic* op, not for the *reduced* form its
parameters may imply. Recognize the reduction from parameters and target the reduced primitive:

- **Non-overlapping convolution** (`stride == kernel_size` per spatial dim, `kernel_size > 1`,
  `padding == 0`):
  windows are disjoint and reuse no input, so the conv is exactly a matmul of flattened
  patches by the flattened weight: for output position `p` and out-channel `co`,
  `out[p, co] = Σ_k patch[p, k] · W[co, k] + bias[co]`, where `k` ranges over
  `in_ch · Π(kernel dims)` and `p` over `Π(output spatial dims)`. Gather each patch by index
  arithmetic (NO `.contiguous()`), run `tl.dot`, add bias, then any fused tail
  (flatten/transpose are absorbed for free by how you index/store; a contained
  `cat`/`+pos`/`dropout(p=0)` tail can be folded into the epilogue). Skeleton (2-D windows;
  drop/extend a dim for 1-D/3-D):

```python
@triton.jit
def _patch_gemm(x_ptr, w_ptr, b_ptr, out_ptr,
                P, CO, K,                 # patches, out-channels, contraction = in_ch*kH*kW
                in_ch, H_in, W_in, kH, kW, H_out, W_out,
                BM: tl.constexpr, BN: tl.constexpr, BK: tl.constexpr):
    pm = tl.program_id(0); pn = tl.program_id(1)
    rm = pm * BM + tl.arange(0, BM)               # patch (output row) indices
    rn = pn * BN + tl.arange(0, BN)               # out-channel indices
    acc = tl.zeros((BM, BN), dtype=tl.float32)
    h_o = rm // W_out; w_o = rm % W_out           # decode patch -> output spatial coords
    base = (h_o * kH) * W_in + (w_o * kW)         # top-left of each patch (stride==kernel), NCHW contiguous x
    for k0 in range(0, K, BK):
        rk = k0 + tl.arange(0, BK); km = rk < K
        ic = rk // (kH * kW); r = rk % (kH * kW)
        kh = r // kW;         kw = r % kW
        feat = ic * (H_in * W_in) + kh * W_in + kw
        a = tl.load(x_ptr + base[:, None] + feat[None, :],
                    mask=(rm[:, None] < P) & km[None, :], other=0.0).to(tl.float32)
        # W flattened to [CO, K] is contiguous: W[co, k] = w_ptr + co*K + k
        b = tl.load(w_ptr + rn[None, :] * K + rk[:, None],
                    mask=km[:, None] & (rn[None, :] < CO), other=0.0).to(tl.float32)
        acc += tl.dot(a, b)
    acc += tl.load(b_ptr + rn, mask=rn < CO, other=0.0).to(tl.float32)[None, :]
    tl.store(out_ptr + rm[:, None] * CO + rn[None, :], acc.to(out_ptr.dtype.element_ty),
             mask=(rm[:, None] < P) & (rn[None, :] < CO))
```

Scope: this specific patch-gather template applies to the **non-overlapping** conv only
(`stride == kernel_size`, `kernel_size > 1`, `padding == 0`); its index math does not model a
**1×1 conv** (already a pointwise matmul cuBLAS handles optimally — default to fusing its tail)
or a **depthwise/grouped/overlapping** conv (default to fusing the tail). Those defaults are
priors; a completed eval can overrule them for an off-regime shape.

Correctness/perf notes (general):
- **`tl.dot(A, B)` computes `A @ B`, not `A @ Bᵀ`.** A conv weight is `[out_ch, in_ch, *kernel]`;
  its flattened form is `[CO, K]`, so index it as `W[co, k]` with the contraction axis `k` on
  the tile's row axis. A transpose slip here gives a large systematic `max_diff` on every
  variant — always numeric-smoke-test (check_pattern `--smoke`) before an eval.
- Accumulate in fp32 (`.to(tl.float32)` after load), store in the eager output dtype. On fp32
  inputs the library may use TF32 tensor cores, so `tl.dot` will differ slightly — it passes
  the fp32 *baseline* tolerance, not the strict bit-exact column; that is expected.
- Pick modest square-ish blocks (e.g. BM=BN=BK=64) as a default; `tl.dot` needs block dims
  ≥16 with masked edges. If the sample has many variants, do NOT autotune (compile-cost ×
  variants risks the timeout) — pick one fixed config.
- If a contained `cat(cls_token)` shifts output rows by one (seq = 1 + P), treat row 0 as the
  prepended token (load it, skip the GEMM) and map `patch = row - 1` for rows ≥ 1.
- Keep the conv's exact positional call form in `pattern` (it is C-bound: mirror stride/pad/
  dilation/groups positionally, per rule 2).
