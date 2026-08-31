# PassBench harness internals — verified mechanics

Everything below was verified against `pass_bench/` source and live runs. File pointers use
repo-relative paths.

## 1. Evaluation pipeline (`entry.sh` → `pass_bench.torch.test_compiler`)

Per graph variant (each runs in a FRESH subprocess):
1. `model.py` is loaded; inputs are replayed from `weight_meta.py` (see §6).
2. `torch.compile(model, backend=PassMgrBackend)` traces the model with dynamo → an FX
   graph in **torch IR** (the ops exactly as written in `model.py` source — not aten IR).
3. `PassMgrBackend` loads pass files from `pass_dir/` in the order given by
   `sorted_output_pass_rule_names.json`, applies each as a pattern-replacement pass.
   If NO pass modifies the graph → RuntimeError → that variant scores 0.1 and the whole
   sample early-exits ("Pass testing early exits on pass mismatch").
4. **Warmup 25 calls with anti-cheat poison ON** (§4), untimed.
5. **100 timed trials with poison OFF**: per-trial `e2e` (host wall clock) and `gpu`
   (cuda events) times; medians reported. Eager model measured the same way.
   Note: each call is preceded by `torch.manual_seed(1024)` — RNG ops are reproducible
   but consume the RNG stream; do not change how many RNG ops execute.
6. Correctness: `torch.allclose` sweep over tolerance levels + dtype equality of outputs
   (`[Datatype]` lines) + `torch.equal`. `[Result] status: success|failed`.
7. `aggregate_es_scores.py` computes the sample score from the log.

Config used by `entry.sh`:
`output_pass_pattern_limit: 100`, **`output_pass_replacement_func_limit: 1`** (critical, §3),
warmup 25, trials 100, `--device cuda`.

## 2. Scoring math (`pass_bench/analysis_util.py::calculate_scores` + `aggregate_es_scores.py`)

- Speedup used: **`[Speedup][e2e]` = eager_e2e_median / compiled_e2e_median**.
- Tolerance level `t` maps to `(rtol, atol)` per dtype
  (`datatype_tolerance_config.py::get_precision`): `rtol = 10^(t·k)` with k =
  {fp16: 0.6, bf16: 0.3592, fp32: 1.1772}; `atol = 10^t`. The **baseline** is `t = -5`:
  | dtype | rtol | atol |
  |---|---|---|
  | float32 | 1.3e-6 | 1e-5 |
  | float16 | 1.0e-3 | 1e-5 |
  | bfloat16 | 1.6e-2 | 1e-5 |
- Per variant per `t`: correct → rectified speedup `s` (p=0 ⇒ no slowdown squaring);
  failed → `0.1`; at `t ≥ 1` failures get "tolerated" (accuracy at t≥1, runtime/compile at
  t≥3 → value 1).
- ES(t) = geometric mean of rectified speedups over all variants in the sample.
- Final = `10^(Σ w_t·log10 ES(t))` with normalized weights
  `{-10..-6: 0.001 each, -5: 1, -4: 1, -3: 1, -2: 0.8, -1: 0.64, 0: 0.512, 1: 0.4096,
  2: 0.32768, 3: 0.262144, 4: 0.001}`.
- Net effect: **correct at t=-5 with speedup s ⇒ sample ≈ 0.998·s** (strict t≤-6 levels are
  ~weightless). Matched-but-wrong ⇒ ≈ 0.147. No match / crash ⇒ 0.1.

## 3. PassMgrBackend mechanics (`pass_bench/torch/backend/pass_mgr_backend.py`)

- Pattern and replacement are traced with `ForceArgsTracer`
  (`custom_replacement.py`): for `call_function` nodes whose target has an
  `inspect.signature` that binds, args are rewritten to FULL POSITIONAL with defaults
  filled, kwargs emptied. `call_method` nodes and C-bound functions (no signature) keep
  exactly the written form. The TARGET graph (from dynamo) is NOT normalized → the
  matchability taxonomy in passnet-pattern-fusion.
- Matching: `SubgraphMatcher` with `match_output=False, match_placeholder=False,
  remove_overlapping_matches=True, ignore_literals=False`.
  - Literals must be EXACTLY equal (eps, dims, shapes...).
  - Pattern placeholders are wildcards (match any producer).
  - Containment: every internal pattern node's users must be inside the match; an
    intermediate consumed elsewhere in the graph (or returned by the model) cannot be
    internal to your pattern.
- **A pattern must have exactly ONE returning value.** The harness builds the replacement
  as a single opaque call node; `_replace_pattern` asserts
  `len(match.returning_nodes) == len(copied_returning_nodes)` — a pattern returning
  2+ values CRASHES the run (AssertionError → variant fails). `return out` and
  `return (out,)` are both fine (1 returning node).
- Replacement wiring: the harness wraps your pass as
  `replacement(*pattern_args) = with_dispatch_wrapper_run(*replacement_args(*pattern_args))`.
  `replacement_args` IS traced with FX proxies — it must be a pure argument shuffle
  (reorder/drop/append constants like a route string; no tensor math, no `.shape` access).
- `replacement_func()` is called MULTIPLE times and must return the SAME module-level
  function object each call (no lambdas/closures) — verified by `f() is f()`.
- **Global single replacement function**: there is ONE process-global
  `g_replacement_func`; `set_g_replacement_func` asserts all passes share it, and
  `output_pass_replacement_func_limit: 1` silently DROPS passes whose
  `replacement_func()` differs from the (randomly) chosen one. Therefore with ≥2 pass
  files, every pass must `from pass_dir._shared_kernels import dispatch_wrapper` and
  return that same object; per-pass behaviour is selected by a constant route string
  appended in `replacement_args`. (`sys.path` contains the sample root during pass
  loading, so `pass_dir.xxx` imports work; no `__init__.py` needed.)
- Check the log line `[PassMgrBackend] Loaded N passes: [...]` — if N < your file count,
  passes were dropped (validation failure or replacement-func limit).
- A pass listed in the JSON but failing AST validation is skipped with
  "Detected hacking behavior ... Skipping loading".

## 4. Anti-cheat (two layers — do not fight them, design within them)

**Layer 1 — AST validation** (`pass_bench/ast_util/validate_pass_source.py`), applied to
every file listed in `sorted_output_pass_rule_names.json`:
- Blocked imports ANYWHERE in the file: `torch.nn`, `torch.nn.functional`, `torch.ops`,
  `torch.autograd` (including `F = torch.nn.functional` alias assignments). Inside
  `pattern()` use full dotted names: `torch.nn.functional.relu(...)`.
- In all code EXCEPT the bodies of `pattern` and `replacement_args`: any call resolving to
  `torch.*` is blocked except `torch.empty, torch.empty_like, torch.zeros,
  torch.zeros_like, torch.ones, torch.ones_like, torch.full, torch.full_like,
  torch.as_tensor`. Tensor METHOD calls pass the AST check but are stopped by layer 2.
- A custom checker hook (`PASSNET_CUSTOM_PASS_SOURCE_CHECKER_PATH`) may add stricter rules
  on the leaderboard. Keep helper modules (e.g. `_shared_kernels.py`) clean too, even
  though the loader currently only validates listed pass files.

**Layer 2 — Poison dispatch** (`posion_dispatch_tensor.py`): during the 25 warmup calls,
your wrapper receives `PosionDispatchTensor` args. Allowed on them: the factory ops above,
`.to()` (`aten._to_copy`), `torch.as_tensor`, and metadata (`.shape`, `.stride()`,
`.numel()`, `.dim()`, `.device`, `.dtype`, `.data_ptr()`). EVERY other aten op
(`.contiguous()`, `.view()`, `+`, `.relu()`, `torch.matmul`...) raises
"Unauthorized Operator" → the variant fails. Triton kernel launches work (they only read
`.data_ptr()` and metadata). Timed trials run unpoisoned, but a wrapper that only works
unpoisoned never survives warmup.

Consequences:
- ALL math happens inside `@triton.jit` kernels.
- You cannot `.contiguous()` inputs — pass strides into the kernel instead.
- Allocate outputs with `torch.empty(...)`/`torch.empty_like(...)`.
- `x.to(dtype)` is legal if you must unify dtypes (it costs a copy).

**Known-cheat patterns that MUST NOT be used** (they appear in some legacy passes; they are
detected as hacking and/or are slower than eager anyway): `getattr(torch, "conv2d")`
laundering, `torch.utils._mode_utils.no_dispatch()`, monkeypatching harness modules,
writing to harness state, returning cached eager results.

## 5. Timing/overhead facts (measured, A100, torch 2.7.1, triton 3.3.1)

| item | cost |
|---|---|
| Triton `kernel[grid](...)` Python launch | ~19 µs/call |
| aten elementwise op (e.g. relu) e2e | ~8 µs |
| aten batch_norm (eval mode) e2e | ~24 µs |
| `torch.empty_like` | ~2.5 µs |
| compiled-vs-eager fixed tax (guards+FX+wrapper+launch) | ~40–70 µs/call |

Implication: replacing ONE cheap op loses (measured 0.77× on a 3-op graph); win by
absorbing MANY ops per launch or replacing genuinely expensive regions. On large tensors
(ms-scale kernels) the tax is negligible and kernel quality dominates.

## 6. Input replay (`pass_bench/torch/utils.py::replay_tensor`)

For each entry in `weight_meta.py`: if `data` present → exact values; else
`randn(shape)·std·0.2 + mean` (std=0 → constant tensor), clamped to `[min_val, max_val]`
if given, non-finite→small noise, clamped to [-100, 100], then `.to(dtype).to(device)`.
Inputs are CONTIGUOUS, freshly replayed; `device` in meta may say `cpu` but everything is
moved to cuda. Model is called with inputs bound by forward-signature parameter NAMES.
Use mean/std/min_val to reason about numerics (e.g. running_var ≥ 0, masks are 0/1).

## 7. Evaluation modes (how to read/write/evaluate)

**Local mode** (you are in a sample dir; no HTTP service):
```bash
ls graph_list.txt pass_dir/ && bash entry.sh   # full eval; log + score under $PASSNET_EVAL_OUTPUT (default /tmp/workspace_pass_bench_test)
```

**Sample Access Service mode** (`/health` returns `"mode": "sample_access_service"`),
multi-tenant; `SVC` and `SAMPLE` are given in your task prompt; every request needs
`?sample_path=$SAMPLE`:
```bash
curl -s "$SVC/problem?sample_path=$SAMPLE"            # graph_list + model_code + weight_meta per graph
curl -s "$SVC/files?sample_path=$SAMPLE"              # list pass_dir files
curl -s "$SVC/files/X.py?sample_path=$SAMPLE"         # read
python3 -c 'import json,sys; print(json.dumps(dict(content=sys.stdin.read())))' < local/X.py | \
  curl -s -X POST "$SVC/files/X.py?sample_path=$SAMPLE" -H 'Content-Type: application/json' -d @-
curl -s -X DELETE "$SVC/files/X.py?sample_path=$SAMPLE"
curl -s -X POST "$SVC/evaluate" -H 'Content-Type: application/json' \
  -d "{\"sample_path\":\"$SAMPLE\"}" --max-time 610    # {"returncode","pass_matched","score","stdout","stderr"}
```
Only `pass_dir/*.py|*.json` are writable; 503 = GPU busy → wait 15 s, retry (≤5×);
eval timeout 600 s. The returned `stdout` is pre-filtered (Trial/allclose lines removed) —
save it to a file and run `parse_eval_log.py` on it.

**API-server mode** (single-sample server): same endpoints WITHOUT `sample_path`
(`/problem`, `/files/...`, `POST /evaluate`).

## 8. Misc facts that bite

- `model.py` lines like `tmp_4 = None` are refcount hints, NOT graph nodes — never put
  them in a pattern.
- A sample's `graph_list.txt` typically holds 2–10 variants but can hold 100+; eval time
  and timeout risk scale with it.
- The eager model output dtype must equal yours exactly (`[Datatype]` check) — store in
  the input/output dtype, never leave fp32 results when eager returns fp16.
- The same pass set runs against ALL variants; per-variant "pass A matches, pass B
  doesn't" is fine as long as ≥1 pass matches per variant (each variant only needs the
  graph to be modified by at least one pass).
- Subprocess-per-variant means module-level state in your pass file does NOT persist
  across variants.
- `aggregated_score.json` is written per run; the service `score` field echoes it
  (averaged over `num_runs` when the service evaluates multiple times).
