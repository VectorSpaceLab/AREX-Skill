#!/usr/bin/env python3
import argparse, json
from pathlib import Path

REQUIRED = ["fid_statistics_computed", "frechet_distance_computed", "fid_disturbance_monotonic", "ttur_separate_rates", "optimizer_step_executed"]

def check_result(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    checks = data.get("mechanism_checks", {})
    missing = [key for key in REQUIRED if checks.get(key) is not True]
    metric = data.get("metrics", {}).get("fid_monotonicity_and_ttur_loss_drop")
    ok = not missing and metric == 1.0 and data.get("is_proxy") is True
    return {"ok": ok, "missing_checks": missing, "metric": metric}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recovery_result")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = check_result(args.recovery_result)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
