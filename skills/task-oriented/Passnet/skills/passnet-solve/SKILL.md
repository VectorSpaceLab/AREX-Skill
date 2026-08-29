---
name: passnet-solve
description: >
  END-TO-END playbook for solving one PassNet sample: analyze the computation graphs,
  decide the optimization strategy (what to fuse, what to replace, what to leave alone),
  drive the iteration loop, and maximize the sample score. This is the ENTRY skill —
  invoke it first for any PassNet optimization task; it tells you when to use
  passnet-pattern-fusion, passnet-triton-opt and passnet-feedback.
---

You are optimizing one PassNet sample. A sample = several *graph variants* of the same
subgraph (different dtypes float32/float16/bfloat16 and input seeds/batch dirs). You write
compiler passes into `pass_dir/`; the evaluator pattern-matches them into each variant's FX
graph, checks correctness vs eager, and measures speedup.

## 0. How the score works (drives every decision)

Per graph variant, the *rectified speedup* is:

| outcome                                     | value            |
|---------------------------------------------|------------------|
| no pass matched, or crash/runtime error     | **0.1**          |
| matched but wrong numerics (baseline tol)   | **≈0.15** effective |
| matched + correct, e2e speedup `s`          | **≈ s** (even if s < 1) |

Sample score = geometric mean across ALL variants (then a tolerance-weighted aggregate that
≈ the geomean). Read `references/passbench-internals.md` for the exact math, the harness
mechanics, anti-cheat rules, and evaluation modes.

Consequences — internalize these:
1. **A matched, correct pass with speedup 0.8 scores 8× better than no match (0.1).**
   Never finish with an empty / non-matching `pass_dir`.
2. One crashing variant (0.1) drags the geomean of the whole sample hard. Consistency
   across ALL variants beats a hero kernel on one variant.
3. Speedup is **end-to-end wall clock** (Python overhead included), median of 100 trials,
   vs eager. The compiled path pays a fixed per-call tax (dynamo guards + FX
   interpretation + wrapper + Triton launch). **The tax scales with graph size and is
   machine-dependent: ~40–70 µs on a 3-op graph, ~150–230 µs measured on a 13-node graph.
   Calibrate it from your first eval** (`tax ≈ compiled_e2e − your_kernel_µs −
   remaining_eager_ops_µs`) and reuse it in ceiling estimates. You only win if the aten
   work you absorb into your kernel(s) exceeds the tax.
4. **A floor pass is downside insurance, not proof of upside.** Use it to avoid the 0.1
   cliff and calibrate tax. If a completed eval shows a floor or narrow pass is matched
   and correct but slower than eager, do not blindly tune the same small kernel. Either
   attempt a clearly larger legal region that should amortize the fixed tax, or record an
   overhead-bound stop when no such region exists.

## 1. Mandatory workflow

### Step 1 — Detect the environment mode (once, at start)

**Explicit task instructions override detection** — if your prompt says which mode to use
(or gives SVC/SAMPLE variables), use that mode; a service answering on the port may
belong to another tenant/GPU on a shared box.

```bash
curl -sS --max-time 5 http://127.0.0.1:${PASSNET_API_PORT:-8968}/health
```
- Response contains `"mode": "sample_access_service"` → **service mode**: all file I/O via
  HTTP with `?sample_path=$SAMPLE`; GPU eval via `POST /evaluate`. See
  `references/passbench-internals.md` §"Evaluation modes" for the exact curl recipes.
- Response is `{"status":"ok"...}` without that mode → **API-server mode** (same endpoints,
  no `sample_path` param).
- No response (or you were told to work locally) and you are in a sample directory (has
  `entry.sh`, `graph_list.txt`) → **local mode**: edit `pass_dir/` directly; evaluate with
  `bash entry.sh` (or `pass_evaluator` if available). Local mode always works from inside
  a sample dir regardless of what services are running.

In service mode, still author files in a local scratch dir first, run the pre-flight
checker on them, then POST them. The service is the source of truth: after upload, call
`/files` and confirm the expected JSON manifest and at least one pass file are visible
before `/evaluate`. Use bounded curl timeouts. In Codex managed sandboxes, try normal
localhost service `curl` first and continue normally if it succeeds. If it fails with
HTTP000, curl exit code 7, an empty body, or a connection-style error, retry once and
then use the approved escalation path if available. A sandboxed connection error does
not prove the service is down. Keep `curl` as its own command segment, capture response
bodies to files, and capture HTTP status separately so status text never corrupts a JSON
body.

### Step 2 — Read the problem

Get `graph_list.txt` and every variant's `model.py` + `weight_meta.py` (locally or via
`/problem`). Note for each variant: ops and their **exact textual call form**, tensor
shapes, dtypes. Variants usually share the op structure; shapes may differ — check, it
decides whether shape literals may appear in patterns.

### Step 3 — Analyze before writing anything

Run the analyzer from passnet-feedback (CPU-only works; GPU enables timings):

```bash
SCRIPTS=<repo>/.claude/skills/passnet-feedback/scripts
python3 $SCRIPTS/analyze_graph.py --sample-dir <dir> [--bench]
```

It prints, per variant, the dynamo graph with per-node **matchability** classification and
(with `--bench`, GPU) per-node eager timings. This tells you (a) which nodes a pattern can
legally bind to, (b) where the time actually goes — the bottleneck.

### Step 4 — Choose the strategy (decision policy)

Work through this in order:

0. **Heavy-op regime check — do this before labeling any dominant conv/matmul "leave in the
   vendor lib."** A vendor kernel is near-optimal only inside the shapes/parameters it tuned for
   and for the *general* form of its op; you can beat it only when the concrete parameters put
   the op OUTSIDE that regime AND equal a cheaper computation. The clearest checkable win to
   actively look for: a **convolution with `stride == kernel_size` AND `kernel_size > 1` AND
   `padding == 0`** (non-overlapping windows) — disjoint receptive fields make it exactly a dense
   patch matmul while cuDNN runs a heavier general path, so a `tl.dot` patch-gather kernel can win
   big; treat it as an ambitious anchor AFTER shipping the tail/floor. For ops in the vendor's
   sweet spot — 1×1 conv (already a cuBLAS GEMM), overlapping conv (im2col would blow up memory),
   depthwise/grouped, general dense matmul — the reliable default is leave-in-aten + fuse-tail;
   rewriting them usually loses. These are strong priors, not absolute bans: the completed eval
   is the arbiter, so if parameters give a concrete reason to expect a win you may try — but only
   after a floor is banked and only keep it if the eval beats the floor. Don't conclude a
   conv/matmul is "unmatchable" (they are C-bound and match fine); see passnet-orchestrate §2.2.

1. **Partition the graph** into maximal *matchable regions*: connected runs of matchable
   nodes (see passnet-pattern-fusion for the matchability rules) where the region has
   exactly ONE output consumed outside it. For normal callable patterns, kwargs-form
   Python-level F.* calls (for example `F.relu(x, inplace=False)`) usually become region
   boundaries because the pattern tracer normalizes them differently. If such a node blocks
   a high-value single-output region, use passnet-pattern-fusion's manual FX `GraphModule`
   pattern escape hatch and require real `check_pattern.py` proof; otherwise leave it in
   eager and fuse around it. Do not absorb `inplace=True` nodes merely because manual FX can
   match them; either reproduce the eager mutation exactly across repeated calls or leave the
   in-place node outside and fuse the downstream side-effect-free region.
2. **Estimate the win for each region** (numbers from `--bench`, or the heuristics in
   passnet-triton-opt §"performance model"):
   `gain ≈ (sum of eager µs of absorbed nodes) − (fixed tax ~50 µs amortized over regions) − (your kernel µs)`.
   - Many small elementwise/norm ops in one region → fuse them into ONE Triton kernel:
     best case, this is where big speedups live.
   - Long memory-bound elementwise or broadcast-affine-activation chains are now priority
     upside targets when they can be expressed as one legal single-output region. A floor
     still comes first for downside protection, but do not stop at a narrow floor on these
     shapes: attempt the larger legal region that absorbs the broadcast/layout producers
     and multiple affine, activation, residual, or normalization consumers unless
     containment, matchability, or numeric pre-flight proves it illegal.
   - Normalization-affine compute prefixes and concat→normalization-affine prefixes are also
     priority likely-amortizable targets when the prefix has one legal output and enough
     output work to pay the launch/framework tax. Keep a normalization-only floor first, then
     evaluate the broader prefix; repeated results show this family can win strongly, but
     small or branchy instances can still be correct-but-slow or regress and must be reverted
     to the best completed state.
   - `conv` / `matmul`: cuDNN/cuBLAS are near-optimal **only inside the regime they tuned for
     and for the op's general form**. Reliable default: leave the heavy op in aten and fuse its
     elementwise *tail* (bias, norm, activation, residual add) into one kernel; re-implementing
     the op competes with the library on its home turf and usually loses.
   - **When a rewrite CAN win — the clearest case: a convolution whose windows do not overlap** —
     `stride == kernel_size` along each spatial dim AND `kernel_size > 1` AND `padding == 0`.
     Then the receptive fields are disjoint, so the conv is exactly a matmul of flattened patches
     by the flattened weight (`patches @ weight.reshape(out_ch, -1).T`, plus bias). cuDNN still
     runs a general im2col/implicit-GEMM path with layout overhead it cannot skip, so a `tl.dot`
     patch-gather kernel that also folds the flatten/transpose/tail into its epilogue can win by
     a wide margin (the patch-embedding stem pattern). This is a real algorithm change, not a
     reimplementation of the same work. Treat it as an ambitious region AFTER the floor.
   - **Why the same rewrite usually loses elsewhere (so the default holds):**
     * **1×1 conv** (kernel_size 1) already IS a pointwise matmul cuBLAS runs directly — no
       general-conv overhead to remove, so `tl.dot` competes head-to-head and rarely wins.
     * **overlapping conv** (stride < kernel_size): a matmul form needs im2col, materializing a
       ~kernel_volume× larger matrix — the blow-up cuDNN's implicit-GEMM/Winograd avoids.
     * **depthwise / grouped conv** (groups > 1): memory-bound with specialized vendor kernels;
       grouped indexing is bug-prone.
     * **general dense matmul**: cuBLAS's sweet spot.
   - **These are strong priors, not bans — the completed eval is the arbiter.** If a specific
     op's parameters give you a concrete reason to expect it sits outside the vendor's efficient
     regime (a tiny/degenerate matmul, a memory-bound op fusable with a long tail into one
     kernel), you MAY try the rewrite — but only after a floor is banked, and keep it only if a
     completed eval beats that floor. Don't burn budget rewriting a sweet-spot op on a hunch;
     don't skip the non-overlapping case just because nothing forbids it.
   - Do NOT assume a heavy op is unmatchable: `conv1d/2d/3d`, `matmul`, `F.linear` are C-bound
     functions the pattern tracer binds to fine — mirror the exact positional call form and they
     match (see passnet-pattern-fusion §3). "It's a big cuDNN op" is never a reason to conclude
     the pattern can't match.
     Discipline is unchanged: ship the safe tail/floor first, then attempt any rewrite as an
     additional ambitious region and REVERT (Step 7) if a completed eval does not beat the floor.
   - Pure layout ops (`view`/`reshape`/`permute`/`transpose`/`unsqueeze`) cost ~0 in eager;
     absorbing them only pays when it lets you bridge two compute ops into one kernel, or
     erase a `.contiguous()` materialization.
   - Layout/view/reshape-only regions and split/fanout tails are usually downside caps:
     useful when they are the only safe way to match, but not a reason to spend tuning
     budget unless they bridge real compute or remove an actual materialization.
   - Be careful with vendor-heavy tails and layout materialization: a larger-looking region
     can lose when it replaces a vendor-tuned producer or forces eager-metadata layout work
     to become a real copy. If the completed larger-region eval is correct but slower, revert
     to the best completed state and record the caveat instead of tuning blindly.
3. **Total-eager-time sanity check**: if the variant's whole eager forward is tiny
   (< ~150 µs e2e, i.e. a couple of cheap ops) the fixed tax means the ceiling is < 1.
   Don't burn time chasing >1; ship the safest correct pass (floor pass) and move on —
   0.85 is a fine score for such a sample.
   If a narrow or floor pass has a completed eval, matches everywhere, is correct, and
   is still slower than eager, classify it as overhead-bound after checking region
   availability; keep it as the downside cap, revert any lower-scoring wider attempt,
   and stop unless there is a clearly larger legal region that absorbs enough eager work
   per launch to plausibly beat the tax.
4. **Skip-list**: never include in a pattern: RNG ops (`torch.rand`, dropout with
   `training=True`), data-dependent control flow, ops you cannot reproduce faithfully
   at the dtype's baseline tolerance (see tolerance table in references). Dropout with
   `training=False` IS safe (identity) when its call form is matchable.
5. **Multi-variant check**: a pattern containing shape literals (for example, a view with fixed dimensions)
   only matches variants with those exact literals. If shapes differ across variants,
   either avoid literal-bearing nodes in patterns, or write one pass per shape family —
   every variant must end with ≥1 matching pass.

### Step 5 — Ship the floor pass FIRST

Housekeeping when starting on a sample: `rm -rf pass_dir/__pycache__` and remove any
leftover `.py`/`.json` from previous occupants — `pass_dir` is imported as a package and
stale files/pyc can shadow your modules or load as unexpected extra passes.

Before any ambitious work, write + verify + evaluate the simplest possible pass:
**one matchable compute node** (prefer `batch_norm`/`layer_norm`/`linear`-tail/`gelu`/
`sigmoid`-class single op; a straightforward Triton kernel you cannot get wrong).
Once it scores (anything ≥ ~0.7), the sample's downside is capped. Keep it in `pass_dir`
until something better replaces it; ALWAYS re-evaluate after replacing.

### Step 6 — Build the upside, iterating

- Write fusion passes per region → use **passnet-pattern-fusion** (file contract, the 10
  hard rules, shared-dispatch architecture for multiple passes, kernel templates).
- ALWAYS pre-flight before GPU eval (`check_pattern.py`, from **passnet-feedback**):
  it verifies load → AST validation → match-per-variant → replacement wiring → a one-shot
  numeric smoke test, in seconds. Only then run the real evaluation.
- Tune slow-but-correct kernels with **passnet-triton-opt** only when the region still has
  plausible headroom. A completed eval that is correct but slow on a maximal tiny or
  layout-heavy region is usually a stop/revert decision, not an invitation to sweep block
  sizes.
- Interpret each evaluation with **passnet-feedback** (`parse_eval_log.py` gives per-variant
  status/speedups + estimated sample score + failure classification). Only a nonempty,
  JSON-parseable evaluation response counts as completed; if the response is empty,
  interrupted, or non-JSON, leave metrics unknown and fix service/upload/access state first.

### Step 7 — Iterate with discipline

- One change-class per iteration (match fix | numeric fix | perf tune); re-check, re-eval.
- Track the best-scoring `pass_dir` state; if an "improvement" lowers the score, revert.
  In service mode keep local copies of every uploaded version so you can restore.
- If a larger legal region completed evaluation but scored lower than the floor or narrow
  state, restore the best completed-evaluation state immediately and do not stack more
  passes on the worse state.
- If a broad manual-FX region is matched and correct but unstable or slower, try the narrower
  side-effect-free region before tuning blindly, especially when the broad region absorbed an
  in-place node or added branch-heavy index logic.
- Typical sane budget: ≤ 6–8 GPU evaluations per sample. Each full eval costs minutes
  (100 trials × variants); the 600 s timeout is real — samples with many variants
  (some have 100+ graphs) can time out if your kernel compiles many autotune configs.
  For such samples: NO autotune, one fixed config, minimal passes.
- Stop when: score ≥ your estimated ceiling × ~0.9, budget is exhausted with a correct
  matching pass in place, or completed evals show a correct narrow/floor pass is
  overhead-bound and no larger legal fusion region remains.

## 2. Strategy cheat-sheet by graph shape

| graph looks like | strategy |
|---|---|
| chain of elementwise + norm ops (MLP tail, norm+act+dropout) | one fused elementwise/row kernel over the maximal matchable region |
| broadcast/layout producer + affine/activation/residual consumers writing a large output | priority target: one legal single-output fused memory-bound kernel; verify it does not force a returned view or metadata-only layout into a costly materialization |
| concat or multi-branch producer → inference normalization → affine/activation | priority target when containment gives one normalized/final output; leave in-place downstream activations outside, and only include kwargs-form Python functional activations when a manual FX pattern pre-flight proves the exact region matches |
| `linear → (gelu/relu/silu) [→ dropout]` | fuse linear's tail if linear is big (keep cuBLAS), or `tl.dot`+epilogue if small; both: measure |
| `conv` with `stride == kernel_size`, `kernel_size > 1`, `padding == 0` (non-overlapping windows) | reduces to a patch matmul: gather disjoint patches + `tl.dot` against the flattened weight, and fuse the flatten/transpose/tail into the same kernel. Treat the conv as the region ANCHOR, not a wall. Ship a tail floor first |
| `conv → bn/act/add` (1×1, depthwise/grouped, or overlapping conv) | leave the conv in aten; fuse the tail ops into one kernel. Rewriting the conv usually loses (vendor sweet spot); the non-overlapping `stride==kernel_size`, `kernel>1` conv above is the case that IS worth rewriting |
| attention-ish (`matmul → softmax(method form) → matmul`) | softmax row-kernel (method-form softmax matches!); large generic matmuls stay aten; consider fusing scale/mask into the softmax kernel |
| `cat`/`stack` of tensors + elementwise or repeated producers | write the final output directly; compare one segmented kernel with a small number of grouped per-branch launches when branches have very different indexing/work |
| mean/sum/norm reductions + broadcast arithmetic (L2-norm, RMSNorm, sq-distance) | single row-reduction kernel producing the final output (verified ~1.6–2.5× on ms-scale tensors) |
| `expand`/broadcast → binary op writing a LARGE output | strong target even alone: aten broadcast-elementwise kernels often run 1.5–2.5× off the bandwidth roofline; a shape-specialized Triton kernel + erased layout nodes wins big (verified 2.3×) |
| mostly `view/permute/contiguous` + 1 compute op | replace the compute op only; or compute-op kernel that reads with source strides (absorbing a `contiguous`) |
| single huge op that is a generic dense matmul / 1×1 / depthwise / overlapping conv | floor pass on an adjacent/auxiliary node; accept ≈1.0; reimplementing usually loses. (A non-overlapping `stride==kernel_size`, `kernel>1` conv is the case worth rewriting — see that row.) |
| graph contains `torch.rand` / training-mode dropout | keep RNG nodes OUT of patterns; optimize around them |

## 3. Red lines (read references for the full list)

- Real computation must happen in **Triton kernels**. The wrapper may only use the
  whitelisted `torch.empty/zeros/ones/full[_like]/as_tensor` allocators plus shape/stride/
  dtype/device accessors — every other aten op on the (poisoned) inputs raises during the
  anti-cheat warmup, failing the variant.
- Do NOT evade validation (no `getattr(torch, ...)` laundering, no `no_dispatch()`, no
  monkeypatching the harness). It's classified as hacking behavior; assume it will score 0
  on the leaderboard even if it slips through locally — and it's usually slower anyway.
- `replacement_func()` must return a stable module-level function, and with
  `output_pass_replacement_func_limit: 1` **all your passes must return the SAME function
  object** — the shared-dispatch architecture in passnet-pattern-fusion is mandatory the
  moment you have ≥2 pass files.

## 4. Final report

End with: final score (last eval), pass_matched, per-variant speedup summary, list of pass
files, 1-paragraph strategy description, and (if below ceiling) what blocked further gains.
