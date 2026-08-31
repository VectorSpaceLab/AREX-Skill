---
name: passnet-triton-opt
description: >
  Make a single PassNet Triton kernel fast AND numerically faithful: performance model
  (when a replacement can win at all), block/grid/warp tuning, autotune policy, launch
  overhead, and per-op numeric recipes to pass the dtype baseline tolerances. Use when a
  pass matches and is correct but speedup below expected, or when correctness fails by small
  numeric margins.
---

## 1. Performance model — know if a win is even possible

Measured costs (A100, torch 2.7.1 / triton 3.3.1; same order of magnitude on the eval box):

| component | cost per call |
|---|---|
| dynamo guards + FX graph interpretation + dispatch wrapper | ~25–45 µs on a 3-op graph; grows with node count (~150–230 µs seen on a 13-node graph) — calibrate from your first eval |
| Triton kernel Python launch (`kernel[grid](...)`) | ~19 µs each |
| `torch.empty_like` / `torch.empty` | ~2–3 µs each |
| each aten op you REMOVED from the graph | +5–25 µs back (small ops) or its real kernel time |

So per variant: `compiled_e2e ≈ eager_e2e − Σ(absorbed aten µs) + tax + Σ(your kernels µs)`.
Rules of thumb:
- Whole eager forward < ~150 µs and you can absorb ≤2 cheap ops → ceiling < 1. Ship a
  safe correct pass, accept ~0.8–0.95, spend your time on another bottleneck.
- Small or narrow fusions can match and be numerically correct yet still lose e2e when
  launch/framework overhead exceeds the eager work removed.
- Layout-only, view/reshape-only, split/fanout, tiny activation, and small reduction-like
  kernels can also lose even when their local kernel is correct: eager may treat the work
  as metadata, use a vendor-tuned primitive, or pay less framework overhead than the
  compiled path. Treat these as floor/downside caps unless they bridge substantial compute
  or remove an actual materialization.
- The lever is **ops absorbed per launch** (and avoiding extra launches/allocs), not
  shaving 10% off an already-tiny kernel.
- Big tensors (≥ a few MB; kernel ≥ 100 µs): overhead noise vanishes; now memory traffic
  is everything — a clean fused kernel that reads each input once and writes once usually
  beats the multi-pass eager chain by the ratio of memory passes saved.
- **The biggest wins can be ALGORITHMIC, not tuning** — but the default for a heavy conv/matmul
  is still "leave it in the library, fuse its tail," because the library is near-optimal inside
  the regime it tuned for. The clearest case where a rewrite beats it: a **non-overlapping
  convolution** (`stride == kernel_size`, `kernel_size > 1`, `padding == 0`) is a dense patch
  matmul while cuDNN runs a heavier general im2col path — a `tl.dot` patch-gather kernel
  (kernel-templates §13) can win big. It usually does NOT pay to rewrite a **1×1 conv** (already
  a cuBLAS-optimal pointwise GEMM), an **overlapping conv** (im2col blows up memory), a
  **depthwise/grouped conv**, or a **general dense matmul** — those are vendor sweet spots.
  Treat this as a prior, not a ban: the completed eval decides. Pursue any rewrite only after a
  floor is banked, and don't dismiss the non-overlapping case as "cuDNN, unbeatable" without
  checking `stride == kernel_size`.
- For large cat/stack/gather-style outputs, one giant kernel is not automatically best if it
  needs heavy branching or irregular index logic. A small fixed number of simple kernels can
  be faster and more timing-stable when each launch writes a large contiguous region. Compare
  sequential micro-bench signals, then trust the completed evaluation.
- Repeated round evidence favors long memory-bound elementwise and broadcast-affine chains
  when one legal single-output kernel absorbs multiple affine, activation, residual, layout,
  or normalization consumers. These are the first places to spend tuning effort after a
  correct floor because saved memory passes can amortize wrapper and launch overhead.
- Repeated completed evaluations also favor normalization-affine compute prefixes and
  concat-to-normalization-affine prefixes when they remove large memory passes in one launch.
  Treat kernel layout choices for concat branches as workload-dependent: a broad prefix can
  win strongly, but small/branchy cases or attempts to absorb extra producers can regress in
  score, correctness, or timing stability. Keep the best completed floor/prefix state and
  revert completed regressions instead of stacking more small kernels or sweeping blindly.
- Reduction-only regions and vendor-tail replacements still need completed-evaluation proof.
  A correct reduction kernel, a small tail behind a vendor op, or a region that replaces a
  vendor-tuned primitive can remain below eager even when local kernel timing looks plausible.
  Use the completed eval to decide keep/revert; do not infer success from the triage family.
- Compare `[Speedup][gpu]` vs `[Speedup][e2e]` in the eval log: gpu≈e2e&both<1 → on-stream
  gaps/launches dominate (absorb more ops / fewer launches); gpu>1 but e2e<1 → host-side
  overhead (reduce launches, drop autotune key churn, simplify wrapper Python).
- Only a completed evaluation can prove the final overhead-bound conclusion. Local
  micro-bench and `check_pattern --bench` are pre-flight signals; if the completed eval is
  matched and correct but below eager for the maximal legal region, stop or revert instead
  of sweeping launch-bound tuning knobs.

## 2. Kernel quality checklist (in order of impact)

1. **One read per input element, one write per output element.** No multi-launch chains
   when one kernel can hold the chain in registers. Exception: for heterogeneous
   direct-output cat/stack branches, compare a branch-heavy single kernel with grouped
   launches; choose by measured stable e2e speed, not by launch count alone.
2. **Contiguous innermost access**: thread `offs` should walk the last (stride-1) dim.
   For strided/permuted inputs pass strides; never `.contiguous()` (poison-illegal) —
   absorbing the transpose INTO the index math is free.
3. **Block sizing**: elementwise → BLOCK 1024 (n ≥ 1M: 2048, num_warps=8). Row kernels →
   `BLOCK_N = next_power_of_2(N)`, and start with **num_warps=4** — more warps on small
   rows HURTS (measured: 512-elem rows, warps=8 was 1.8× slower than warps=4). If
   N > 16384 switch to a looped accumulation (template 6 in kernel-templates).
   For tiny rows (≤1024 elems), SWEEP rows-per-program ∈ {1, 2, 4, 8} (2D tile) — the
   winner is shape-dependent (measured 1.45× for ROWS=4 at D=512/131k rows, but ROWS=1
   best on a 768-wide LayerNorm); never assume, always micro-bench (§5).
4. **Grid**: prefer 1D `cdiv(n, BLOCK)`; for row kernels one program per row is fine up
   to ~256k rows. Avoid grids of 1–4 programs on big inputs (underutilization) — split.
5. **num_stages**: only matters for `tl.dot`/looped kernels (3–4); elementwise ignore.
6. **Avoid recompilation churn**: every distinct `tl.constexpr` value (incl. BLOCK chosen
   from shape) compiles a new binary during warmup. 2–3 specializations fine; per-shape
   formulas over 100-variant samples → timeout risk. Derive constexprs from a small fixed
   set (e.g. BLOCK_N = next_pow2 clamped to {128, 512, 1024, 4096}).
7. **Autotune policy**: `@triton.autotune` is legal and runs during the untimed warmup
   (poison-safe). Use ≤4–6 configs, `key=['N']`-style coarse keys. SKIP autotune when the
   sample has many graph variants (tuning cost × variants × 600 s timeout) or when the
   kernel is launch-bound anyway. A hand-picked config from one local micro-benchmark is
   usually within 5%.
8. **Scalar args beat tensor args**: precompute `n`, `C`, `HW`, strides in the wrapper
   (metadata access is poison-legal) — never load shape info from tensors in-kernel.
9. **Reduce wrapper Python**: no dict lookups in hot path beyond the route `if`; compute
   grid inline; allocate with `torch.empty` (not zeros — don't pay a memset you'll
   overwrite).

## 3. Numeric fidelity — passing t=-5 baseline tolerances

Baselines: fp32 rtol 1.3e-6/atol 1e-5 (tight — mirror eager's algorithm), fp16 rtol 1e-3,
bf16 rtol 1.6e-2 (loose). The same kernel must satisfy ALL dtype variants.

Recipes (these match aten's CUDA implementations):
- **Always compute in fp32** (`.to(tl.float32)` after load), store with
  `.to(out_ptr.dtype.element_ty)`. For fp16/bf16 inputs this reproduces aten (which also
  accumulates in fp32) to ≤1 ulp.
- Reductions: `tl.sum`/`tl.max` over a row in one block ≈ aten's order closely enough for
  fp32 rtol 1.3e-6 at typical sizes (N ≤ 16k). For looped accumulation keep ONE fp32
  accumulator (don't reorder into multiple partial schemes unnecessarily).
- softmax: subtract row max (aten does), exp, divide by sum. Don't use exp2 shortcuts on
  fp32 variants.
- layer_norm/batch_norm: biased variance (÷N), `1/sqrt(var+eps)` in fp32, then scale/shift.
- mean: `sum/N` (single division at the end, not running mean).
- GELU exact: `0.5x(1+erf(x/√2))` via `tl.math.erf`; tanh GELU only when model.py says
  `approximate='tanh'`.
- sigmoid/silu: `1/(1+exp(-x))` fp32 — fine at all baselines.
- `x.pow(2)` → `x*x`; `torch.rsqrt` → `1.0/tl.sqrt` (matches aten rsqrt within 1 ulp; if
  a strict fp32 variant complains, try `tl.math.rsqrt`).
- Integer/bool tensors: compare with `torch.equal` (atol/rtol=0 conceptually) — your
  kernel must be EXACT (indices, masks, argmax-style ops: replicate tie-breaking by
  first-occurrence).
- Output dtype must equal eager's per output ([Datatype] check), including intermediate
  `.to(torch.float32)` nodes you absorbed — store in the dtype eager would have at the
  region's output.

Diagnosing accuracy failures from eval logs: `[Correctness][max_diff]` magnitude vs the
table above (parse_eval_log.py does this) —
- max_diff ~1e-3·|values| on fp16 only → fp16 rounding mismatch: ensure fp32 internal math.
- fails ONLY fp32 variants → algorithmic mismatch (reduction order, formula) — mirror
  aten's exact sequence.
- max_diff huge (≥1) → indexing/masking bug, not numerics: check strides, `other=` values
  contaminating reductions (use `-inf` for max, `0` for sum, and mask BEFORE divide),
  uninitialized output regions (mask coverage), `offs` overflow on >2^31 elements
  (use `tl.int64` offsets when numel > 2e9).
- NaN/Inf only in compiled → division by masked-out zero lanes; `tl.where` the mask before
  the division, not after.

## 4. Launch-overhead reduction (when e2e-bound)

- Merge kernels (one launch per region; the whole point of fusion).
- Do not add a tiny independent kernel after a correct-but-slow state unless it absorbs
  enough real eager work to pay for another launch. If a completed eval shows the added
  region lowers score, revert to the best completed state and stop that line.
- Avoid per-call `next_power_of_2` recompute churn → precompute in wrapper; constexpr set
  small (see 2.6).
- Don't return tuples/lists from the wrapper unless the pattern output needs it.
- Buffer reuse across calls (cache `out` keyed by shape in a module dict) saves ~2 µs but
  risks aliasing bugs if the model returns your output AND mutates downstream — only as a
  last resort, verify with full eval.
- CUDA graphs / `torch.compile` of the wrapper / `no_dispatch` tricks: NOT allowed
  (torch.* calls blocked / hacking). Don't.

## 5. Micro-benchmark before full eval (GPU, seconds)

```python
import torch, time
def bench(fn, *args, iters=500):
    for _ in range(20): fn(*args)
    torch.cuda.synchronize(); t0 = time.perf_counter()
    for _ in range(iters): fn(*args)
    torch.cuda.synchronize(); return (time.perf_counter() - t0) / iters * 1e6  # µs
```
Compare: (a) eager region ops chained, (b) your wrapper. Build inputs with the shapes /
dtypes from weight_meta (use the checker's replay). Target: wrapper ≤ eager_region − 40 µs
for small graphs; for ms-scale kernels target the memory-traffic bound (bytes moved /
~1.5 TB/s on A100 ≈ achievable µs).

`check_pattern.py --bench` (passnet-feedback) automates exactly this comparison per
variant; trust the full eval for the final number (it adds guards/FX costs that local
micro-bench misses).
