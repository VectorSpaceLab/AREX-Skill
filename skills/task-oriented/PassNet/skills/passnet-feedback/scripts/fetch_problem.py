#!/usr/bin/env python3
"""Materialize a service-mode PassNet problem into a local directory so that
analyze_graph.py / check_pattern.py can run on it.

Usage:
  python3 fetch_problem.py --svc http://127.0.0.1:8765 --sample <sample_path> --out /tmp/ws
  python3 fetch_problem.py --svc ... --out /tmp/ws            # API-server mode (no --sample)

Creates: <out>/graph_list.txt, <out>/graphs/.../{model.py,weight_meta.py}, <out>/pass_dir/
Then author passes in <out>/pass_dir, pre-flight with check_pattern.py --sample-dir <out>,
and POST the files to the service when green.
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svc", required=True)
    ap.add_argument("--sample", default=None, help="sample_path (service mode)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    q = f"?sample_path={urllib.parse.quote(args.sample, safe='')}" if args.sample else ""
    prob = get(f"{args.svc}/problem{q}")

    out = Path(args.out)
    (out / "pass_dir").mkdir(parents=True, exist_ok=True)
    (out / "graph_list.txt").write_text("\n".join(prob["graph_list"]) + "\n")
    for g in prob["graphs"]:
        gdir = out / g["name"]
        gdir.mkdir(parents=True, exist_ok=True)
        (gdir / "model.py").write_text(g.get("model_code") or "")
        (gdir / "weight_meta.py").write_text(g.get("weight_meta") or "")
    print(f"materialized {len(prob['graphs'])} graphs under {out}")
    print(f"next: python3 analyze_graph.py --sample-dir {out}")


if __name__ == "__main__":
    main()
