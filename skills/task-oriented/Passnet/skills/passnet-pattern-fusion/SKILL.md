---
name: passnet-pattern-fusion
description: >
  Author PassNet pass files: write patterns that actually MATCH the FX graph, pick fusion
  regions (which ops to absorb into one Triton kernel), and structure multi-pass
  submissions with the mandatory shared-dispatch architecture. Use when creating or fixing
  pattern()/replacement_args()/replacement_func() files, when a pass "failed to match",
  or when deciding how to fuse multiple kernels/ops.
---

A pass file teaches the compiler: "this subgraph → my Triton kernel". Getting the PATTERN
right is binary (match or 0.1); getting the FUSION REGION right decides the speedup.
Kernel implementation details live in `references/kernel-templates.md`; numeric-fidelity
recipes in passnet-triton-opt.

## 1. Pass file contract

```python
import torch                      # 'import triton' etc. as needed
def pattern(a, b, ...):           # subgraph to match — torch IR, mirrors model.py
    ...
    return out                    # EXACTLY ONE returned value (tuple-of-1 ok)
def replacement_args(a, b, ...):  # pure arg shuffle, FX-traced — no math/.shape here!
    return (a, b, "route_name")   # constants (route strings/scalars) may be appended
def replacement_func():           # returns the SAME module-level function every call
    return dispatch_wrapper
```
Plus `pass_dir/sorted_output_pass_rule_names.json`: `["PassA", "PassB"]` — file stems,
priority order, every pass you want loaded MUST be listed.

## 2. The 10 hard rules (violating any ⇒ no match / crash / dropped pass)

1. **ONE output.** A pattern returning ≥2 values crashes the variant (harness asserts).
   If two intermediates are observable outside the region, write two passes that each end
   at one of them — never one pattern returning both.
2. **Mirror `model.py`'s exact call forms.** The target graph keeps the source form; your
   pattern is traced with normalization (see matchability table below). Same op spelled
   differently = no match (`torch.relu` ≠ `torch.nn.functional.relu`; `x.transpose(...)`
   (method) ≠ `torch.transpose(x, ...)`).
3. **Literals must be exactly equal**: eps `1e-05` ≠ `1e-04`, dims, shape lists, scale
   constants, `device(type='cuda')` objects in factory calls. Shape literals differing
   across variants ⇒ that node can't be in a shared pattern (write per-shape passes or
   exclude the node).
4. **Containment**: every node inside the pattern except the returned one must be consumed
   ONLY inside the pattern. If a producer feeds both your target consumer and any outside
   or returned value, do not hide that producer inside a larger pattern. End the region at
   the consumer/tail output or write separate one-output passes. If `model.py` returns an
   intermediate or feeds it to a node outside your region, end the region there (it becomes
   the pattern's single output) or exclude it. When an external producer has multiple
   observable consumers, prefer a one-output consumer-side floor pass or split regions
   over pulling that producer into a fused region.
   This is the single-output contract in practice: a producer whose value is externally
   visible or shared across a fanout cannot disappear inside your pass unless the one value
   returned by the pattern preserves every outside observation. Do not "simplify" by
   recomputing only the consumer you care about while hiding the shared producer; that makes
   the graph semantically incomplete or non-containment-safe.
5. **No `tmp = None`** statements, no prints, no asserts inside `pattern`. Pure alias
   lines in model.py (`tmp_0 = in_0`) create NO graph node either — skip them and use the
   original name's value flow.
6. **`replacement_args` is FX-traced**: only reorder/drop arguments and append literal
   constants. No arithmetic, no `.shape`, no conditionals on tensors.
7. **`replacement_func()` must be stable** (module-level function, `f() is f()`), and with
   2+ pass files ALL must return the SAME object via the shared-dispatch module (§4).
8. **No RNG ops** (`torch.rand*`, dropout `training=True`) inside patterns; eval-mode
   dropout (`training=False`) is identity and safe to absorb.
9. **AST restrictions** (file-wide): never import `torch.nn(/functional)`, `torch.ops`,
   `torch.autograd`, never alias them; in pattern bodies use full dotted
   `torch.nn.functional.xxx(...)`. Outside `pattern`/`replacement_args`, only the
   whitelisted `torch.empty/zeros/ones/full[_like]/as_tensor` calls.
10. **Wrapper-runtime restrictions** (poison dispatch during warmup): inside the kernel
    wrapper, only allocator ops + metadata (`.shape/.stride()/.numel()/.dim()/.device/
    .dtype/.data_ptr()`) + `.to()` + Triton launches. NO `.contiguous()`, no tensor math.

## 3. Matchability — what a pattern node can bind to

For a normal callable `def pattern(...)`, the pattern is traced with `ForceArgsTracer`; the
target (dynamo) graph is not. Per node:

| node kind in model.py | pattern is normalized? | matchable when... | pattern should write... |
|---|---|---|---|
| method call `x.view(...)`, `x.mean(dim=-2, keepdim=True)`, `x.to(dtype=...)`, `x.softmax(dim=-1)` | NO | always | mirror EXACTLY (incl. kwargs spelling) |
| C-bound function: `torch.conv2d`, `torch.matmul`, `torch.cat`, `torch.sigmoid`, `torch.arange`, `torch.sum`, `F.linear`, `F.gelu`, `operator.+ - * /` | NO (no inspect signature) | always | mirror EXACTLY (incl. kwargs spelling) |
| Python-def `F.*`: `relu`, `silu`, `softmax`, `dropout`, `layer_norm`, `batch_norm`, `embedding`, `interpolate`, `adaptive_avg_pool2d`, `pad`, `normalize`, `max_pool2d`... | YES → full positional, defaults filled | ONLY if model.py call is full-positional with ALL params spelled out | the same call (any style — it normalizes) |

Examples from real graphs:
- `torch.nn.functional.batch_norm(x, m, v, w, b, False, 0.1, 1e-05)` → matchable ✓
- `torch.nn.functional.dropout(x, 0.1, False, False)` → matchable ✓ (and it's identity!)
- `torch.nn.functional.relu(x, inplace = False)` → **kwargs on a Python-def op: NOT matchable** ✗
- `torch.nn.functional.softmax(x, 2, _stacklevel = 5)` → ✗ (and `_stacklevel` precedes
  `dtype` in the signature — normalization can't reproduce it)
- `x.softmax(dim=-1)`, `x.mean(dim = -2, keepdim = True)` → method form: matchable ✓
- `torch.cat([a, b], dim = 2)` → C-bound with kwargs: matchable (mirror the kwargs) ✓
- `torch.nn.functional.gelu(x)` / `F.gelu(x, approximate='none')` → C-bound: matchable ✓

Treat kwargs-form Python-level activations and functional calls as suspect boundaries
until `check_pattern.py` proves they match. For small or low-value regions, if they block
matching, start the region after that node or end just before it instead of spending
evaluations on near-miss patterns.

**Manual FX escape hatch for valuable kwargs regions.** The harness accepts `pattern` as a
`torch.fx.GraphModule`. In that case `_replace_pattern` uses `pattern.graph` directly and
does NOT run `ForceArgsTracer`, so exact kwargs-form Python functional nodes can match.
Use this only when a high-value single-output region is blocked by callable-pattern
normalization and a real pre-flight matcher confirms the manual graph matches.

Build the graph inside a function literally named `pattern` (that function body is
AST-exempt), then replace `pattern` with the returned `GraphModule` and set
`__signature__` to the placeholders in order:

```python
import inspect
import operator
import torch

def pattern():
    graph = torch.fx.Graph()
    x = graph.placeholder("x")
    y = graph.placeholder("y")
    act = graph.call_function(
        torch.nn.functional.relu, args=(x,), kwargs={"inplace": True}
    )
    out = graph.call_function(operator.add, args=(act, y), kwargs={})
    graph.output(out)
    gm = torch.fx.GraphModule({}, graph, "ExactKwargPattern")
    gm.__signature__ = inspect.Signature([
        inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        inspect.Parameter("y", inspect.Parameter.POSITIONAL_OR_KEYWORD),
    ])
    return gm

pattern = pattern()
```

The manual graph must still obey every other rule: one output, containment, exact targets
and literals, matching `replacement_args` parameters, and Triton-only runtime computation.
Do not use it as a speculative default; it is a repair for proven callable-pattern
normalization misses.

Manual FX does not make side effects free. Treat `inplace=True` functional calls as
side-effectful even when the graph matches: only absorb them if the replacement mutates the
input exactly as eager would under repeated benchmark calls. If that is awkward or uncertain,
leave the in-place node in eager and fuse the downstream side-effect-free region.

Do NOT trust memory on which ops are C-bound — VERIFY with the pre-flight checker
(`passnet-feedback/scripts/check_pattern.py`) before every GPU eval; it traces your
pattern, runs the real `SubgraphMatcher` against the real dynamo graph of every variant,
and prints near-miss diffs when a pattern doesn't match.

## 4. Multi-pass architecture (mandatory for ≥2 pass files)

`output_pass_replacement_func_limit: 1` keeps only ONE distinct replacement function —
passes returning a different object are SILENTLY dropped (watch `Loaded N passes` in the
log). Structure:

`pass_dir/_shared_kernels.py` (helper module, NOT listed in the json):
```python
import torch
import triton
import triton.language as tl

@triton.jit
def _fused_a_kernel(...): ...
@triton.jit
def _fused_b_kernel(...): ...

def _run_a(x, w):
    out = torch.empty_like(x)
    ...launch _fused_a_kernel...
    return out

def _run_b(x):
    ...
    return out

@torch.fx.wrap
def dispatch_wrapper(*args):
    route = args[-1]
    if route == "fuse_a":
        return _run_a(args[0], args[1])
    if route == "fuse_b":
        return _run_b(args[0])
    raise ValueError(f"unknown route {route}")
```

each `pass_dir/FuseA.py`:
```python
import torch
from pass_dir._shared_kernels import dispatch_wrapper

def pattern(x, w):
    ...
    return out

def replacement_args(x, w):
    return (x, w, "fuse_a")

def replacement_func():
    return dispatch_wrapper
```

- Works because the sample root is on `sys.path` while passes load; the shared module is
  imported once → one function object → nothing is dropped.
- Keep `_shared_kernels.py` AST-clean too (Triton + whitelisted allocators only).
- A single-pass submission may simply define its wrapper in the pass file — but starting
  with the shared layout costs nothing and survives growth.
- Order in the json = application order. Earlier passes consume nodes; a later pattern
  overlapping an earlier match will no longer find its nodes. Order independent patterns
  freely; order overlapping ones from largest to smallest region.

## 5. Choosing fusion regions

1. From the analyzer output, mark every node matchable/unmatchable for a normal callable
   pattern, and separately mark high-value kwargs-form Python functional nodes that may be
   recoverable with a manual FX `GraphModule` pattern.
2. Greedily grow regions over callable-matchable nodes along dataflow; STOP at: an
   unrecovered unmatchable node, RNG, a node whose output is consumed outside the region
   (unless you end the region exactly there), a conv/big-matmul you've decided to keep in aten.
   **Keeping a heavy conv/matmul in aten and fusing its tail is the DEFAULT and usually right.**
   The clearest case where the conv itself becomes the region ANCHOR instead of a wall: a
   **non-overlapping conv** — `stride == kernel_size`, `kernel_size > 1`, `padding == 0` — which
   is exactly a dense patch matmul (§ kernel-templates §13). Anchoring on a 1×1 conv (already a
   cuBLAS-optimal pointwise GEMM), a depthwise/grouped conv, or a general matmul usually loses —
   default to fusing their tails and leaving the op in aten (let a completed eval overrule this
   if parameters look off-regime). Either way the op is C-bound and matches when you mirror its
   exact positional call form; never treat "it's a big cuDNN op" as "unmatchable."
   If the only blocker is callable-pattern normalization of kwargs-form Python functional
   calls and the wider region has real upside, try a manual FX pattern and require
   `check_pattern.py` proof before evaluation.
   For fanout, draw the boundary at the first value that has multiple external consumers.
   If each consumer is independently valuable, write separate one-output passes using the
   shared-dispatch architecture; if the consumers are only cheap layout/view work, treat
   them as floor/downside-cap candidates rather than performance targets.
   When a shared or returned producer feeds a substantial downstream consumer, consider a
   consumer-side region that leaves that producer outside the pattern and treats it as an
   input. Do not reject the whole sample for global fanout if a local backward slice from the
   chosen output still has exactly one output and absorbs enough compute to amortize a
   launch.
   Prefer a single-output region that absorbs several elementwise, affine, activation,
   residual, or normalization consumers fed by the same broadcast/layout producer when
   containment is legal. Repeated round evidence shows this family is more likely to pay the
   fixed launch/wrapper cost than isolated reductions or tiny tails.
   For concat-to-normalization-affine prefixes, containment can still be legal even when a
   downstream activation is unmatchable or in-place: return the normalized or affine prefix
   tensor as the one crossing value and leave the boundary consumer in eager. Do not pull an
   in-place activation into the pattern just to make the region look complete.
   When repeated duplicate compute exists, anchor the replacement on values with real users.
   Userless/dead duplicate nodes can structurally match but fail replacement because the
   matched return has no observable consumer. If the profitable opportunity is dead-work
   elimination, treat it as a graph-rewrite edge case and prove it with the real matcher and
   smoke test before spending an evaluation.
3. Each region ⇒ one pass ⇒ ideally ONE Triton kernel launch. Two kernels for one region
   only when a reduction's result feeds elementwise work over a DIFFERENT axis size
   (e.g. softmax over rows then matmul) — usually better: split into two passes.
4. Region inputs = tensors crossing into it (pattern parameters); region output = the one
   tensor crossing out.
5. Sanity: replacing N aten ops saves roughly Σ(their eager µs); your kernel costs
   ~19 µs launch + memory traffic. If the sum is < ~50 µs the region only makes sense as
   the floor pass / part of something bigger.
6. Layout ops at region EDGES are usually better left outside (they're ~free in eager).
   Layout ops INSIDE a region (between two compute ops) are absorbed for free via index
   arithmetic. Special case worth taking even "alone": `view/unsqueeze/expand → binary op`
   chains that WRITE a large output — aten's broadcast-elementwise kernels are often
   1.5–2.5× off the bandwidth roofline, so a shape-specialized Triton kernel wins well
   beyond the erased python overhead (measured 2.3× on a 67M-element broadcast-sub).
   Don't guess: `analyze_graph.py --bench` gives each node's real eager µs; estimate your
   kernel as `bytes_moved / 1.4 TB/s` and compare.
   Do not force eager metadata-only layout/view/reshape work to materialize just to make a
   larger pattern. If the pattern output is a returned or externally observed view that eager
   can keep cheap, materializing it in a wrapper may erase the benefit of absorbing nearby
   elementwise work; treat that as a downside cap unless a completed eval proves otherwise.

## 6. Kernel wrapper conventions (poison-proof)

```python
def _run_fused(x, w, b):
    B, N = x.shape                       # metadata: allowed
    out = torch.empty((B, N), dtype=x.dtype, device=x.device)
    grid = (triton.cdiv(B * N, 1024),)
    _kernel[grid](x, w, b, out, B * N, N,
                  x.stride(0), x.stride(1),   # pass strides — NEVER .contiguous()
                  BLOCK=1024)
    return out
```
- Output dtype MUST equal what eager produces (usually the input dtype; watch explicit
  `.to(torch.float32)` nodes in the region).
- If the pattern output is consumed by `.view(...)` outside the region, your output's
  contiguity must allow that view — return a fresh contiguous tensor of the eager
  output's shape (the normal case).
- Handle every variant's shapes/dtypes with ONE wrapper: derive sizes from `.shape`,
  never hardcode, unless the pattern itself is shape-literal-specific.
- Scalars you need (eps, slopes, dims) that appear as pattern literals: hardcode them in
  the kernel for that pass (they're fixed by the match) or pass via `replacement_args`
  constants.

See `references/kernel-templates.md` for ready-to-adapt Triton templates: elementwise
chain (stride-aware), row reduction (softmax/layer_norm/mean/L2-norm), BN-inference
affine, bias+activation epilogue, cat+elementwise, embedding gather, matmul+epilogue
(`tl.dot`), 2-pass split reductions.

## 7. Debug: "Pass X failed to match"

1. Run `check_pattern.py` — it prints the dynamo node list vs your traced pattern nodes.
2. Compare node-by-node: op kind (`call_function` vs `call_method`), target identity,
   arg/kwarg shapes of the WRITTEN forms, literals.
3. Most frequent causes, in order: kwargs-form Python-def F.* op included in a normal
   callable pattern (drop the node for a cheap region, or switch to an exact manual FX
   pattern for a valuable one); literal mismatch across variants; intermediate consumed
   outside (containment); userless/dead nodes selected as the match output; wrong
   method-vs-function form; `_stacklevel`-style hidden kwargs; pattern includes a
   `tmp = None`-induced phantom; two returned values. If a producer has outside consumers,
   exclude that producer or split at the consumer output before retrying.
4. `[PassMgrBackend] Diagnostic ... best-attempt` lines in eval logs name the first
   mismatching node pair — read them.

## 8. Round-planning containment checklist

Before handing a region to kernel tuning, answer these with the real graph in mind:

- Does the proposed pattern return exactly one value?
- Are all nodes hidden inside the pattern consumed only inside the pattern, except that
  single returned value?
- Does any producer inside the region feed another returned value, an outside consumer, or
  a later observable fanout branch? If yes, exclude it or split into one-output passes.
- Is the region mainly layout/view/reshape/split fanout work? If yes, mark it as a
  downside-cap/floor candidate unless it bridges compute or avoids a real materialization.
- Does the proposed region force a returned view or metadata-only layout value to become an
  allocated output? If yes, prefer a consumer-side elementwise/affine region or a narrow
  floor, and require completed-evaluation proof before keeping the wider materializing pass.
- If multiple passes are needed, do they all return the same shared dispatch wrapper?

Tentative guidance from repeated round behavior: when a larger-looking region is blocked
only by the single-output/external-fanout contract, it is usually better to stop with the
best correct floor than to add tiny independent kernels that increase launch overhead.
