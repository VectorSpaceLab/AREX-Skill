---
name: passnet-feedback
description: >
  Fast, deterministic feedback for PassNet work: pre-flight pattern/match verification
  WITHOUT burning a GPU evaluation, per-node bottleneck analysis of a sample's graphs,
  and eval-log parsing into per-variant status + estimated score + failure classification.
  Use BEFORE every GPU evaluation (check_pattern), at the START of a sample
  (analyze_graph), and AFTER every evaluation (parse_eval_log).
---

GPU evaluations cost minutes and are rate-limited; these tools answer in seconds. The
iteration loop is: `analyze_graph` once → author passes → `check_pattern` until green →
GPU evaluate → `parse_eval_log` → fix the top issue → repeat.

All scripts live in the `scripts/` directory next to this `SKILL.md`. In this repo, prefer
`SCRIPTS=<repo>/.claude/skills/passnet-feedback/scripts`. Invoke
`python3 $SCRIPTS/<name>.py ...` from anywhere. They need: the PassNet repo importable
(auto-detected from the sample dir's `entry.sh` symlink, or set
`PYTHONPATH`/`PASSNET_ROOT`), torch, and for smoke/bench steps a GPU
(`CUDA_VISIBLE_DEVICES` respected; they degrade to CPU structure-checks without one).

## 1. `analyze_graph.py` — where is the bottleneck, what is matchable

```bash
python3 $SCRIPTS/analyze_graph.py --sample-dir <sample_root> [--bench] [--max-variants N]
# default --max-variants 3, dtype-spread
```
- Captures the REAL dynamo graph of each variant (exactly what passes must match).
- Per node: op kind, target, written args/kwargs form, output shape/dtype, and callable
  pattern **matchability** (`method`/`C-bound` = mirror exactly; `PY-sig positional` =
  matchable; `PY-sig kwargs/partial` = normal callable pattern will normalize differently).
  A high-value kwargs-form Python functional region may still be recoverable with an exact
  manual FX `GraphModule` pattern; use passnet-pattern-fusion and confirm with
  `check_pattern.py`.
- `--bench` (GPU): per-node eager µs via an instrumented FX interpreter + whole-forward
  eager e2e estimate → tells you the absorbable time and a ROUGH speedup ceiling. The
  ceiling assumes a ~70 µs fixed tax — real tax grows with FX node count (150–230 µs on
  13-node graphs); treat the printed ceiling as optimistic and recalibrate after your
  first eval.
- Use the region table at the bottom as the starting plan: it lists maximal runs of
  matchable nodes with their absorbed-µs totals.

## 2. `check_pattern.py` — pre-flight a pass_dir in seconds (run before EVERY eval)

```bash
python3 $SCRIPTS/check_pattern.py --sample-dir <sample_root> [--pass-dir <dir>] [--smoke [--bench]]
# --max-variants N (default 8, dtype-spread; 0 = all). --bench implies --smoke.
# --smoke/--bench run on ONE variant per dtype; matching runs on all chosen variants.
```
Replicates the harness pipeline faithfully and reports:
1. JSON manifest sanity (names ↔ files).
2. AST validation per pass (the real `validate_pass_source` when repo importable).
3. `replacement_func()` stability + **distinct-function count** (must be 1 when >1 pass —
   otherwise passes WILL be silently dropped by the limit).
4. Pattern trace → real `SubgraphMatcher` against each variant's dynamo graph:
   match count per pass per variant, single-output check, containment check, and on
   mismatch a node-by-node nearest-miss diff (pattern form vs graph form).
5. Verdict per variant: would the run match (≥1 pass), or early-exit at 0.1.
6. `--smoke` (GPU): actually applies the passes (real `PassMgrBackend`) and runs one
   poisoned warmup call + numeric comparison vs eager at the dtype's baseline tolerance —
   catches Unauthorized-Operator, dtype mismatch, and gross numeric bugs pre-eval.
7. `--bench` (GPU): micro-benchmarks compiled-vs-eager e2e (200 calls) per variant for a
   speedup preview (no dynamo guards, so real eval ≈ a few % worse).

CPU-only output can validate structure and matchability triage, but it does not prove poisoned-wrapper legality, dtype behavior, numeric correctness, or real speed. GPU smoke/bench or a completed evaluation is still required for those claims.

`--smoke` is a one-shot semantic check, not a full harness proof. Be extra cautious when a
replacement absorbs `inplace=True` nodes or other side-effectful behavior: a one-shot compare
can pass while repeated benchmark calls expose mutation/aliasing differences. For those
regions, either leave the in-place node outside the pattern or confirm repeated-call behavior
with a harness-style check/completed evaluation.

Green output = safe to spend a GPU evaluation. Any red line tells you which skill to open:
match issues → passnet-pattern-fusion §7; poison/API issues → passnet-pattern-fusion §6;
numeric issues → passnet-triton-opt §3.

## 3. `parse_eval_log.py` — turn an eval into decisions

```bash
python3 $SCRIPTS/parse_eval_log.py <validation.log | evaluate_response.json>
# also reads the "stdout"/"stderr" fields of a saved /evaluate JSON response
```
Prints:
- Per-variant table: dtype | status | e2e/gpu speedup | eager/compiled medians | max_diff |
  passes applied/failed.
- Failure classification with the fix pointer:
  - localhost connection failure from a Codex managed sandbox → retry normal bounded curl once, then retry through the approved escalation path if available before diagnosing service downtime.
  - empty, interrupted, HTTP000-style, status-corrupted, or non-JSON `/evaluate` response → no completed eval; leave score, speed, correctness, and pass-matched metrics null, retry service access/upload state if appropriate, and do not interpret any performance or correctness result.
  - `no pass matched` + diagnostic lines → pattern form problem (which pass, which node).
  - `AssertionError` in `_replace_pattern` → multi-output pattern (rule 1).
  - `Unauthorized Operator (aten.xxx)` → illegal torch op in wrapper (poison).
  - `Detected hacking behavior` → AST validation rejected a file (it was NOT loaded).
  - `Loaded N passes` < listed → replacement_func limit dropped passes (shared dispatch!).
  - dtype mismatch / accuracy with max_diff vs that dtype's baseline tolerance.
  - replacement crash mentioning a returning node with no users → the pattern likely matched
    userless/dead duplicate work; re-anchor the region on an observable value or use a proven
    graph-rewrite approach instead of a normal output replacement.
  - evaluator/environment fluctuation messages, timing-stability errors, or rerun requests
    with otherwise clean matching and successful-variant correctness → classify separately
    from numeric, no-match, unauthorized-operator, timeout, and OOM. If the pass pre-flights
    cleanly and successful variants are correct, an unchanged rerun can be a valid use of
    remaining evaluation budget.
  - timeout/OOM hints.
- **Estimated sample score** using the real ES(t) weights, plus per-variant rectified
  speedups — so you know the score impact of fixing each failing variant before re-running.

For round or multi-worker aggregation, keep family labels separate:

- `triage_family`: the static family assigned before implementation.
- `worker_confirmed_family`: the family the worker confirmed after reading the graph and
  pre-flight results.
- `actual_winning_region_family`: the family of the best completed-evaluation state.

Do not aggregate a win under the original triage family if the best completed state belongs
to a different region family. Round summaries should report, per family: number of completed
workers, score-above-eager count, correct-but-slow count, numeric-preflight-blocked count,
correctness-regressed-on-larger-region count, larger-region-attempted count, and evaluator
instability count. Keep evaluator/environment fluctuation separate from numeric, no-match,
unauthorized-operator, timeout, and OOM.

## 4. Reading raw logs yourself (when needed)

Key markers in `stdout`/`validation.log`:
`[PassMgrBackend] Loaded/Applied/failed to match/Diagnostic`,
`[Result] status: success|failed`, `[Speedup][e2e]/[gpu]`,
`[Performance][eager|compiled]` (medians), `[Correctness][max_diff|mean_diff|equal]`,
`[Datatype][eager|compiled]`, `debug-model-execution <ExcType>` (crash),
`Has Any pass matched? [True|False]`, `aggregated_speedup=...`.
The service strips `Trial`/`[Profiling]`/`all_close` lines; everything above survives.

## 5. Bottleneck decision guide (after analyze/eval)

| signal | diagnosis | action |
|---|---|---|
| eager e2e < 150 µs, ≤2 matchable cheap nodes | overhead-bound, ceiling < 1 | floor pass, move on |
| big gap between eager e2e and Σ(node µs) | per-call fixed costs dominate | absorb more nodes per launch; nothing else helps |
| one node ≥ 60% of eager time, matchable | real kernel target | fuse it + its neighbors; tune via passnet-triton-opt |
| a `conv` dominates AND `stride == kernel_size`, `kernel_size > 1`, `padding == 0` (non-overlapping) | disjoint windows ⇒ exactly a dense patch matmul; cuDNN pays for a general im2col path | reformulate as a `tl.dot` patch-gather kernel + fused tail (kernel-templates §13), AFTER banking a tail floor. Don't dismiss as "cuDNN, leave alone" or "unmatchable" |
| a `conv`/`matmul` dominates in any OTHER form (1×1, depthwise/grouped, overlapping conv, general dense matmul) | vendor sweet spot | default: leave it in aten; fuse its cheap tail (bias/BN/act/residual). Rewriting usually loses — try only if parameters look off-regime and a completed eval beats the floor |
| one node ≥ 60%, callable-unmatchable kwargs form | try exact manual FX if the region is single-output and valuable; otherwise fuse what's left | expectation depends on whether the exact pattern pre-flight matches |
| compiled gpu ≈ e2e, both < 1 | stream gaps (launch-bound) | fewer launches/allocs |
| compiled gpu > 1, e2e < 1 | host overhead | drop autotune churn, simplify wrapper, fewer passes |
| some dtype variants fail only | numeric fidelity | passnet-triton-opt §3 recipes |
| timeout (600 s) | too many variants × compile/tune cost | remove autotune, single config, fewer passes |
| evaluator reports timing/environment fluctuation while successful variants match and pass correctness | evaluator instability, not proven kernel bug | rerun unchanged if budget remains; record separately from numeric/no-match/unauthorized |
