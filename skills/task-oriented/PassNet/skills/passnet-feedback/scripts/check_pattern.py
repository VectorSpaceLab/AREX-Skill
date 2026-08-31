#!/usr/bin/env python3
"""Pre-flight a PassNet pass_dir without spending a GPU evaluation.

Replicates the harness pipeline: manifest -> AST validation -> pass loading ->
replacement_func stability/uniqueness -> pattern trace -> SubgraphMatcher against each
variant's real dynamo graph (+ nearest-miss diff) -> optional poisoned smoke run and
micro-benchmark.

Usage:
  python3 check_pattern.py --sample-dir <sample_root> [--pass-dir DIR] [--smoke] [--bench]
                           [--max-variants N] [--match-all]

Exit code 0 = every analyzed variant has >=1 matching pass (and smoke passed, if used).
"""
import argparse
import inspect
import importlib.util
import json
import re
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    build_inputs, capture_dynamo_graph, ensure_repo_on_path, fmt_args, force_args_trace,
    load_graph_list, load_model, pick_variants, target_name, variant_dtype,
)

import torch  # noqa: E402

GREEN, RED, YEL, END = "\033[32m", "\033[31m", "\033[33m", "\033[0m"
def ok(s): return f"{GREEN}{s}{END}"
def bad(s): return f"{RED}{s}{END}"
def warn(s): return f"{YEL}{s}{END}"

BASELINE_TOL = {  # t=-5 (rtol, atol)
    "torch.float32": (1.3e-6, 1e-5),
    "torch.float16": (1e-3, 1e-5),
    "torch.bfloat16": (1.6e-2, 1e-5),
    "torch.float64": (1e-7, 1e-7),
}


def load_manifest(pass_dir):
    mf = pass_dir / "sorted_output_pass_rule_names.json"
    issues = []
    if not mf.exists():
        return None, [bad("sorted_output_pass_rule_names.json MISSING — nothing will load")]
    try:
        names = json.loads(mf.read_text())
        assert isinstance(names, list) and all(isinstance(x, str) for x in names)
    except Exception as e:
        return None, [bad(f"manifest unreadable: {e}")]
    for n in names:
        if not (pass_dir / f"{n}.py").exists():
            issues.append(bad(f"manifest lists '{n}' but {n}.py does not exist"))
    listed = set(names)
    for f in pass_dir.glob("*.py"):
        if f.stem not in listed and not f.stem.startswith("_"):
            issues.append(warn(f"{f.name} exists but is NOT in the manifest (won't load; "
                               f"prefix helpers with '_' to silence)"))
    return names, issues


def ast_validate(pass_dir, names):
    try:
        from pass_bench.ast_util import validate_pass_source
    except ImportError:
        return {n: ["(pass_bench not importable — AST validation skipped)"] for n in names}, False
    out = {}
    for n in names:
        p = pass_dir / f"{n}.py"
        if not p.exists():
            continue
        try:
            out[n] = validate_pass_source(p.read_text())
        except SyntaxError as e:
            out[n] = [f"SyntaxError: {e}"]
    return out, True


def load_pass_modules(pass_dir, names):
    """Load pass modules like the harness (sample root on sys.path for pass_dir.* imports)."""
    sample_root = str(pass_dir.parent)
    if sample_root not in sys.path:
        sys.path.insert(0, sample_root)
    if pass_dir.name != "pass_dir":
        text = "".join((pass_dir / f"{n}.py").read_text()
                       for n in names if (pass_dir / f"{n}.py").exists())
        if "pass_dir." in text or "from pass_dir" in text:
            print(warn(f"pass dir is named '{pass_dir.name}' but passes import "
                       f"'pass_dir.*' — name the directory 'pass_dir' (e.g. "
                       f"/tmp/ws/pass_dir) or imports will fail here AND in the harness"))
    mods, errors = {}, {}
    for n in names:
        p = pass_dir / f"{n}.py"
        if not p.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location(n, p)
            m = importlib.util.module_from_spec(spec)
            m.__file__ = str(p)
            spec.loader.exec_module(m)
            for fn in ("pattern", "replacement_args", "replacement_func"):
                if not callable(getattr(m, fn, None)):
                    raise AttributeError(f"missing function {fn}()")
            mods[n] = m
        except Exception as e:
            errors[n] = f"{type(e).__name__}: {e}"
    return mods, errors


def check_replacement_funcs(mods):
    msgs, funcs = [], {}
    for n, m in mods.items():
        try:
            f1, f2 = m.replacement_func(), m.replacement_func()
            if f1 is not f2:
                msgs.append(bad(f"{n}: replacement_func() UNSTABLE (returns new object per "
                                f"call) — harness raises; return a module-level function"))
            if not callable(f1):
                msgs.append(bad(f"{n}: replacement_func() returned non-callable {f1!r}"))
            funcs[n] = f1
        except Exception as e:
            msgs.append(bad(f"{n}: replacement_func() raised {type(e).__name__}: {e}"))
    distinct = {id(f) for f in funcs.values()}
    if len(funcs) > 1 and len(distinct) > 1:
        msgs.append(bad(
            f"{len(funcs)} passes but {len(distinct)} distinct replacement functions — "
            f"output_pass_replacement_func_limit=1 will RANDOMLY DROP all but one pass. "
            f"All passes must `from pass_dir._shared_kernels import dispatch_wrapper` "
            f"and return that same object (see passnet-pattern-fusion §4)."))
    return msgs, funcs


def single_output_check(pattern_gm):
    out_node = next(n for n in pattern_gm.graph.nodes if n.op == "output")
    arg = out_node.args[0]
    if isinstance(arg, (tuple, list)):
        n_out = len(arg)
    else:
        n_out = 1
    return n_out, len(out_node.all_input_nodes)


def nearest_miss(pattern_gm, target_gm, max_lines=8):
    """Per pattern compute node, show target nodes with the same target (form diff)."""
    lines = []
    pat_nodes = [n for n in pattern_gm.graph.nodes
                 if n.op not in ("placeholder", "output")]
    tgt_nodes = [n for n in target_gm.graph.nodes
                 if n.op not in ("placeholder", "output")]
    for pn in pat_nodes:
        same = [tn for tn in tgt_nodes if tn.op == pn.op and tn.target == pn.target]
        if not same:
            kind = {"call_function": "function", "call_method": "method"}.get(pn.op, pn.op)
            others = [tn for tn in tgt_nodes
                      if target_name(tn).split(".")[-1] == target_name(pn).split(".")[-1]]
            hint = (f" — graph has same-named node as {others[0].op} "
                    f"{target_name(others[0])}{fmt_args(others[0])} (form mismatch!)"
                    if others else " — no node with this target in the graph at all")
            lines.append(f"    pattern {kind} {target_name(pn)}{fmt_args(pn)}: "
                         f"NO target-node{hint}")
        else:
            pa = fmt_args(pn)
            forms = {fmt_args(tn) for tn in same}
            if pa not in forms:
                lines.append(f"    pattern {target_name(pn)}{pa}  vs  graph "
                             f"{' | '.join(sorted(forms)[:3])}   ← arg/kwarg/literal diff")
        if len(lines) >= max_lines:
            break
    if not lines:
        lines.append("    every pattern node has a same-form twin — failure is structural: "
                      "check dataflow edges, containment (an intermediate is consumed "
                      "outside the pattern), or overlapping matches")
    return lines


def run_matcher(pattern_gm, target_gm):
    from torch.fx.passes.utils.matcher_utils import SubgraphMatcher
    m = SubgraphMatcher(pattern_gm.graph, match_output=False, match_placeholder=False,
                        remove_overlapping_matches=True, ignore_literals=False)
    return m.match(target_gm.graph)


def pattern_graph_for(pattern):
    """Mirror the harness: GraphModule/Graph patterns bypass ForceArgsTracer."""
    if isinstance(pattern, torch.fx.GraphModule):
        return pattern
    if isinstance(pattern, torch.fx.Graph):
        return torch.fx.GraphModule({}, pattern, "ManualPattern")
    return force_args_trace(pattern)


def pattern_signature_params(pattern, pattern_gm):
    """Return parameter names used by PassMgrBackend for replacement wrapper generation."""
    if isinstance(pattern, torch.fx.Graph):
        return [], [n.name for n in pattern_gm.graph.nodes if n.op == "placeholder"]
    sig = inspect.signature(pattern)
    params = list(sig.parameters)
    placeholders = [n.name for n in pattern_gm.graph.nodes if n.op == "placeholder"]
    if isinstance(pattern, (torch.fx.GraphModule, torch.fx.Graph)) and params != placeholders:
        return params, placeholders
    return params, []


def smoke_variant(rel, gdir, device, pass_dir):
    """Apply passes with the real PassMgrBackend; one poisoned call; numeric compare."""
    import pass_bench.torch.backend.pass_mgr_backend as pmb
    from pass_bench.torch.backend.pass_mgr_backend import PassMgrBackend
    from pass_bench.torch.override_dispatch_flag import global_override_dispatch
    # The harness runs each variant in a fresh subprocess; mirror that isolation for the
    # process-global replacement-function registry (each load creates new func objects).
    pmb.g_replacement_func = None
    model = load_model(gdir, device)
    inputs = build_inputs(model, gdir, device)
    backend = PassMgrBackend({
        "input_pass_rule_dir": str(Path(gdir).parents[0] / "__none__"),
        "output_pass_rule_dir": str(pass_dir),
        "output_pass_pattern_limit": 100,
        "output_pass_replacement_func_limit": 1,
        "pass_match_result_file_path": None,
    })
    import torch._dynamo as dynamo
    dynamo.reset()
    cm = backend(model)
    with torch.no_grad():
        torch.manual_seed(1024)
        with global_override_dispatch(True):   # anti-cheat warmup parity
            compiled_out = cm(*inputs)
        with global_override_dispatch(False):
            torch.manual_seed(1024)
            compiled_out = cm(*inputs)
        torch.manual_seed(1024)
        eager_out = model(*inputs)
    if not isinstance(compiled_out, tuple):
        compiled_out = (compiled_out,)
    if not isinstance(eager_out, tuple):
        eager_out = (eager_out,)
    msgs, all_ok = [], True
    for i, (e, c) in enumerate(zip(eager_out, compiled_out)):
        if not isinstance(e, torch.Tensor):
            continue
        if e.dtype != c.dtype:
            msgs.append(bad(f"out[{i}] dtype mismatch: eager {e.dtype} vs compiled {c.dtype}"))
            all_ok = False
            continue
        rtol, atol = BASELINE_TOL.get(str(e.dtype), (1e-5, 1e-6))
        close = torch.allclose(e.float(), c.float(), rtol=rtol, atol=atol)
        md = (e.float() - c.float()).abs().max().item()
        line = f"out[{i}] {str(e.dtype).replace('torch.','')} max_diff={md:.3e} baseline({rtol:g},{atol:g}) → {'OK' if close else 'FAIL'}"
        msgs.append(ok(line) if close else bad(line))
        all_ok &= close
    return all_ok, msgs, (model, cm, inputs)


def bench_pair(model, cm, inputs, iters=200):
    """Mirrors the harness model_call: manual_seed + forward + sync per trial."""
    def run(fn):
        with torch.no_grad():
            for _ in range(25):
                fn(*inputs)
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            for _ in range(iters):
                torch.manual_seed(1024)
                fn(*inputs)
                torch.cuda.synchronize()
            return (time.perf_counter() - t0) / iters * 1e6
    e, c = run(model), run(cm)
    return e, c, e / c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-dir", required=True)
    ap.add_argument("--pass-dir", default=None)
    ap.add_argument("--max-variants", type=int, default=8,
                    help="match-check this many variants, dtype-spread (default 8; "
                         "0 = all — beware samples with 100+ variants)")
    ap.add_argument("--smoke", action="store_true", help="apply passes + numeric smoke (GPU)")
    ap.add_argument("--bench", action="store_true",
                    help="micro-benchmark eager vs compiled (implies --smoke; GPU)")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()
    if args.bench:
        args.smoke = True

    sample_dir = Path(args.sample_dir).resolve()
    pass_dir = Path(args.pass_dir).resolve() if args.pass_dir else sample_dir / "pass_dir"
    repo = ensure_repo_on_path(sample_dir)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    force_dtype = None if device.startswith("cuda") else torch.float32
    failures = 0

    print(f"sample:   {sample_dir}\npass_dir: {pass_dir}\nrepo:     {repo}\ndevice:   {device}\n")

    # 1. manifest
    names, issues = load_manifest(pass_dir)
    for line in issues:
        print(line)
        if "MISSING" in line or "unreadable" in line or "does not exist" in line:
            failures += 1
    if names is None:
        sys.exit(1)
    print(f"manifest: {names}")

    # 2. AST validation
    ast_results, real_ast = ast_validate(pass_dir, names)
    for n, viols in ast_results.items():
        if viols and real_ast:
            failures += 1
            print(bad(f"AST validation FAILED for {n} (harness will SKIP this pass):"))
            for v in viols:
                print(f"    - {v}")
        elif viols:
            print(warn(f"{n}: {viols[0]}"))
        else:
            print(ok(f"AST validation OK for {n}"))

    # 3. load + replacement funcs
    mods, load_errors = load_pass_modules(pass_dir, names)
    for n, err in load_errors.items():
        failures += 1
        print(bad(f"IMPORT FAILED for {n}: {err}"))
    rf_msgs, _funcs = check_replacement_funcs(mods)
    for m in rf_msgs:
        print(m)
        failures += 1

    # 4. pattern traces
    patterns = {}
    for n, m in mods.items():
        try:
            pg = pattern_graph_for(m.pattern)
            n_out, _ = single_output_check(pg)
            if n_out != 1:
                failures += 1
                print(bad(f"{n}: pattern returns {n_out} values — harness CRASHES on "
                          f"multi-output patterns; split into {n_out} passes"))
                continue
            pat_args, placeholder_mismatch = pattern_signature_params(m.pattern, pg)
            rep_args = list(inspect.signature(m.replacement_args).parameters)
            n_pat_args = len(pat_args)
            n_rep_args = len(rep_args)
            if isinstance(m.pattern, torch.fx.Graph):
                failures += 1
                print(bad(f"{n}: bare torch.fx.Graph patterns do not expose a callable "
                          f"signature for the backend wrapper — wrap it in "
                          f"torch.fx.GraphModule and set pattern.__signature__"))
            elif placeholder_mismatch:
                failures += 1
                print(bad(f"{n}: GraphModule pattern signature {pat_args} does not match "
                          f"graph placeholders {placeholder_mismatch} — set "
                          f"pattern.__signature__ to the placeholder order"))
            if n_pat_args != n_rep_args:
                failures += 1
                print(bad(f"{n}: pattern takes {n_pat_args} args but replacement_args "
                          f"takes {n_rep_args} — must be identical"))
            patterns[n] = pg
            print(ok(f"{n}: pattern traced, single output, "
                     f"{sum(1 for x in pg.graph.nodes if x.op not in ('placeholder', 'output'))} nodes"))
        except Exception as e:
            failures += 1
            print(bad(f"{n}: pattern trace FAILED: {type(e).__name__}: {e}"))

    # 5. match per variant
    variants = load_graph_list(sample_dir)
    chosen = pick_variants(variants, args.max_variants or None)
    if len(chosen) < len(variants):
        skipped = [r for r, _ in variants if r not in {c for c, _ in chosen}]
        print(f"\n[note] match-checking {len(chosen)}/{len(variants)} variants "
              f"(--max-variants {args.max_variants}); dtype coverage guaranteed, "
              f"skipped same-dtype extras:")
        for r in skipped[:6]:
            print(f"        - {r}")
        if len(skipped) > 6:
            print(f"        ... +{len(skipped) - 6} more (pass --max-variants 0 for all)")
    print(f"\nmatching {len(patterns)} pass(es) against {len(chosen)}/{len(variants)} variants:")
    unmatched_variants = []
    target_cache = {}
    for rel, gdir in chosen:
        try:
            model = load_model(gdir, device)
            inputs = build_inputs(model, gdir, device, force_dtype)
            gm, _ = capture_dynamo_graph(model, inputs)
            target_cache[rel] = (gm, gdir)
        except Exception as e:
            print(bad(f"  {rel}: dynamo capture failed: {type(e).__name__}: {e}"))
            traceback.print_exc(limit=2)
            unmatched_variants.append(rel)
            continue
        any_match = False
        per = []
        for n, pg in patterns.items():
            try:
                ms = run_matcher(pg, gm)
            except Exception as e:
                per.append(f"{n}: matcher error {e}")
                continue
            per.append(f"{n}: {len(ms)}")
            any_match |= bool(ms)
        status = ok("MATCH") if any_match else bad("NO MATCH → variant would score 0.1")
        seed_m = re.search(r"/(float\d+|bfloat16)/(\w+)/", rel)
        vtag = f"{seed_m.group(1)}/{seed_m.group(2)}" if seed_m else variant_dtype(rel)
        print(f"  [{vtag:12}] {rel.split('/')[-1][:44]:44} {status}   ({', '.join(per)})")
        if not any_match:
            unmatched_variants.append(rel)
            for n, pg in patterns.items():
                print(f"   nearest-miss for {n}:")
                for line in nearest_miss(pg, gm):
                    print(line)

    if unmatched_variants:
        failures += len(unmatched_variants)

    # 6. smoke
    if args.smoke and patterns and not unmatched_variants:
        if not device.startswith("cuda"):
            print(warn("\n--smoke needs CUDA; skipped"))
        elif repo is None:
            print(warn("\n--smoke needs pass_bench importable; skipped"))
        else:
            print("\nsmoke (real PassMgrBackend, poisoned warmup, numeric compare):")
            seen_dtypes = set()
            for rel, gdir in chosen:
                dt = variant_dtype(rel)
                if dt in seen_dtypes:
                    continue
                seen_dtypes.add(dt)
                try:
                    good, msgs, trio = smoke_variant(rel, gdir, device, pass_dir)
                    for m in msgs:
                        print(f"  [{dt:8}] {m}")
                    if not good:
                        failures += 1
                    elif args.bench:
                        e, c, s = bench_pair(*trio)
                        line = (f"  [{dt:8}] micro-bench eager {e:.1f}µs vs compiled {c:.1f}µs "
                                f"→ ~{s:.2f}x (full eval adds guard overhead)")
                        print(ok(line) if s >= 1 else warn(line))
                except Exception as e:
                    failures += 1
                    print(bad(f"  [{dt:8}] smoke CRASHED: {type(e).__name__}: {e}"))
                    tb = traceback.format_exc()
                    if "Unauthorized Operator" in tb:
                        print(bad("      → poison dispatch: an illegal aten op runs inside "
                                  "your wrapper (only empty/zeros/ones/full/as_tensor/.to "
                                  "+ metadata are allowed; do ALL math in Triton)"))
                    else:
                        print("      " + tb.strip().splitlines()[-1])

    print()
    if failures == 0:
        print(ok(f"PRE-FLIGHT GREEN — safe to spend a GPU evaluation."))
    else:
        print(bad(f"PRE-FLIGHT: {failures} blocking issue(s) — fix before evaluating."))
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
