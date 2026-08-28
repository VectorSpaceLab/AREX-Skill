---
name: passnet-orchestrate
description: >
  Round/batch planning and decision support for PassNet graph optimization. Use for
  multi-sample triage, worker allocation, eval-budget policy, and post-eval keep/revert
  decisions. For solving one concrete sample end to end, use passnet-solve as the entry
  skill; consult this skill only when you need broader planning or a specific decision gate.
---

This skill is the **planning and decision** layer for PassNet. It is not the single-sample
entry point. For one concrete sample, start with **passnet-solve**; it owns the end-to-end
loop and calls passnet-pattern-fusion, passnet-triton-opt, and passnet-feedback at the right
time. Use this skill when planning a multi-sample round, choosing which sample families to
dispatch, auditing whether a line of attack is overhead-bound, or deciding whether to keep,
revert, or stop after completed evaluations.

For context, a **sample** = several **graph variants** of the same subgraph (different dtypes —
float32 / float16 / bfloat16 — and seeds/batch dirs). You write passes; the harness
pattern-matches them into each variant's graph, checks correctness vs eager, and measures
end-to-end speedup. Your deliverable is a final report (§8).

This skill is self-contained: every decision below is made from each variant's `model.py`
(the computation), `weight_meta.py` (shapes/dtypes), and the evaluation results. It does not
depend on any external helper script. It does, at two points, rely on *capturing the real
graph and running the real matcher/kernel* (to confirm a pattern matches and a kernel is
correct before spending a GPU eval) — that is a local, GPU-free check you can run yourself.
The `passnet-feedback` scripts package that check for convenience; use them if present, but
the flow never requires them and you must have a hand fallback when they can't capture a
graph.

---

## 1. The score is the strategy

Four metrics are reported; the **AS Score** (an ES-weighted geometric mean of per-variant
"rectified speedups") is the headline, and the other three (G-Mean Speedup, Correctness,
fast_1) move with it. Optimize the AS Score. Two facts about it drive every decision below:

**The rectification cliff.** Per variant, your outcome is worth roughly:

| outcome                                   | worth (rectified speedup) |
|-------------------------------------------|---------------------------|
| no pass matched, or a crash/runtime error | **~0.1**                  |
| matched but numerically wrong             | **~0.15**                 |
| matched + correct, end-to-end speedup `s` | **~s** (even when s < 1)  |

So a **matched, correct pass that runs at 0.8× scores ~8× better than not matching (0.1).**
Slow-but-correct is a *good* outcome; not-matching is a disaster.

**The geometric-mean trap.** The sample score is a geometric mean across **all** variants.
One variant at 0.1 drags the whole sample down hard — a single red variant outweighs a hero
result on another. **Consistency across every variant beats a peak on one.**

Consequences this skill enforces (internalize these — they explain every rule that follows):
1. **Never finish with an empty or non-matching `pass_dir`.** A floor pass is mandatory.
   Matching even a *free-in-eager* region for a sub-1.0 score is far better than 0.1 — when
   that's the only region you can bind to, take it (a constrained floor of ~0.5 still beats
   0.1 by ~5×).
2. **Never ship a change that turns a previously-green variant red.** Protect the gmean.
3. **Prefer ONE pattern that covers every variant** over per-variant passes — fewer ways to
   leave a variant unmatched, and one evaluation validates them all. The way to do this is to
   write patterns with NO shape/scalar literals that differ across variants.
4. **You do NOT have to cover every observable output.** A single matching pass already
   modifies the graph (no 0.1); any output your passes don't produce simply runs in eager and
   still scores. So target the **highest-value single region** rather than trying to absorb
   the whole graph. (Tiny diffs may appear on outputs your kernel never touched — e.g. eager
   dtype-cast nondeterminism — and they pass baseline tolerance; don't chase them.)

(The exact tolerance weights and scoring formula are mechanics — see passnet-skill / its
references. You don't need them to make decisions; you need the cliff and the trap.

When the harness reports an **authoritative aggregated score**, trust THAT over any estimate.
A variant is "correct" at the dtype's *baseline* tolerance — not the strict bit-exact column.
Read the end-to-end speedup, the success/failed status, and baseline-tolerance correctness;
do not be alarmed by a nonzero diff that is still within baseline tolerance.)

---

## 2. "Can I even win?" — the cost gate

The compiled path pays a **fixed per-call tax** (graph-guard + interpretation + wrapper +
launch overhead) that does not exist in eager. It is small on tiny graphs and grows with
graph size; each Triton kernel launch adds more on top. You don't need the exact numbers —
you need the rule they imply:

> **You only win when the eager work you absorb into your kernel(s) per launch exceeds the
> tax you add.** Replacing one cheap op on a small graph loses; absorbing many ops, or
> replacing genuinely heavy memory-bound work, wins.

Calibrate the real tax for *this machine and graph* from your first evaluation (compare the
compiled median against eager minus the work you removed) and reuse it when estimating later
regions. The detailed performance model lives in **passnet-triton-opt**; bring just enough
intuition here to triage floor-vs-ambitious in §3.

---

## 2.2 The one heavy-op exception — non-overlapping conv reduces to a patch matmul

The right question is never the op's *name*, it is its *regime*. A vendor kernel
(cuDNN/cuBLAS) is near-optimal only for (a) the shapes/parameters it has tuned kernels for and
(b) the *general* form of its op class. You can beat it only when the op's concrete parameters
put it OUTSIDE that efficient regime AND make it equal to a cheaper computation you can express
as a legal Triton kernel. Otherwise you are competing with a vendor library on its home turf and
will lose. Derive this from the parameters in front of you — do not memorize a per-op verdict.

The clearest checkable win, and the one to actively look for:

- **A convolution whose windows do not overlap** — `stride == kernel_size` along each spatial
  dim, `kernel_size > 1`, `padding == 0`. Each output reads a disjoint input patch (no input is
  reused), so the conv is *exactly* a dense matmul of flattened patches by the flattened weight
  (`patches @ W.reshape(Co,-1).T` plus bias). cuDNN does not specialize for this — it runs its
  general convolution path (implicit-GEMM / im2col / Winograd) built for the overlapping case,
  which for an odd kernel/channel shape can be far off a well-shaped GEMM. A `tl.dot`
  patch-gather kernel that also folds the flatten/transpose/tail into its epilogue can win by a
  wide margin. Confirm `stride == kernel_size` and `kernel_size > 1` from the parameters.

Why the *same* rewrite usually LOSES on the other conv/matmul shapes — i.e. why the reliable
default is "leave the op in aten and fuse its elementwise tail":

- **1×1 conv** already *is* a pointwise matmul (PyTorch lowers it to a cuBLAS GEMM); there is no
  general-conv overhead to remove, so a hand `tl.dot` competes head-to-head with cuBLAS.
- **overlapping conv** (`stride < kernel_size`, e.g. 3×3 s1): writing it as a matmul needs
  im2col, which materializes a ~kernel_volume× larger matrix — the exact memory blow-up
  cuDNN's implicit-GEMM/Winograd avoids. You pay more, not less.
- **depthwise / grouped conv**: memory-bound with specialized vendor kernels; a hand kernel
  rarely wins and grouped indexing is bug-prone.
- **large/general dense matmul**: cuBLAS's sweet spot.

None of this is an absolute rule — **the completed eval is always the arbiter.** The lines above
are strong *priors*, not prohibitions: if the concrete parameters give you a specific reason to
believe a case sits outside the vendor's efficient regime (e.g. a tiny/degenerate matmul, or a
memory-bound op you can fuse with a long tail into one kernel), you may try it — but only AFTER
banking the tail/floor pass, and you KEEP it only if a completed eval beats that floor. Do not
spend budget rewriting an op that is squarely in the vendor's sweet spot on a hunch, and do not
skip the non-overlapping case just because no rule forbids it.

Two matchability facts (independent of the above): `conv1d/2d/3d`, `matmul`, `F.linear` are
C-bound functions the pattern tracer binds to fine — "it's a big cuDNN op" never means the
pattern can't match.

Discipline (unchanged and mandatory): **always ship the tail/floor pass FIRST** (S3); only then
attempt a rewrite as an additional ambitious region; REVERT (S5/GATE e) if a completed eval does
not beat the banked floor. The rewrite is upside insurance layered on top of the floor, never a
replacement for it.

---

## 2.1 Round triage gate — choose likely-amortizable samples first

When planning a multi-sample round, do not dispatch workers randomly across small graphs.
Spend a cheap triage pass first and label each candidate sample:

- `likely_amortizable`: at least one legal single-output region absorbs substantial real
  compute per launch: a large-output broadcast/binary op, a sizeable reduction plus its
  arithmetic, a long elementwise/norm chain over enough elements, or a compute tail that can
  be fused without reimplementing a vendor-optimal heavy op.
  Judge this from candidate regions, not only whole-sample labels: a sample with global
  returned values or producer fanout can still be likely amortizable when a downstream
  consumer-side region leaves the shared producer outside the pattern and returns one legal
  output.
- `downside_cap_only`: only tiny regions, layout/view/reshape-only work, returned views,
  split/fanout layout tails, or cheap consumers behind boundaries that are not worth
  repairing. These can still justify a floor pass to avoid 0.1, but they should not consume
  scarce worker slots in a performance-strategy round unless you need calibration examples.
- `blocked_by_contract`: every promising compute region would require multiple externally
  observable outputs, hiding a shared producer with outside consumers, RNG/data-dependent
  work, or a call form that cannot be recovered by exact/manual-FX matching. These are
  pattern-fusion lessons, not performance targets.
- `unstable_eval_risk`: previous or local evidence suggests evaluator timing instability,
  timeout risk, or many variants with heavy compile cost. Track this separately from
  numeric, no-match, and unauthorized-operator failures; it may justify rerunning an
  unchanged confirmed state, not rewriting the kernel.

Dispatch priority for performance validation:
1. `likely_amortizable` long memory-bound elementwise or broadcast-affine-activation chains:
   layout/broadcast producers plus multiple affine, activation, residual, or normalization
   consumers that can be contained in one single-output region. Repeated round evidence shows
   these are the best first allocation for performance-strategy validation because they can
   save multiple memory passes per Triton launch.
2. Clean normalization-affine compute prefixes and concat-to-normalization-affine prefixes:
   allocate formal workers to them after verifier/probe success, but record mixed outcomes
   separately. The same static family can produce strong wins, near-eager correct states, or
   a reverted floor depending on size, branch structure, dtype boundaries, and whether the
   profitable prefix is truly the actual winning region.
3. Local-region candidates recovered by a backward slice from a promising output. Allow
   shared, returned, vendor-heavy, or otherwise risky producers to stay outside the pattern
   as inputs when the downstream region itself has one output and absorbs enough compute.
   Repeated evidence shows this avoids over-pruning while preserving the single-output
   contract.
4. Other `likely_amortizable` samples with all key anchors matchable.
5. `likely_amortizable` but one boundary uncertain, if a cheap pre-flight can settle it.
6. A small number of reduction-only or vendor-tail controls. Allocate these deliberately,
   not as filler: repeated results show they often end correct-but-slow unless a larger
   compute-containing region is both legal and numerically clean.
7. Defer `blocked_by_contract` unless the round is specifically about matcher behavior.

For batch planning, keep separate fields for `triage_family`, `worker_confirmed_family`,
and `actual_winning_region_family`. Do not credit a successful larger replacement to the
initial triage family when the completed evaluation shows the winning region was really a
different family, such as a compute-plus-normalization prefix, a layout materialization tail,
or a vendor-heavy replacement. Use family-level completed-evaluation counts to adjust the
next batch allocation: wins above eager, correct-but-slow, numeric-preflight blocks,
correctness regressions on larger regions, and larger-region attempts.

This gate is benchmark-general: the goal is to spend workers where absorbed eager work can
plausibly pay for wrapper/framework/launch tax, then use completed evaluations to confirm.

---

## 3. The decision flow

Follow this top to bottom. Gates are marked **(a)–(e)**; sub-skill hand-offs are marked
**→→ CALL**.

```
S0. SET UP  (mechanics — see passnet-skill)
    - Read graph_list + every variant's model.py and weight_meta.py.
    - In service mode, confirm service health and verify uploaded pass files with /files before any /evaluate call.
    - In Codex managed sandboxes, try bounded normal localhost curl first; if it fails, retry once and then use the approved escalated localhost path if available. Do not interpret sandboxed connection failures as service downtime.
    - Clear stale files from pass_dir (it is imported as a package; leftovers shadow yours).

S1. CHARACTERIZE  (no GPU; read the graphs, then verify matchability with the real matcher)
    - For each variant list: ops in their EXACT written call form, tensor shapes, dtypes.
    - Mark each node matchable / unmatchable for normal callable patterns (the rules are in
      passnet-pattern-fusion). RNG/data-dependent nodes are hard walls. Keyword-form Python
      functional calls are walls for callable patterns, but a high-value single-output region
      may be recoverable with an exact manual FX `GraphModule` pattern; require real matcher
      proof before treating it as legal. In-place / augmented-assign ops (a node written as
      `x op= c`, or a call flagged in-place) often normalize to a different form than your
      pattern produces; bind to neighbours unless passnet-pattern-fusion proves an exact
      pattern can match and the replacement preserves the eager mutation semantics across
      repeated calls.
    - Partition the graph into maximal matchable REGIONS, each with exactly ONE value
      consumed outside it. Eyeballing model.py tells you the candidate regions, but whether a
      given op actually matches is often NOT visible by eye — confirm it with the real matcher
      (capture the graph + run the subgraph matcher, see S3 pre-flight) before you commit the
      strategy to a region.
    - Mark region economics before authoring: compute-heavy and large-output regions are
      likely amortizable; layout/view/reshape-only regions, returned views, and split/fanout
      layout tails are downside caps unless they bridge compute or remove a real
      materialization.
    - Classify the sample against the archetype table (§4) — this names your line of attack.
    - Cross-variant literal check: do shape/scalar LITERALS differ across variants? If yes,
      a shared pattern must avoid those literals (or you need per-shape passes). Every
      variant must end with >=1 matching pass.

S2. CEILING TRIAGE          ===== GATE (a): FLOOR vs AMBITIOUS =====
    Estimate, per region, whether absorbed eager work clearly exceeds the tax (§2).
    - Total eager work tiny / no region absorbs more than the tax
            -> OVERHEAD-BOUND. Target = a safe FLOOR only. (Ceiling < 1; do not chase >1.)
    - The only legal matchable regions are layout/view/reshape/split-fanout floors
            -> DOWNSIDE CAP. Evaluate the safest correct state if needed, but do not tune it
               blindly; stop after a completed correct eval unless a larger compute-containing
               region becomes legal.
    - The dominant cost is a heavy conv/matmul in the vendor sweet spot (1×1, depthwise/grouped,
      overlapping conv, or a general dense matmul) with no worthwhile cheap tail
            -> DEFAULT to not reimplementing it: floor on an adjacent node; accept ~1.0.
      Precondition: you checked §2.2. The clearest upside case (below) is a non-overlapping conv
      (`stride == kernel_size`, `kernel_size > 1`, `padding == 0`); the others are strong-prior
      walls, not absolute — a completed eval may still justify a rewrite in a specific
      off-regime shape.
    - There is a fusible region whose absorbed work clearly beats the tax, OR a heavy op that
      §2.2 shows sits outside the vendor's regime and equals a cheaper computation
            -> REAL UPSIDE. Ambitious path enabled.

S3. SHIP THE FLOOR FIRST  (cap the downside before taking any risk)
    Pick the single most trivially-correct matchable region — one compute node you cannot get
    numerically wrong. This caps EVERY variant at "matched + correct."
    →→ CALL passnet-pattern-fusion  — author the floor pass (pattern + replacement + a single
       kernel; use the shared-dispatch layout from the start even for one pass).
    - PRE-FLIGHT (no GPU) — MANDATORY before every eval (this is the single biggest lever for
      not wasting evals). Check two things:
        (1) MATCH: re-read your pattern against each variant's model.py — exactly one output?
            exact call form (method vs function, positional vs kwargs, no in-place op inside)?
            literals equal across the variants it must cover? every inside-node consumed only
            inside? Confirm it would match EVERY variant.
        (2) NUMERICS: run your kernel once on inputs of the right shape/dtype and compare to
            the eager computation at the dtype's baseline tolerance. Index-arithmetic kernels
            (copies, permutes, strided gathers) are the #1 source of silent wrong answers —
            always numerically check them before an eval.
      The reliable way to do BOTH checks without a GPU eval is to reproduce the harness
      locally: capture each variant's real graph (compile the model with a graph-capturing
      backend, or trace it) and run the actual subgraph matcher with your pattern against it,
      then run your kernel on correctly-shaped/dtyped inputs and compare to eager. The
      passnet-feedback checker packages exactly this — use it if available. But it is only a
      convenience: it can itself fail to capture some graphs (e.g. ones using advanced integer-
      tensor indexing or other data-dependent ops). When it fails, fall back to capturing the
      graph yourself the same way and running the matcher/numeric compare directly — do NOT
      skip the pre-flight and "just try an eval." Reading model.py by eye is the weakest form
      of this check and misses non-obvious unmatchable forms; prefer the real matcher.
    - EVALUATE  (GPU eval #1).                ===== GATE (e) applies after every eval =====
        * service upload unconfirmed -> do NOT evaluate; fix upload/listing first.
        * empty/interrupted/non-JSON eval response -> no metrics exist; retry or fix service access/state before making strategy conclusions.
        * not matched / wrong -> fix MATCH or NUMERICS and re-eval; a floor that doesn't
          match is worse than useless.
        * matched + correct  -> snapshot this pass_dir as BEST-KNOWN-GOOD; calibrate the tax
          from this eval's numbers.
    - If GATE (a) said FLOOR-only -> go S7. Else -> S4.

S4. BUILD UPSIDE — one region at a time
    Choose the single highest-expected-gain region not yet addressed.
    →→ CALL passnet-pattern-fusion  — pick which ops to absorb into the region, author the
       pattern, and (for >=2 passes) wire the shared-dispatch architecture.
       GATE (b): any time you author or repair a pattern, or decide what to fuse, you are
       in passnet-pattern-fusion — not here, not passnet-triton-opt.
    - PRE-FLIGHT (no GPU), MANDATORY — same two checks as S3 (match every variant + numeric
      sanity at baseline tolerance). Fix any match/numeric problem BEFORE spending a GPU eval.
    - EVALUATE (GPU eval #k). Read per-variant status + speedups + the authoritative score.

S5. ===== GATE (e): REVERT or KEEP =====   (run after EVERY eval)
    - Authoritative score < BEST-KNOWN-GOOD, OR any variant that was green is now red
            -> REVERT to BEST-KNOWN-GOOD immediately. Do not stack a new change on a worse
               base. Diagnose from the log, then try a DIFFERENT single change or abandon the
               region.
    - Otherwise -> this becomes the new BEST-KNOWN-GOOD. Continue.

S6. ===== GATE (c): matched + correct but SLOW? =====
    - A region matches and is correct but its speedup is below the ceiling, OR correctness
      misses by a SMALL numeric margin (a dtype-tolerance miss, not a gross bug)
            →→ CALL passnet-triton-opt  — perf tuning and/or numeric-fidelity fix. Change ONE
               class at a time (perf XOR numeric). Re-eval -> back to S5.
    - A completed eval is matched and correct but slower than eager, and the region is already
      maximal or only layout/view/fanout work remains
            -> OVERHEAD-BOUND STOP. Keep the best completed state as the floor/downside cap;
               do not spend evaluations on block-size sweeps or tiny independent kernels.
    - A wider legal attempt completed but scored lower than the floor or narrow state
            -> REVERT and STOP that line unless a different likely-amortizable region remains.
    - A broad manual-FX attempt is matched and correct but unstable or slower after absorbing
      an in-place node
            -> REVERT to the best state and consider a narrower downstream region that leaves
               the side effect in eager.
    - Matched, correct, at/near ceiling -> this region is done.

    ===== GATE (d): STOP? =====  Stop when ANY of:
        * best score >= ~0.9 x your estimated ceiling, OR
        * GPU-eval budget exhausted AND a matched+correct pass is in place, OR
        * the last 2 evals produced no improvement, OR
        * no un-addressed region has expected gain greater than the tax.
    Otherwise pick the next region -> S4.
    CEILING SANITY: if a dominant conv is the reason your ceiling is ~1.0, first confirm (§2.2)
    it is NOT a non-overlapping conv (`stride == kernel_size`, `kernel_size > 1`, `padding == 0`)
    — that one case has a much higher ceiling via a patch-matmul rewrite. Do NOT "preserve
    budget" by stopping early when that specific reformulation remains unattempted and evals
    remain. (For 1×1 / depthwise / general matmul a ~1.0 ceiling IS correct — don't chase them.)

S7. FINAL REPORT (§8). Make sure BEST-KNOWN-GOOD is what is on disk.
```

Compact tree:

```
read sample -> characterize -> ceiling triage (a)
   overhead-bound / vendor-heavy  -> floor (b) -> eval -> report
   real upside                    -> floor (b) -> eval -> [loop: pick region (b) -> eval
                                                           -> revert-or-keep (e)
                                                           -> if slow/near-miss tune (c)
                                                           -> stop? (d)] -> report
```

---

## 4. Graph-shape archetypes → line of attack (operator-AGNOSTIC)

Classify by **dataflow structure, tensor-size regime, and matchability — never by which
operator it is**. (The right kernel is derived from the graph in front of you; this table
only tells you *where the upside lives* and *what to try first*.)

| structural shape | size regime | line of attack | rough ceiling |
|---|---|---|---|
| a chain of cheap elementwise/normalize ops feeding ONE output | any | fuse the maximal matchable region into one kernel | good if tensors large; ~1.0 if tiny |
| a reduction over a large axis, then arithmetic on the result | ms-scale tensors | one fused reduction kernel producing the final output | among the highest (often >1.5×) |
| a broadcast/expand feeding a binary op that WRITES a large output | large output | one shape-aware kernel; absorb the layout ops | strong even alone |
| a heavy conv/matmul + a cheap tail — 1×1 conv, depthwise/grouped conv, overlapping conv, general dense matmul | any | default: leave the heavy op in the graph; fuse only the tail. Rewriting the op is usually a loss (vendor sweet spot) — try only if parameters suggest off-regime AND a completed eval beats the floor | bounded by tail size |
| a non-overlapping conv (`stride == kernel_size`, `kernel_size > 1`, `padding == 0`) | any | reformulate as a `tl.dot` patch-gather kernel + fused tail; the conv is the region ANCHOR, not a wall. Ship a tail floor first | can be large |
| tiny total eager time (a couple of cheap ops) | small | overhead-bound: ship a floor, accept < 1 | < 1 |
| mostly layout ops (view/reshape/permute/transpose) + 1 compute op | any | replace the compute op only; absorb adjacent layout for free | modest |
| the only matchable region is a layout op whose result is RETURNED directly (a view eager never materializes) | any | replacing it FORCES a copy eager skips, so it scores < 1 — but it still matches; take it ONLY as a last-resort floor to escape 0.1 | < 1, but >> 0.1 |
| split/fanout layout region with multiple externally observable consumers | any | single-output floor or separate consumer-side passes only; do not hide the shared producer | < 1 unless each pass absorbs real compute |
| graph contains RNG / data-dependent / unrecovered call-form / in-place nodes | any | those nodes are walls by default; try exact manual FX only for valuable single-output call-form blockers, otherwise fuse around them | bounded by what's left |

Rules for using this table:
- **Matchability overrides structure.** A graph can look exactly like a high-upside row (a
  reduction-then-arithmetic chain, say) yet score < 1, because the op that would anchor the
  fusion is in a form a normal callable pattern cannot reproduce, or because an in-place,
  RNG, or data-dependent node severs the region. So BEFORE you commit to an ambitious row,
  confirm the anchor op actually matches. For kwargs-form Python functional blockers, first
  try the normal callable form; if it near-misses and the region is valuable, use
  passnet-pattern-fusion's manual FX pattern path and verify it with the real matcher.
  **Verify matchability with the real matcher** (the passnet-feedback checker, or a graph
  capture you do yourself per S1) before building on a region — not just before the eval.
- Pick the row that matches the **structure** AND whose anchor op is matchable, then hand the
  region to **passnet-pattern-fusion** to turn into a concrete pattern + kernel.
- Layout-only ops are ~free in eager: absorbing them pays only when it lets you bridge two
  compute ops into one kernel or erase a materialization — not as a goal in itself. The one
  exception is the last-resort floor above: when EVERY compute op is unmatchable, materializing
  a returned view is the only way to modify the graph, and a ~0.5 beats a 0.1.
- If two rows apply, prefer the one with the larger absorbed-work-per-launch.
- Your kernel can be faster than eager in isolation yet the sample still lands near 1.0,
  because an unmatchable neighbour you couldn't absorb stays in BOTH paths. The ceiling is set
  by absorbed work, not total work — estimate it from what you can actually bind to.

---

## 5. Dead ends (DON'T) and disciplines (DO)

**DON'T** (each line is a path that scores badly — avoid it):
- **Finish with an empty or non-matching `pass_dir`.** That's the 0.1 floor; a slow correct
  pass is ~8× better.
- **Return more than one value from a pattern.** Multi-output crashes the variant -> 0.1.
  If two intermediates are observable, that's two separate passes (passnet-pattern-fusion).
- **Add a second pass without the shared-dispatch architecture.** With >=2 passes the harness
  silently drops any pass whose replacement function differs -> variants stop matching.
- **Re-implement a vendor-optimal heavy op in a custom kernel that does the SAME work** — a
  general dense matmul, a 1×1 conv (already a pointwise GEMM), a depthwise/grouped conv, or an
  overlapping conv, when it sits in the vendor's efficient regime. You will lose to the library;
  fuse its cheap tail instead. (The clearest exception is not "the same work": a non-overlapping
  conv — `stride == kernel_size`, `kernel_size > 1`, `padding == 0` — is algebraically a dense
  patch matmul while cuDNN runs a heavier general path, so a `tl.dot` patch-gather rewrite is a
  real algorithm change worth pursuing; see §2.2. This red line is a strong prior — a completed
  eval can still justify a rewrite for a provably off-regime shape. Also: never conclude a heavy
  op is unmatchable — it is a C-bound function that binds fine.)
- **Chase >1.0 on an overhead-bound sample.** The tax caps the ceiling below 1 — take the
  floor and move on.
- **Tune a correct-but-slow tiny/layout-only/fanout floor by reflex.** First ask whether a
  larger legal compute-containing region exists; if not, stop with the floor.
- **Make multi-change rewrites between evals.** Regressions become un-diagnosable. One
  change-class per eval.
- **Build on top of a change that lowered the score.** Revert to BEST-KNOWN-GOOD first.
- **Put RNG / data-dependent / unrecovered call-form nodes inside a pattern.** They are
  region boundaries; including them without exact matcher proof means no match.
- **Evade the anti-cheat** (operator laundering, dispatch tricks, returning precomputed eager
  results). It's classified as hacking, scores 0 on the leaderboard, and is usually slower
  than eager anyway.
- **Spend a GPU eval to discover a match failure** you could have caught by running the real
  matcher against the captured graph, or a numeric bug you could have caught by running the
  kernel once on correctly-shaped inputs.
- **Mis-judge correctness from a strict bit-exact comparison.** A variant counts as correct
  at its dtype's *baseline* tolerance, which is loose for fp16/bf16. A small nonzero diff —
  especially on an output your kernel never produced — is usually fine. Read the authoritative
  speedup/score, not the strict-equal column.
- **Abandon a region as "infeasible" because your first kernel was wrong.** A wrong result is
  a numeric bug to fix (one change-class), not proof the strategy can't work.

**DO** (process discipline that the trajectories show pays off):
- **Ship a trivially-correct floor pass first**, then build upside on a known-good base.
- **One change-class per iteration** (match | numeric | perf) so every eval is attributable.
- **Track a BEST-KNOWN-GOOD snapshot** and revert to it on any regression. In service mode
  keep a local copy of every uploaded version.
- **Write patterns with no shape literals when variants differ only by shape** — one pass
  then covers all variants and one eval validates them.
- **Calibrate the per-call tax from your first eval** and reuse it in ceiling estimates.
- **Maximize ops absorbed per launch** rather than shaving an already-tiny kernel.
- **Recognize overhead-bound samples early and accept a sub-1.0 floor.**
- **Classify evaluator timing instability separately** from no-match, numeric,
  unauthorized-operator, timeout, and OOM failures. If the pass pre-flights cleanly and
  successful variants are correct, an unchanged rerun can be a valid use of budget.
- **Abandon a fundamentally-losing line of attack early** (don't sink evals into fighting a
  vendor kernel or a region whose absorbed work can't beat the tax) — but distinguish "wrong
  strategy" from "right strategy, buggy kernel": fix the bug before abandoning.
- **Read the authoritative result.** Use end-to-end speedup + success status + baseline-
  tolerance correctness as ground truth; treat any other estimate as a hint, not a verdict.

---

## 6. GPU-eval budget & iteration discipline

GPU evaluations cost minutes (many trials × many variants) and there is a hard per-eval
timeout. Treat them as the scarce resource and plan around them:

- **Budget ~6–8 GPU evals per sample.** If you're past that without progress, ship
  BEST-KNOWN-GOOD and stop.
- **Eval #1 is always the floor pass** — it buys downside insurance and calibrates the tax.
  Never spend eval #1 on an ambitious multi-pass attempt.
- **Pre-flight before every eval is mandatory** (both checks in S3: match-every-variant +
  numeric sanity at baseline tolerance — by hand or with the optional checker). A GPU eval
  that only learns "didn't match" or "kernel was wrong" is wasted; the budget assumes you
  never spend one that way. Done well, this drives wasted evals toward zero.
- **One change-class per eval** — so each eval answers exactly one question.
- **Many-variant samples (tens to 100+ graphs) risk timeout.** There, minimize compile cost:
  no autotune, a single fixed kernel config, the fewest passes, and a small fixed set of
  compile-time specializations. (The *how* is passnet-triton-opt; the *decision to do it* is
  yours, here, based on variant count.)
- **Snapshot every evaluated pass_dir state** so reverting is instant.

---

## 7. Generalization & anti-copy

The sample you are given will differ from anything you've seen. **Derive the optimization
from the dataflow in `model.py` and the shapes/dtypes in `weight_meta.py` in front of you** —
not from a remembered "for operator X do Y" recipe. If you catch yourself recalling a
per-operator formula, stop and re-derive it from the actual graph; the held-out set is built
to punish memorized answers. This skill deliberately gives you *decision structure* (where to
start, what to try, what to avoid), and leaves the operator-specific kernel math to be worked
out per problem in passnet-pattern-fusion / passnet-triton-opt.

---

## 8. Final report

End your work with:
- **Final AS Score** (from the last evaluation) and whether the pass matched.
- **Per-variant summary**: dtype → matched? correct? speedup.
- **Pass files** you created and a one-paragraph strategy description.
- If below the ceiling you estimated: the specific blocker (overhead-bound, vendor op,
  numeric limit, timeout, …).
- Do NOT write result files to disk; your reply text is the result.

---

## 9. Where things live (boundary map)

| skill | owns |
|---|---|
| **passnet-orchestrate** (this) | the decisions: where to start, what to try, dead ends, floor-vs-ambitious, revert/stop, eval budget |
| **passnet-pattern-fusion** | authoring patterns that match, choosing fusion regions, multi-pass shared-dispatch wiring, kernel templates |
| **passnet-triton-opt** | making a matched kernel fast (block/grid/warps/autotune/launch) and numerically faithful per dtype |
| **passnet-skill** | mechanics: fetching the problem, the pass-file format, how evaluation is invoked |
| **passnet-feedback** (optional) | scripts that give the same analysis/pre-flight/log-parsing faster — never required by this flow |

This skill is the **strategy** half and **passnet-skill** is the **mechanics** half; use them
together (this one to decide, that one for how to fetch/format/evaluate). If you only need to
know *how* to do a mechanical step, go straight to passnet-skill; for *what to do and in what
order*, stay here.
