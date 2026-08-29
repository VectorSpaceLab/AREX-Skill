#!/usr/bin/env python3
"""Analyze a PassNet sample: dynamo graph per variant, per-node matchability,
optional per-node eager timings (--bench), and fusion-region suggestions.

Usage:
  python3 analyze_graph.py --sample-dir <sample_root> [--bench] [--max-variants 3]
  python3 analyze_graph.py --sample-dir <materialized_dir_from_fetch_problem> ...
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    build_inputs, capture_dynamo_graph, classify_matchability, ensure_repo_on_path,
    fmt_args, is_rng_node, load_graph_list, load_model, pick_variants, shape_of,
    target_name, variant_dtype,
)

import torch  # noqa: E402


class NodeTimer(torch.fx.Interpreter):
    """Times each node with CUDA events over `reps` replays.

    Subtracts the measurement floor (sync + event overhead, measured on an empty loop)
    from host times so Σ(node µs) approximates real absorbable time.
    """

    def __init__(self, gm, reps=30):
        super().__init__(gm)
        self.reps = reps
        self.times = {}
        self.floor_us = self._measure_floor() if torch.cuda.is_available() else 0.0

    def _measure_floor(self):
        start, end = torch.cuda.Event(True), torch.cuda.Event(True)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        start.record()
        for _ in range(self.reps):
            pass
        end.record()
        torch.cuda.synchronize()
        return (time.perf_counter() - t0) / self.reps * 1e6

    def run_node(self, n):
        if n.op in ("placeholder", "output", "get_attr") or not torch.cuda.is_available():
            return super().run_node(n)
        # warmup once
        result = super().run_node(n)
        start, end = torch.cuda.Event(True), torch.cuda.Event(True)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        start.record()
        for _ in range(self.reps):
            super().run_node(n)
        end.record()
        torch.cuda.synchronize()
        host_us = (time.perf_counter() - t0) / self.reps * 1e6
        gpu_us = start.elapsed_time(end) * 1000 / self.reps
        host_us = max(host_us - self.floor_us, gpu_us, 0.5)
        self.times[n] = (host_us, gpu_us)
        return result


def bench_eager_e2e(model, inputs, iters=200):
    """Mirrors the harness model_call: manual_seed + forward + sync per trial."""
    with torch.no_grad():
        for _ in range(25):
            model(*inputs)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(iters):
            torch.manual_seed(1024)
            model(*inputs)
            torch.cuda.synchronize()
        return (time.perf_counter() - t0) / iters * 1e6


def suggest_regions(gm, matchable_map, times):
    """Connected components of matchable compute nodes (dataflow edges)."""
    nodes = [n for n in gm.graph.nodes if matchable_map.get(n) and not is_rng_node(n)]
    nodeset = set(nodes)
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] is not x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra is not rb:
            parent[ra] = rb

    for n in nodes:
        for a in n.all_input_nodes:
            if a in nodeset:
                union(n, a)
    comps = {}
    for n in nodes:
        comps.setdefault(find(n), []).append(n)
    regions = []
    for comp in comps.values():
        comp_set = set(comp)
        outputs = [n for n in comp if any(u not in comp_set for u in n.users)]
        total_us = sum(times.get(n, (0, 0))[0] for n in comp) if times else None
        regions.append({"nodes": comp, "outputs": outputs, "us": total_us})
    regions.sort(key=lambda r: -(r["us"] or len(r["nodes"])))
    return regions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-dir", required=True)
    ap.add_argument("--bench", action="store_true", help="per-node eager timings (GPU)")
    ap.add_argument("--max-variants", type=int, default=3)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    ensure_repo_on_path(args.sample_dir)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    force_dtype = None if device.startswith("cuda") else torch.float32
    if args.bench and not device.startswith("cuda"):
        print("[warn] --bench needs CUDA; continuing without timings")
        args.bench = False

    variants = load_graph_list(args.sample_dir)
    print(f"sample: {args.sample_dir}")
    print(f"variants: {len(variants)} "
          f"({', '.join(sorted({variant_dtype(r) for r, _ in variants}))}); "
          f"analyzing {min(args.max_variants, len(variants))} on {device}\n")

    for rel, gdir in pick_variants(variants, args.max_variants):
        print("=" * 100)
        print(f"variant: {rel}")
        try:
            model = load_model(gdir, device)
            inputs = build_inputs(model, gdir, device, force_dtype)
            gm, gm_inputs = capture_dynamo_graph(model, inputs)
        except Exception as e:
            print(f"  [ERROR] could not capture graph: {type(e).__name__}: {e}")
            continue

        # NB: gm placeholders follow dynamo's order — always feed gm with gm_inputs,
        # never with the forward-signature-ordered `inputs`.
        try:
            from torch.fx.passes.shape_prop import ShapeProp
            ShapeProp(gm).propagate(*gm_inputs)
        except Exception:
            pass

        times = {}
        eager_e2e = None
        if args.bench:
            try:
                timer = NodeTimer(gm)
                with torch.no_grad():
                    timer.run(*gm_inputs)
                times = timer.times
                eager_e2e = bench_eager_e2e(model, inputs)
            except Exception as e:
                print(f"  [warn] bench failed: {type(e).__name__}: {e}")

        matchable_map = {}
        print(f"{'#':>3} {'kind':13} {'target':26} {'written form':44} "
              f"{'out shape':24} {'match?':7} {'µs':>8}")
        idx = 0
        for n in gm.graph.nodes:
            if n.op in ("placeholder", "output"):
                continue
            tag, ok, note = classify_matchability(n)
            rng = is_rng_node(n)
            matchable_map[n] = bool(ok) and not rng
            us = f"{times[n][0]:8.1f}" if n in times else ""
            flag = ("RNG!" if rng else ("yes" if ok else ("NO" if ok is False else "?")))
            print(f"{idx:>3} {n.op:13} {target_name(n):26} {fmt_args(n):44.44} "
                  f"{shape_of(n):24.24} {flag:7} {us}")
            if ok is False or rng:
                print(f"      └─ {('RNG op — never include in a pattern' if rng else note)}")
            idx += 1

        if eager_e2e is not None:
            node_sum = sum(t[0] for t in times.values())
            print(f"\n  eager e2e ≈ {eager_e2e:.1f} µs/call (incl. the harness's per-call "
                  f"manual_seed+sync ≈60µs)   Σ per-node µs ≈ {node_sum:.1f} "
                  f"(upper bound on absorbable; per-node timing adds sync overhead)")

        regions = suggest_regions(gm, matchable_map, times)
        if regions:
            print("\n  candidate fusion regions (matchable connected components):")
            for i, r in enumerate(regions):
                names = " → ".join(target_name(n) for n in r["nodes"][:8])
                more = "" if len(r["nodes"]) <= 8 else f" (+{len(r['nodes']) - 8} more)"
                us = f", ≈{r['us']:.0f} µs absorbable" if r["us"] else ""
                multi = ("  [!] region has ≥2 external outputs — split into one pass per output"
                         if len(r["outputs"]) > 1 else "")
                print(f"   R{i}: {len(r['nodes'])} nodes{us}: {names}{more}{multi}")
            if eager_e2e is not None:
                absorbable = sum(r["us"] or 0 for r in regions)
                tax = 70.0   # guards+FX+wrapper+launch, calibrated on real evals
                # assume a good fused kernel costs ~30% of the absorbed eager time
                denom = max(eager_e2e - absorbable, 0.0) + tax + 0.30 * absorbable
                ceiling = eager_e2e / denom
                if ceiling < 1.05:
                    verdict = ("overhead-bound: ceiling < 1 — ship a floor pass, "
                               "don't chase >1")
                elif ceiling < 1.2:
                    verdict = (f"marginal (rough ceiling ≈ {ceiling:.2f}x): expect ≈1.0; "
                               f"fuse the largest region, accept the result either way")
                else:
                    verdict = f"fusible: rough ceiling ≈ {ceiling:.2f}x"
                print(f"\n  verdict: {verdict}")
        else:
            print("\n  [!] no matchable compute nodes — only floor options are get_attr/"
                  "layout nodes; expect ≤1.0 and prioritize ANY match over speedup")
        print()


if __name__ == "__main__":
    main()
