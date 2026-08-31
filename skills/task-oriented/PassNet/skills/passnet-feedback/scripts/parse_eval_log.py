#!/usr/bin/env python3
"""Parse a PassNet evaluation output into per-variant results, failure classification,
and an estimated sample score.

Accepts: a raw validation.log, a pass_evaluator stdout capture, or a saved JSON response
from POST /evaluate (uses its "stdout"+"stderr" fields and reports its "score").

Usage: python3 parse_eval_log.py <file> [--sample-dir DIR]
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ensure_repo_on_path  # noqa: E402

BASELINE_TOL = {
    "float32": (1.3e-6, 1e-5),
    "float16": (1e-3, 1e-5),
    "bfloat16": (1.6e-2, 1e-5),
    "float64": (1e-7, 1e-7),
}
# weights from aggregate_es_scores.get_weights()
WEIGHTS = {-10: 0.001, -9: 0.001, -8: 0.001, -7: 0.001, -6: 0.001, -5: 1.0, -4: 1.0,
           -3: 1.0, -2: 0.8, -1: 0.64, 0: 0.512, 1: 0.4096, 2: 0.32768, 3: 0.262144,
           4: 0.001}
WSUM = sum(WEIGHTS.values())


def read_text(path):
    raw = Path(path).read_text(errors="ignore")
    score = None
    stripped = raw.lstrip()
    if stripped.startswith("{"):
        try:
            j = json.loads(raw)
            txt = (j.get("stdout", "") or "") + "\n" + (j.get("stderr", "") or "")
            score = j.get("score")
            if j.get("error"):
                txt += f"\n[service-error] {j['error']}"
            return txt, score, j
        except json.JSONDecodeError:
            pass
    return raw, score, None


def split_per_variant(text):
    blocks, cur = [], []
    for line in text.splitlines():
        if "[Processing]" in line:
            if cur:
                blocks.append(cur)
            cur = [line]
        elif cur:
            cur.append(line)
    if cur:
        blocks.append(cur)
    return blocks


F_SPEED = re.compile(r"\[Speedup\]\[(\w+)\]: ([\d.eE+-]+)")
F_PERF = re.compile(r"\[Performance\]\[(\w+)\]: (\{.*\})")
F_MAXD = re.compile(r"\[Correctness\]\[max_diff\]: (.+)")
F_DTYPE = re.compile(r"\[Datatype\]\[(\w+)\]: (.+)")
F_RESULT = re.compile(r"\[Result\] status: (\w+)")
F_APPLIED = re.compile(r"Applied (\d+) replacements with (\w+)")
F_FAILMATCH = re.compile(r"Pass (\w+) failed to match")
F_ALLCLOSE = re.compile(r"\[Correctness\]\[all_close_atol_([\d.E+-]+)_rtol_([\d.E+-]+)\]: (.+)")


def parse_block(lines):
    d = {"path": lines[0].split()[-1], "speed": {}, "applied": [], "failed_match": [],
         "max_diff": None, "dtype": None, "status": None, "errors": [], "allclose": {},
         "eager_med": None, "compiled_med": None, "diag": []}
    for ln in lines:
        if m := F_SPEED.search(ln):
            d["speed"][m.group(1)] = float(m.group(2))
        elif m := F_PERF.search(ln):
            try:
                d[f"{m.group(1)}_med"] = json.loads(m.group(2))["e2e"]["median"]
            except Exception:
                pass
        elif m := F_MAXD.search(ln):
            d["max_diff"] = [float(x) for x in m.group(1).split()]
        elif m := F_DTYPE.search(ln):
            if m.group(1) == "eager":
                d["dtype"] = m.group(2).split()[0]
        elif m := F_RESULT.search(ln):
            d["status"] = m.group(1)
        elif m := F_APPLIED.search(ln):
            d["applied"].append((m.group(2), int(m.group(1))))
        elif m := F_FAILMATCH.search(ln):
            d["failed_match"].append(m.group(1))
        elif m := F_ALLCLOSE.search(ln):
            vals = m.group(3).split()
            d["allclose"][(float(m.group(1)), float(m.group(2)))] = all(v == "1" for v in vals)
        elif "Unauthorized Operator" in ln:
            d["errors"].append("poison: illegal aten op in wrapper")
        elif "Detected hacking behavior" in ln:
            d["errors"].append("AST validation rejected a pass file (not loaded)")
        elif "No passes modified the graph" in ln:
            d["errors"].append("no pass matched this variant")
        elif "AssertionError" in ln and "custom_replacement" in "".join(lines):
            d["errors"].append("harness assert — likely multi-output pattern")
        elif "CUDA out of memory" in ln:
            d["errors"].append("OOM")
        elif "illegal memory access" in ln.lower():
            d["errors"].append("CUDA illegal memory access (kernel indexing bug)")
        elif "debug-model-execution" in ln:
            d["errors"].append(f"crash: {ln.split()[1]}")
        elif "Diagnostic for" in ln or re.match(r"\s+- MatchFailure", ln):
            d["diag"].append(ln.strip())
        elif m := re.search(r"Loaded (\d+) passes: (\[.*\])", ln):
            d["loaded"] = (int(m.group(1)), m.group(2))
    return d


def baseline_correct(d):
    """correct at t=-5 from allclose keys (unfiltered logs) or heuristics."""
    if d["status"] != "success":
        return False, "exec-failed"
    dt = (d["dtype"] or "").replace("torch.", "")
    rtol, atol = BASELINE_TOL.get(dt, (1e-5, 1e-6))
    for (a, r), is_ok in d["allclose"].items():
        if math.isclose(a, atol, rel_tol=0.01) and math.isclose(r, rtol, rel_tol=0.01):
            return is_ok, "exact"
    if d["max_diff"] is not None:  # filtered log: heuristic
        md = max(d["max_diff"])
        if md == 0.0:
            return True, "max_diff=0"
        return md <= atol, f"heuristic(max_diff={md:.2e} vs atol={atol:g}; verify)"
    return True, "assumed(status=success)"


def estimate_score(blocks):
    """ES(t)-weighted estimate. Failure→0.1; accuracy-failure tolerated at t>=1."""
    per_t = {}
    for t in WEIGHTS:
        vals = []
        for d in blocks:
            okv, _ = baseline_correct(d)
            s = d["speed"].get("e2e")
            if d["status"] == "success" and okv and s:
                vals.append(s)          # approximation: correct@-5 ⇒ correct for t≥-5
                if t < -5:
                    # strict levels usually fail unless bit-exact
                    md = max(d["max_diff"]) if d["max_diff"] else 1.0
                    vals[-1] = s if md == 0.0 else 0.1
            else:
                tolerated = (t >= 1 and d["status"] == "success") or t >= 3
                vals.append(1.0 if tolerated else 0.1)
        if vals:
            per_t[t] = math.exp(sum(math.log(max(v, 1e-10)) for v in vals) / len(vals))
    if not per_t:
        return None
    logscore = sum(WEIGHTS[t] * math.log10(per_t[t]) for t in per_t) / WSUM
    return 10 ** logscore


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logfile")
    ap.add_argument("--sample-dir", default=None, help="for repo autodetection")
    args = ap.parse_args()
    ensure_repo_on_path(args.sample_dir)

    text, svc_score, svc_json = read_text(args.logfile)
    blocks = [parse_block(b) for b in split_per_variant(text)]
    if not blocks:
        print("no [Processing] blocks found — the run died before evaluating any variant.")
        if "No replacement functions available after filtering 0 rules" in text:
            print("cause: pass_dir effectively EMPTY — no pass loaded (missing manifest, "
                  "AST-rejected files, or no .py files). Sample scores 0.1. "
                  "Run check_pattern.py to see why each pass was dropped.")
        elif "failed to match" in text or "No passes modified the graph" in text:
            print("cause: pass(es) loaded but matched NOTHING. Diagnostic lines:")
            for ln in text.splitlines():
                if "failed to match" in ln or "Diagnostic" in ln or "MatchFailure" in ln:
                    print(f"  {ln.strip()}")
            print("→ run check_pattern.py for nearest-miss diffs "
                  "(passnet-pattern-fusion §7).")
        elif "Detected hacking behavior" in text:
            print("cause: AST validation rejected your pass file(s) — see "
                  "passnet-pattern-fusion §2 rule 9.")
        elif "ModuleNotFoundError" in text or "ImportError" in text:
            print("cause: a pass file failed to import:")
            for ln in text.splitlines():
                if "Error" in ln:
                    print(f"  {ln.strip()}")
                    break
        elif "timed out" in text.lower():
            print("cause: evaluation timeout (600 s) — too many variants × compile cost; "
                  "remove autotune, reduce pass count.")
        if svc_json is not None:
            print(f"service fields: returncode={svc_json.get('returncode')} "
                  f"pass_matched={svc_json.get('pass_matched')} score={svc_score} "
                  f"error={svc_json.get('error')!r}")
        sys.exit(1)

    print(f"{'dtype':9} {'status':9} {'e2e':>6} {'gpu':>6} {'eager':>8} {'comp':>8} "
          f"{'max_diff':>10} {'corr@-5':14} notes")
    n_corr = 0
    speeds = []
    for d in blocks:
        okv, how = baseline_correct(d)
        n_corr += okv
        dt = (d["dtype"] or "?").replace("torch.", "")
        s_e2e = d["speed"].get("e2e")
        if okv and s_e2e:
            speeds.append(s_e2e)
        notes = []
        if d["failed_match"]:
            notes.append(f"no-match:{','.join(d['failed_match'])}")
        if d["applied"]:
            notes.append("applied:" + ",".join(f"{n}×{c}" for n, c in d["applied"]))
        notes += d["errors"][:2]
        print(f"{dt:9} {(d['status'] or 'crash'):9} "
              f"{s_e2e or float('nan'):6.3f} {d['speed'].get('gpu', float('nan')):6.3f} "
              f"{(d.get('eager_med') or float('nan')) * 1000:8.1f} "
              f"{(d.get('compiled_med') or float('nan')) * 1000:8.1f} "
              f"{(max(d['max_diff']) if d['max_diff'] else float('nan')):10.2e} "
              f"{('OK(' + how + ')' if okv else 'FAIL(' + how + ')'):14.14} "
              f"{'; '.join(notes)}")
        for ln in d["diag"][:4]:
            print(f"          diag: {ln}")

    print(f"\nvariants: {len(blocks)}  correct@baseline: {n_corr}/{len(blocks)}")
    if speeds:
        gm = math.exp(sum(math.log(s) for s in speeds) / len(speeds))
        print(f"gmean e2e speedup over correct variants: {gm:.3f}  "
              f"fast_1: {sum(s >= 1 for s in speeds)}/{len(speeds)}")
    m = re.search(r"aggregated_speedup=([\d.eE+-]+)", text)
    if m:
        print(f"authoritative aggregated score (from log): {float(m.group(1)):.4f}")
    elif svc_score is not None:
        sc = svc_score.get("score") if isinstance(svc_score, dict) else svc_score
        print(f"authoritative score (service): {sc}")
    est = estimate_score(blocks)
    if est is not None:
        print(f"estimated sample score (ES-weighted): {est:.4f}")
        # impact preview: each failing variant fixed to speedup 1.0
        fails = [i for i, d in enumerate(blocks)
                 if not baseline_correct(d)[0] or not d["speed"].get("e2e")]
        if fails:
            import copy
            fixed_blocks = copy.deepcopy(blocks)
            for i in fails:
                fixed_blocks[i]["status"] = "success"
                fixed_blocks[i]["speed"]["e2e"] = 1.0
                fixed_blocks[i]["max_diff"] = [0.0]
            est2 = estimate_score(fixed_blocks)
            print(f"if the {len(fails)} failing variant(s) were fixed to 1.0x: ≈{est2:.4f} "
                  f"(+{est2 - est:.4f}) ← prioritize fixing failures over tuning winners")


if __name__ == "__main__":
    main()
